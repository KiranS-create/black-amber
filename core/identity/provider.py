from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import os
import re

from core.identity.models import Identity, Group, IdentityStatus

class IdentityProvider(ABC):
    """
    Abstract identity provider interface.
    Allows AegisTrace to interface seamlessly with Microsoft Entra ID, Okta,
    Google Workspace, enterprise LDAP, or local directory adapters.
    """
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def get_identity(self, identity_id: str) -> Optional[Identity]:
        """Lookup an identity by opaque identity_id."""
        pass

    @abstractmethod
    def resolve_subject(self, provider_subject: str) -> Optional[Identity]:
        """Lookup an identity by external provider immutable subject."""
        pass

    @abstractmethod
    def search_identities(self, query: str, limit: int = 20) -> List[Identity]:
        """Search identities by name, email, department, or organization."""
        pass

    @abstractmethod
    def validate_identity(self, identity_id: str) -> bool:
        """Verify whether an identity exists and is currently in an ACTIVE state."""
        pass

    @abstractmethod
    def get_groups(self) -> List[Group]:
        """List available directory groups."""
        pass

    @abstractmethod
    def resolve_group_members(self, group_id: str) -> List[Identity]:
        """Resolve all active members belonging to a group."""
        pass


class LocalIdentityProvider(IdentityProvider):
    """
    Production-grade local enterprise identity directory adapter.
    Pre-configured with realistic corporate organization structure, groups,
    external contractors, and guest accounts.
    """
    def __init__(self, provider_name: str = "enterprise_directory"):
        self._provider_name = provider_name
        self._identities: Dict[str, Identity] = {}
        self._subjects: Dict[str, str] = {}  # subject -> identity_id
        self._groups: Dict[str, Group] = {}
        self._seed_directory()

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def _seed_directory(self) -> None:
        """Seed realistic enterprise directory data."""
        # 1. Executive Leadership
        u1 = Identity(
            identity_id="usr_8f7a9c2b01",
            provider=self._provider_name,
            provider_subject="sub_entra_108429401",
            display_name="Sarah Jenkins",
            email="sarah.jenkins@defense-aegis.org",
            organization_id="org_defense_prime",
            department="Executive Leadership",
            title="Chief Information Security Officer",
            status=IdentityStatus.ACTIVE,
            metadata={"clearance": "TOP_SECRET", "employee_id": "EMP-1001"}
        )
        u2 = Identity(
            identity_id="usr_3d4e5f6a02",
            provider=self._provider_name,
            provider_subject="sub_entra_108429402",
            display_name="Marcus Vance",
            email="marcus.vance@defense-aegis.org",
            organization_id="org_defense_prime",
            department="Strategic Operations",
            title="Director of Global Deployments",
            status=IdentityStatus.ACTIVE,
            metadata={"clearance": "TOP_SECRET", "employee_id": "EMP-1002"}
        )

        # 2. Cryptographic Engineering & Security Operations
        u3 = Identity(
            identity_id="usr_9b8c7d6e03",
            provider=self._provider_name,
            provider_subject="sub_entra_108429403",
            display_name="Elena Rostova",
            email="elena.rostova@defense-aegis.org",
            organization_id="org_defense_prime",
            department="Cryptographic Research",
            title="Principal Cryptographic Engineer",
            status=IdentityStatus.ACTIVE,
            metadata={"clearance": "SECRET", "employee_id": "EMP-2041"}
        )
        u4 = Identity(
            identity_id="usr_5a4b3c2d04",
            provider=self._provider_name,
            provider_subject="sub_entra_108429404",
            display_name="David Chen",
            email="david.chen@defense-aegis.org",
            organization_id="org_defense_prime",
            department="Security Operations",
            title="Lead Forensic Investigator",
            status=IdentityStatus.ACTIVE,
            metadata={"clearance": "SECRET", "employee_id": "EMP-2042"}
        )

        # 3. External Legal Counsel & Partner Organization (Cross-Tenant)
        u5 = Identity(
            identity_id="usr_2e3f4a5b05",
            provider="external_counsel_okta",
            provider_subject="okta_ext_5510294",
            display_name="Rachel Sterling",
            email="rachel.sterling@sterling-legal-partners.com",
            organization_id="org_external_legal_partners",
            department="External Legal Counsel",
            title="Senior Partner",
            status=IdentityStatus.ACTIVE,
            metadata={"guest": True, "jurisdiction": "Fed-Circuit"}
        )

        # 4. Contractor / Guest User
        u6 = Identity(
            identity_id="usr_7c8d9e0f06",
            provider="guest_contractor",
            provider_subject="sub_contractor_9901",
            display_name="Liam Thorne",
            email="liam.thorne.guest@external-consulting.net",
            organization_id="org_consulting_group",
            department="Security Audit Team",
            title="External Penetration Tester",
            status=IdentityStatus.ACTIVE,
            metadata={"contract_end": "2027-01-01", "sponsor": "usr_8f7a9c2b01"}
        )

        # 5. Revoked / Deprovisioned Historical Identity
        u7 = Identity(
            identity_id="usr_1a2b3c4d07",
            provider=self._provider_name,
            provider_subject="sub_entra_108429407",
            display_name="Arthur Pendelton",
            email="arthur.pendelton@defense-aegis.org",
            organization_id="org_defense_prime",
            department="Procurement",
            title="Former Logistics Officer",
            status=IdentityStatus.DEPROVISIONED,
            metadata={"deprovisioned_date": "2026-01-15", "reason": "Departure"}
        )

        for user in [u1, u2, u3, u4, u5, u6, u7]:
            self.add_identity(user)

        # Seed Groups
        g1 = Group(
            group_id="grp_executive_leadership",
            display_name="Executive Leadership",
            description="Board members, C-level executives, and strategic division heads",
            organization_id="org_defense_prime",
            member_identity_ids=[u1.identity_id, u2.identity_id]
        )
        g2 = Group(
            group_id="grp_security_operations",
            display_name="Security Operations & Cryptography",
            description="Core engineering and defensive operations personnel",
            organization_id="org_defense_prime",
            member_identity_ids=[u3.identity_id, u4.identity_id]
        )
        g3 = Group(
            group_id="grp_external_audit",
            display_name="External Legal & Compliance Audit",
            description="Cross-tenant external legal counsel and contracted compliance auditors",
            organization_id="org_external_legal_partners",
            member_identity_ids=[u5.identity_id, u6.identity_id]
        )

        for grp in [g1, g2, g3]:
            self._groups[grp.group_id] = grp

    def add_identity(self, identity: Identity) -> None:
        self._identities[identity.identity_id] = identity
        self._subjects[identity.provider_subject] = identity.identity_id

    def get_identity(self, identity_id: str) -> Optional[Identity]:
        return self._identities.get(identity_id)

    def resolve_subject(self, provider_subject: str) -> Optional[Identity]:
        id_id = self._subjects.get(provider_subject)
        if id_id:
            return self._identities.get(id_id)
        return None

    def search_identities(self, query: str, limit: int = 20) -> List[Identity]:
        if not query:
            return list(self._identities.values())[:limit]
        
        q = query.lower().strip()
        matches = []
        for identity in self._identities.values():
            if (
                q in identity.display_name.lower()
                or q in identity.email.lower()
                or q in identity.identity_id.lower()
                or (identity.department and q in identity.department.lower())
                or (identity.organization_id and q in identity.organization_id.lower())
                or (identity.title and q in identity.title.lower())
            ):
                matches.append(identity)
                if len(matches) >= limit:
                    break
        return matches

    def validate_identity(self, identity_id: str) -> bool:
        identity = self._identities.get(identity_id)
        return identity is not None and identity.status == IdentityStatus.ACTIVE

    def get_groups(self) -> List[Group]:
        return list(self._groups.values())

    def resolve_group_members(self, group_id: str) -> List[Identity]:
        grp = self._groups.get(group_id)
        if not grp:
            return []
        members = []
        for mid in grp.member_identity_ids:
            ident = self.get_identity(mid)
            if ident:
                members.append(ident)
        return members


