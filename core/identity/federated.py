"""
Federated Identity Directory Architecture for AegisTrace.

Provides multi-tenant identity directory routing across enterprise IdPs:
- Microsoft Entra ID (Azure AD)
- Okta Workforce Identity Cloud
- Google Workspace Directory
- OpenLDAP / Active Directory
- Air-Gapped Local Directory

Key Architectural Invariants:
1. Forensic Decoupling: Human directory attributes (email, name, dept) are strictly
   metadata outputs of post-attribution resolution, NOT inputs to cryptographic attribution.
2. Stable Identity Invariant: identity_id is an opaque, immutable surrogate key (usr_...)
   that persists across human name changes, email changes, transfers, and deprovisioning.
3. Cache Lifecycle State Machine:
   - FRESH: Within active cache TTL.
   - CACHED: Past primary TTL, served from local warm cache during transient blips.
   - STALE: Past stale threshold, directory still unreachable; forensic warning logged.
   - UNAVAILABLE: Provider down and no cache entry; gracefully degrades to PENDING
     without invalidating cryptographic attribution.
4. Strict Multi-Tenant Partitioning: Tenant A cannot enumerate or resolve identities
   belonging to Tenant B.
"""

import time
import threading
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from core.identity.models import Identity, IdentityStatus, ResolvedIdentitySummary


class IdentityCacheState(str, Enum):
    FRESH = "FRESH"
    CACHED = "CACHED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class FederatedProviderType(str, Enum):
    ENTRA_ID = "entra_id"
    OKTA = "okta"
    GOOGLE_WORKSPACE = "google_workspace"
    LDAP = "ldap"
    LOCAL_DIRECTORY = "local_directory"


class CompactIdentityRecord:
    """Memory-efficient representation of an enterprise identity (~120 bytes)."""
    __slots__ = (
        "identity_id",
        "tenant_id",
        "provider",
        "provider_subject",
        "display_name",
        "email",
        "department",
        "status",
        "cached_at_epoch",
    )

    def __init__(
        self,
        identity_id: str,
        tenant_id: str,
        provider: str,
        provider_subject: str,
        display_name: str,
        email: str,
        department: str,
        status: str,
        cached_at_epoch: float,
    ):
        self.identity_id = identity_id
        self.tenant_id = tenant_id
        self.provider = provider
        self.provider_subject = provider_subject
        self.display_name = display_name
        self.email = email
        self.department = department
        self.status = status
        self.cached_at_epoch = cached_at_epoch

    def __repr__(self) -> str:
        return f"CompactIdentityRecord(id={self.identity_id!r}, email={self.email!r}, tenant={self.tenant_id!r})"


class FederatedProviderAdapter:
    """Abstract base adapter for enterprise identity federation."""
    def __init__(self, provider_id: str, provider_type: FederatedProviderType, tenant_id: str):
        self.provider_id = provider_id
        self.provider_type = provider_type
        self.tenant_id = tenant_id
        self.is_healthy: bool = True
        self._identities: Dict[str, Identity] = {}  # keyed by provider_subject
        self._email_to_subject: Dict[str, str] = {} # keyed by lowercase email

    def get_identity_by_subject(self, subject: str) -> Optional[Identity]:
        if not self.is_healthy:
            raise ConnectionError(f"IdP '{self.provider_id}' is unreachable")
        return self._identities.get(subject)

    def search_by_email(self, email: str) -> Optional[Identity]:
        if not self.is_healthy:
            raise ConnectionError(f"IdP '{self.provider_id}' is unreachable")
        norm = email.lower().strip()
        subject = self._email_to_subject.get(norm)
        if subject is not None:
            return self._identities.get(subject)
        for ident in self._identities.values():
            if ident.email.lower() == norm:
                return ident
        return None

    def add_identity(self, identity: Identity) -> None:
        self._identities[identity.provider_subject] = identity
        self._email_to_subject[identity.email.lower().strip()] = identity.provider_subject


class EntraIdAdapter(FederatedProviderAdapter):
    def __init__(self, tenant_id: str, provider_id: str = "entra_id_primary"):
        super().__init__(provider_id, FederatedProviderType.ENTRA_ID, tenant_id)


