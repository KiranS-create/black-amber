from enum import Enum
from typing import List, Set, Optional, Dict
from pydantic import BaseModel, Field

from core.identity.models import Identity, IdentityStatus
from core.identity.provider import IdentityProvider, LocalIdentityProvider

class ReleaseTargetType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    GROUP = "GROUP"
    DIRECTORY_QUERY = "DIRECTORY_QUERY"

class ReleaseTargetSpec(BaseModel):
    target_type: ReleaseTargetType = ReleaseTargetType.INDIVIDUAL
    target_ids: List[str] = Field(..., description="List of identity_ids or group_ids")
    organization_id: Optional[str] = None

class ReleaseTargetingService:
    """
    Resolves high-level enterprise release targets (individuals, groups, departments)
    into individual distinct identities for cryptographic packaging.
    
    Guarantees:
    - Groups are expanded into individual identities.
    - No shared cryptographic keys exist for an entire group.
    - Inactive (REVOKED / DEPROVISIONED / SUSPENDED) identities are rejected from new releases.
    - Duplicate identity resolutions are cleanly deduplicated.
    """
    def __init__(self, provider: Optional[IdentityProvider] = None):
        self.provider = provider or LocalIdentityProvider()

    def resolve_targets(self, target_spec: ReleaseTargetSpec) -> List[Identity]:
        resolved: Dict[str, Identity] = {}

        if target_spec.target_type == ReleaseTargetType.INDIVIDUAL:
            for i_id in target_spec.target_ids:
                ident = self.provider.get_identity(i_id)
                if not ident:
                    raise ValueError(f"Identity '{i_id}' not found in directory.")
                if ident.status != IdentityStatus.ACTIVE:
                    raise ValueError(f"Cannot release to inactive identity '{i_id}' (status: {ident.status}).")
                resolved[ident.identity_id] = ident

        elif target_spec.target_type == ReleaseTargetType.GROUP:
            for g_id in target_spec.target_ids:
                members = self.provider.resolve_group_members(g_id)
                if not members:
                    raise ValueError(f"Group '{g_id}' has no members or does not exist.")
                for m in members:
                    if m.status == IdentityStatus.ACTIVE:
                        resolved[m.identity_id] = m

        elif target_spec.target_type == ReleaseTargetType.DIRECTORY_QUERY:
            for query in target_spec.target_ids:
                matches = self.provider.search_identities(query)
                for m in matches:
                    if m.status == IdentityStatus.ACTIVE:
                        resolved[m.identity_id] = m

        if not resolved:
            raise ValueError("Release targeting resolved to zero active recipients.")

        return list(resolved.values())