class CachedIdentityProvider(IdentityProvider):
    """
    Offline/Air-Gapped Identity Provider Cache.
    Maintains only identities participating in releases or historical forensic investigations.
    """
    def __init__(self, upstream_provider: Optional[IdentityProvider] = None):
        self.upstream = upstream_provider
        self._cache: Dict[str, Identity] = {}
        self.is_offline = False

    @property
    def provider_name(self) -> str:
        return f"cached_{self.upstream.provider_name if self.upstream else 'local'}"

    def set_offline(self, offline: bool) -> None:
        self.is_offline = offline

    def cache_identity(self, identity: Identity) -> None:
        self._cache[identity.identity_id] = identity

    def get_identity(self, identity_id: str) -> Optional[Identity]:
        if not self.is_offline and self.upstream:
            try:
                res = self.upstream.get_identity(identity_id)
                if res:
                    self.cache_identity(res)
                    return res
            except Exception:
                pass
        return self._cache.get(identity_id)

    def resolve_subject(self, provider_subject: str) -> Optional[Identity]:
        if not self.is_offline and self.upstream:
            try:
                res = self.upstream.resolve_subject(provider_subject)
                if res:
                    self.cache_identity(res)
                    return res
            except Exception:
                pass
        for ident in self._cache.values():
            if ident.provider_subject == provider_subject:
                return ident
        return None

    def search_identities(self, query: str, limit: int = 20) -> List[Identity]:
        if not self.is_offline and self.upstream:
            try:
                results = self.upstream.search_identities(query, limit)
                for r in results:
                    self.cache_identity(r)
                return results
            except Exception:
                pass
        
        q = query.lower().strip()
        matches = []
        for ident in self._cache.values():
            if q in ident.display_name.lower() or q in ident.email.lower() or q in ident.identity_id.lower():
                matches.append(ident)
                if len(matches) >= limit:
                    break
        return matches

    def validate_identity(self, identity_id: str) -> bool:
        ident = self.get_identity(identity_id)
        return ident is not None and ident.status == IdentityStatus.ACTIVE

    def get_groups(self) -> List[Group]:
        if not self.is_offline and self.upstream:
            try:
                return self.upstream.get_groups()
            except Exception:
                pass
        return []

    def resolve_group_members(self, group_id: str) -> List[Identity]:
        if not self.is_offline and self.upstream:
            try:
                members = self.upstream.resolve_group_members(group_id)
                for m in members:
                    self.cache_identity(m)
                return members
            except Exception:
                pass
        return []
