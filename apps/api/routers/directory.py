from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from apps.api.models import (
    IdentityResponse,
    DirectorySearchResponse,
    GroupResponse,
    GroupListResponse,
)
from apps.api.orchestrator import default_orchestrator
from apps.api.security import Actor, require_role, get_current_actor, validate_id_format
from apps.api.errors import APIException, ErrorCode
from core.identity.models import IdentityStatus

router = APIRouter(prefix="/directory", tags=["Identity Directory"])

@router.get("/search", response_model=DirectorySearchResponse)
def search_directory(
    query: str = Query("", max_length=200, description="Search by name, email, department, organization, or title"),
    limit: int = Query(20, ge=1, le=100),
    actor: Actor = Depends(get_current_actor)
):
    """
    Search the enterprise identity directory.
    Queries external identity providers (Entra, Okta, LDAP) or local cached directory.
    Returns opaque identity_id and enterprise directory metadata.
    """
    identities = default_orchestrator.search_directory(query=query, limit=limit)
    res = [
        IdentityResponse(
            identity_id=i.identity_id,
            provider=i.provider,
            provider_subject=i.provider_subject,
            display_name=i.display_name,
            email=i.email,
            organization_id=i.organization_id,
            department=i.department,
            title=i.title,
            status=i.status.value,
            created_at=i.created_at
        )
        for i in identities
    ]
    return DirectorySearchResponse(identities=res, total=len(res))

@router.get("/identities/{identity_id}", response_model=IdentityResponse)
def get_identity(
    identity_id: str,
    actor: Actor = Depends(get_current_actor)
):
    """Retrieve full directory details for an identity_id."""
    validate_id_format(identity_id, "identity_id")
    ident = default_orchestrator.get_identity(identity_id)
    if not ident:
        raise APIException(
            code=ErrorCode.IDENTITY_NOT_FOUND if hasattr(ErrorCode, "IDENTITY_NOT_FOUND") else ErrorCode.RECIPIENT_NOT_FOUND,
            message=f"Identity '{identity_id}' not found in directory.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return IdentityResponse(
        identity_id=ident.identity_id,
        provider=ident.provider,
        provider_subject=ident.provider_subject,
        display_name=ident.display_name,
        email=ident.email,
        organization_id=ident.organization_id,
        department=ident.department,
        title=ident.title,
        status=ident.status.value,
        created_at=ident.created_at
    )

@router.get("/groups", response_model=GroupListResponse)
def list_groups(
    actor: Actor = Depends(get_current_actor)
):
    """List all available directory groups and teams."""
    groups = default_orchestrator.list_groups()
    res = [
        GroupResponse(
            group_id=g.group_id,
            display_name=g.display_name,
            description=g.description,
            organization_id=g.organization_id,
            member_count=len(g.member_identity_ids),
            member_identity_ids=g.member_identity_ids
        )
        for g in groups
    ]
    return GroupListResponse(groups=res, total=len(res))

@router.get("/groups/{group_id}/members", response_model=List[IdentityResponse])
def get_group_members(
    group_id: str,
    actor: Actor = Depends(get_current_actor)
):
    """Resolve all active members belonging to a directory group."""
    members = default_orchestrator.resolve_group_members(group_id)
    return [
        IdentityResponse(
            identity_id=i.identity_id,
            provider=i.provider,
            provider_subject=i.provider_subject,
            display_name=i.display_name,
            email=i.email,
            organization_id=i.organization_id,
            department=i.department,
            title=i.title,
            status=i.status.value,
            created_at=i.created_at
        )
        for i in members
    ]