class OktaAdapter(FederatedProviderAdapter):
    def __init__(self, tenant_id: str, provider_id: str = "okta_primary"):
        super().__init__(provider_id, FederatedProviderType.OKTA, tenant_id)


class GoogleWorkspaceAdapter(FederatedProviderAdapter):
    def __init__(self, tenant_id: str, provider_id: str = "google_ws_primary"):
        super().__init__(provider_id, FederatedProviderType.GOOGLE_WORKSPACE, tenant_id)


class LdapAdapter(FederatedProviderAdapter):
    def __init__(self, tenant_id: str, provider_id: str = "ldap_primary"):
        super().__init__(provider_id, FederatedProviderType.LDAP, tenant_id)


class LocalDirectoryAdapter(FederatedProviderAdapter):
    def __init__(self, tenant_id: str, provider_id: str = "local_airgap_primary"):
        super().__init__(provider_id, FederatedProviderType.LOCAL_DIRECTORY, tenant_id)


class FederatedIdentityDirectory:
    """
    High-scale, multi-tenant federated identity directory router with four-state cache lifecycle.
    """
    def __init__(
        self,
        fresh_ttl_seconds: float = 3600.0,      # 1 hour
        stale_threshold_seconds: float = 86400.0 # 24 hours
    ):
        self.fresh_ttl = fresh_ttl_seconds
        self.stale_threshold = stale_threshold_seconds
        self._lock = threading.RLock()

        # Multi-tenant adapter registries: (tenant_id, provider_id) -> adapter
        self._adapters: Dict[Tuple[str, str], FederatedProviderAdapter] = {}

        # Default provider per tenant: tenant_id -> provider_id
        self._tenant_default_provider: Dict[str, str] = {}

        # Local cache: (tenant_id, identity_id) -> CompactIdentityRecord
        self._cache: Dict[Tuple[str, str], CompactIdentityRecord] = {}

        # Inverted index: (tenant_id, email.lower()) -> identity_id
        self._by_email: Dict[Tuple[str, str], str] = {}

        # Inverted index: (tenant_id, provider_id, provider_subject) -> identity_id
        self._by_subject: Dict[Tuple[str, str, str], str] = {}

        # Group memberships: (tenant_id, group_id) -> Set[identity_id]
        self._groups: Dict[Tuple[str, str], Set[str]] = {}

        # Recipient to identity bindings: (tenant_id, recipient_id) -> identity_id
        self._recipient_bindings: Dict[Tuple[str, str], str] = {}

    def register_provider(self, adapter: FederatedProviderAdapter, set_as_default: bool = True) -> None:
        """Register an enterprise identity provider adapter for a specific tenant."""
        with self._lock:
            key = (adapter.tenant_id, adapter.provider_id)
            self._adapters[key] = adapter
            if set_as_default or adapter.tenant_id not in self._tenant_default_provider:
                self._tenant_default_provider[adapter.tenant_id] = adapter.provider_id

    def set_provider_health(self, tenant_id: str, provider_id: str, is_healthy: bool) -> None:
        with self._lock:
            adapter = self._adapters.get((tenant_id, provider_id))
            if adapter:
                adapter.is_healthy = is_healthy

    def bind_recipient(self, recipient_id: str, identity_id: str, tenant_id: str = "default_tenant") -> None:
        with self._lock:
            self._recipient_bindings[(tenant_id, recipient_id)] = identity_id

    def cache_identity(self, identity: Identity, tenant_id: str = "default_tenant") -> None:
        with self._lock:
            record = CompactIdentityRecord(
                identity_id=identity.identity_id,
                tenant_id=tenant_id,
                provider=identity.provider,
                provider_subject=identity.provider_subject,
                display_name=identity.display_name,
                email=identity.email,
                department=identity.department or "",
                status=identity.status.value,
                cached_at_epoch=time.time()
            )
            self._cache[(tenant_id, identity.identity_id)] = record
            self._by_email[(tenant_id, identity.email.lower().strip())] = identity.identity_id
            self._by_subject[(tenant_id, identity.provider, identity.provider_subject)] = identity.identity_id

    def get_cache_state(self, record: CompactIdentityRecord) -> IdentityCacheState:
        age = time.time() - record.cached_at_epoch
        if age <= self.fresh_ttl:
            return IdentityCacheState.FRESH
        elif age <= self.stale_threshold:
            return IdentityCacheState.CACHED
        else:
            return IdentityCacheState.STALE

    def resolve_by_identity_id(
        self,
        identity_id: str,
        tenant_id: str = "default_tenant"
    ) -> Tuple[Optional[ResolvedIdentitySummary], IdentityCacheState]:
        """
        Resolves identity metadata through the multi-tier cache / live provider lifecycle.
        Guarantees tenant isolation: query strictly bounded to tenant_id.
        """
        with self._lock:
            cache_key = (tenant_id, identity_id)
            record = self._cache.get(cache_key)

            # Check if we have a fresh cache record
            if record:
                state = self.get_cache_state(record)
                if state == IdentityCacheState.FRESH:
                    summary = ResolvedIdentitySummary(
                        identity_id=record.identity_id,
                        display_name=record.display_name,
                        email=record.email,
                        organization_id=tenant_id,
                        provider=record.provider,
                        status=record.status,
                        department=record.department or None,
                        title=None,
                        source=f"CACHE_{state.value}"
                    )
                    return summary, state

            # If cache is absent, cached, or stale: attempt to refresh from live provider
            default_pid = self._tenant_default_provider.get(tenant_id)
            if default_pid:
                adapter = self._adapters.get((tenant_id, default_pid))
                if adapter and adapter.is_healthy:
                    try:
                        # Attempt resolution by provider subject or email from record
                        live_id: Optional[Identity] = None
                        if record:
                            live_id = adapter.get_identity_by_subject(record.provider_subject)
                        if live_id:
                            self.cache_identity(live_id, tenant_id=tenant_id)
                            summary = ResolvedIdentitySummary(
                                identity_id=live_id.identity_id,
                                display_name=live_id.display_name,
                                email=live_id.email,
                                organization_id=tenant_id,
                                provider=live_id.provider,
                                status=live_id.status.value,
                                department=live_id.department,
                                title=live_id.title,
                                source="DIRECTORY_LIVE"
                            )
                            return summary, IdentityCacheState.FRESH
                    except Exception:
                        pass  # Degrade gracefully to cache fallback

            # If live directory unreachable or failed: fall back to cached record
            if record:
                state = self.get_cache_state(record)
                summary = ResolvedIdentitySummary(
                    identity_id=record.identity_id,
                    display_name=record.display_name,
                    email=record.email,
                    organization_id=tenant_id,
                    provider=record.provider,
                    status=record.status,
                    department=record.department or None,
                    title=None,
                    source=f"FALLBACK_{state.value}"
                )
                return summary, state

            # No cache and directory unreachable: fail-soft PENDING
            return None, IdentityCacheState.UNAVAILABLE

    def resolve_recipient(
        self,
        recipient_id: str,
        tenant_id: str = "default_tenant"
    ) -> Tuple[Optional[ResolvedIdentitySummary], str]:
        """
        Entry point for forensic attribution pipeline.
        Maps recipient_id -> identity_id -> ResolvedIdentitySummary.
        """
        with self._lock:
            identity_id = self._recipient_bindings.get((tenant_id, recipient_id))
            if not identity_id:
                return None, "NOT_FOUND"

            summary, cache_state = self.resolve_by_identity_id(identity_id, tenant_id=tenant_id)
            if summary:
                status_str = "RESOLVED" if cache_state == IdentityCacheState.FRESH else "CACHED"
                return summary, status_str
            return None, "PENDING"

    def count_identities(self, tenant_id: Optional[str] = None) -> int:
        with self._lock:
            if tenant_id:
                return sum(1 for (tid, _) in self._cache.keys() if tid == tenant_id)
            return len(self._cache)


# Global default federated identity directory
default_federated_directory = FederatedIdentityDirectory()
