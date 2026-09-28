from typing import Optional, Tuple, Dict
from datetime import datetime, timezone
import logging

from core.identity.models import Identity, RecipientPrincipal, ResolvedIdentitySummary, IdentityStatus, IdentityResolutionResult
from core.identity.provider import IdentityProvider, LocalIdentityProvider, CachedIdentityProvider

logger = logging.getLogger(__name__)

class IdentityResolver:
    """
    Decouples forensic attribution from directory lookup.
    Resolves:
        recipient_id (cryptographic principal)
        -> identity_id (internal identity reference)
        -> Identity (human & enterprise directory metadata)
    
    Guarantees:
    - Directory outage returns status="PENDING" or "CACHED" without invalidating cryptographic attribution.
    - Revoked/deprovisioned identities retain historical forensic auditability.
    - Identities outside the local enterprise (guests, external partners) resolve cleanly.
    """
    def __init__(
        self,
        provider: Optional[IdentityProvider] = None,
        cached_provider: Optional[CachedIdentityProvider] = None
    ):
        self.provider = provider or LocalIdentityProvider()
        self.cached_provider = cached_provider or CachedIdentityProvider(self.provider)
        # In-memory mapping from recipient_id to identity_id
        self._recipient_to_identity: Dict[str, str] = {}
        # In-memory mapping for recipient principals
        self._principals: Dict[str, RecipientPrincipal] = {}
        self._directory_available: bool = True

    def set_directory_availability(self, available: bool) -> None:
        """Simulate or handle external directory network availability."""
        self._directory_available = available
        self.cached_provider.set_offline(not available)

    def register_principal(self, principal: RecipientPrincipal) -> None:
        """Register a cryptographic principal and bind it to an identity_id."""
        self._principals[principal.recipient_id] = principal
        self._recipient_to_identity[principal.recipient_id] = principal.identity_id

    def bind_recipient_identity(self, recipient_id: str, identity_id: str) -> None:
        """Bind an opaque recipient_id to an identity_id."""
        self._recipient_to_identity[recipient_id] = identity_id

    def get_principal(self, recipient_id: str) -> Optional[RecipientPrincipal]:
        return self._principals.get(recipient_id)

    def resolve_recipient(self, recipient_id: str) -> Tuple[Optional[ResolvedIdentitySummary], str]:
        """
        Resolve a recipient_id to human identity metadata.
        Returns:
            (ResolvedIdentitySummary, resolution_status)
        where resolution_status in ["RESOLVED", "CACHED", "PENDING", "NOT_FOUND"]
        """
        identity_id = self._recipient_to_identity.get(recipient_id)
        if not identity_id:
            # Check if principal exists
            principal = self._principals.get(recipient_id)
            if principal:
                identity_id = principal.identity_id
            else:
                return None, "NOT_FOUND"

        # Case 1: Directory is available -> query live directory
        if self._directory_available:
            try:
                identity = self.provider.get_identity(identity_id)
                if identity:
                    # Cache for offline resilience
                    self.cached_provider.cache_identity(identity)
                    summary = ResolvedIdentitySummary(
                        identity_id=identity.identity_id,
                        display_name=identity.display_name,
                        email=identity.email,
                        organization_id=identity.organization_id,
                        provider=identity.provider,
                        status=identity.status.value,
                        department=identity.department,
                        title=identity.title,
                        source="DIRECTORY"
                    )
                    return summary, "RESOLVED"
                else:
                    principal = self._principals.get(recipient_id)
                    if principal:
                        disp_name = getattr(principal, "display_name", None) or getattr(principal, "name", None) or f"Recipient [{recipient_id}]"
                        summary = ResolvedIdentitySummary(
                            identity_id=principal.identity_id,
                            display_name=disp_name,
                            email=getattr(principal, "email", None) or f"{recipient_id}@local.principal",
                            organization_id=getattr(principal, "organization_id", None) or "local",
                            provider=getattr(principal, "identity_provider", getattr(principal, "provider", "local")),
                            status=principal.status.value if hasattr(principal.status, "value") else str(principal.status),
                            source="LOCAL"
                        )
                        return summary, "RESOLVED"
            except Exception as e:
                logger.warning(f"Live directory resolution failed for identity '{identity_id}': {e}")

        # Case 2: Directory unavailable or failed -> attempt local cache
        cached_identity = self.cached_provider.get_identity(identity_id)
        if cached_identity:
            summary = ResolvedIdentitySummary(
                identity_id=cached_identity.identity_id,
                display_name=cached_identity.display_name,
                email=cached_identity.email,
                organization_id=cached_identity.organization_id,
                provider=cached_identity.provider,
                status=cached_identity.status.value,
                department=cached_identity.department,
                title=cached_identity.title,
                source="CACHE"
            )
            return summary, "CACHED"

        # Case 3: Directory unavailable and no cache exists -> fail-soft PENDING
        return None, "PENDING"

    def resolve_recipient_id(self, recipient_id: str, **kwargs) -> IdentityResolutionResult:
        """
        Unified identity resolution method returning IdentityResolutionResult.
        """
        summary, status_code = self.resolve_recipient(recipient_id)
        return IdentityResolutionResult(
            recipient_id=recipient_id,
            status=status_code,
            display_name=summary.display_name if summary else None,
            email=summary.email if summary else None,
            department=summary.department if summary else None,
            title=summary.title if summary else None,
            account_status=summary.status if summary else None,
            confidence=1.0 if status_code == "RESOLVED" else (0.8 if status_code == "CACHED" else 0.0),
            source=summary.source if summary else ("DIRECTORY_404" if status_code == "NOT_FOUND" else "ERROR_TIMEOUT")
        )

# Default global resolver
default_identity_resolver = IdentityResolver()
