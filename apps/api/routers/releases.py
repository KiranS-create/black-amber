from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status

from apps.api.config import config
from apps.api.errors import APIException, ErrorCode
from apps.api.models import CreateReleaseRequest, DecryptRequest, DecryptionResponse
from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    SecurityPrincipal,
    get_current_actor,
    require_recipient_access,
    require_role,
    validate_id_format,
    verify_tenant_boundary,
)
from core.ledger.ledger import EvidenceEvent
from core.release import DocumentRelease, ReleaseRecipientPackage

router = APIRouter(prefix="/releases", tags=["Releases"])

@router.post("", response_model=DocumentRelease)
def create_release(
    req: CreateReleaseRequest,
    actor: SecurityPrincipal = Depends(require_role(["operator", "administrator", "authority", "system"]))
):
    """
    Create a quantum-resistant multi-recipient document release.
    Performs ML-KEM-768 key encapsulation and AES-256-GCM authenticated envelope encryption.
    Scoped to the authenticated principal's tenant.
    """
    if req.document_id:
        validate_id_format(req.document_id, "document_id")
    if req.recipient_ids:
        for r in req.recipient_ids:
            validate_id_format(r, "recipient_id")

    # Set tenant boundary
    target_tenant = req.tenant_id or actor.tenant_id
    verify_tenant_boundary(target_tenant, actor, "tenant", target_tenant)
    req.tenant_id = target_tenant

    release = default_orchestrator.create_release(req)
    return release

@router.get("", response_model=List[DocumentRelease])
def list_releases(
    actor: SecurityPrincipal = Depends(require_role(["operator", "administrator", "investigator", "viewer", "authority", "auditor", "system"]))
):
    """List all created document releases scoped to tenant."""
    all_releases = default_orchestrator.list_releases()
    if actor.role == "system":
        return all_releases
    return [r for r in all_releases if getattr(r, "tenant_id", "default_tenant") == actor.tenant_id]

@router.get("/{release_id}", response_model=DocumentRelease)
def get_release(
    release_id: str,
    actor: SecurityPrincipal = Depends(require_role(["operator", "administrator", "investigator", "viewer", "authority", "auditor", "system"]))
):
    """Retrieve full release metadata including encrypted recipient packages."""
    validate_id_format(release_id, "release_id")
    rel = default_orchestrator.get_release(release_id)
    verify_tenant_boundary(getattr(rel, "tenant_id", "default_tenant"), actor, "release", release_id)
    return rel

@router.get("/{release_id}/packages/{recipient_id}", response_model=ReleaseRecipientPackage)
def get_recipient_package(
    release_id: str,
    recipient_id: str,
    actor: SecurityPrincipal = Depends(get_current_actor)
):
    """
    Retrieve isolated encrypted package for a specific authorized recipient.
    Enforces IDOR boundary preventing cross-recipient package exfiltration and cross-tenant access.
    """
    validate_id_format(release_id, "release_id")
    validate_id_format(recipient_id, "recipient_id")
    require_recipient_access(recipient_id, actor)

    rel = default_orchestrator.get_release(release_id)
    verify_tenant_boundary(getattr(rel, "tenant_id", "default_tenant"), actor, "release", release_id)

    return default_orchestrator.get_recipient_package(release_id, recipient_id)

@router.post("/{release_id}/decrypt", response_model=DecryptionResponse)
def decrypt_release_package(
    release_id: str,
    req: DecryptRequest,
    actor: SecurityPrincipal = Depends(get_current_actor)
):
    """
    Decrypt recipient package:
    - In decentralized mode: simulated local oracle with caller verification.
    - Requires caller to be the designated recipient or system.
    - Enforces IDOR, state-machine (revocation), and tenant boundaries.
    """
    validate_id_format(release_id, "release_id")
    validate_id_format(req.recipient_id, "recipient_id")
    require_recipient_access(req.recipient_id, actor)

    rel = default_orchestrator.get_release(release_id)
    verify_tenant_boundary(getattr(rel, "tenant_id", "default_tenant"), actor, "release", release_id)

    return default_orchestrator.decrypt_release_package(release_id, req.recipient_id)

@router.post("/{release_id}/provenance", status_code=status.HTTP_201_CREATED)
def submit_release_provenance(
    release_id: str,
    event: EvidenceEvent,
    actor: SecurityPrincipal = Depends(get_current_actor)
):
    """
    Decentralized Provenance Ingestion:
    Accepts a client-side signed EvidenceEvent, cryptographically verifies the ML-DSA-65 signature
    against the recipient's enrolled public key, and appends it to the immutable ledger.
    Enforces anti-replay and tenant boundaries.
    """
    validate_id_format(release_id, "release_id")
    validate_id_format(event.recipient_id, "recipient_id")
    validate_id_format(event.event_id, "event_id")
    require_recipient_access(event.recipient_id, actor)

    rel = default_orchestrator.get_release(release_id)
    verify_tenant_boundary(getattr(rel, "tenant_id", "default_tenant"), actor, "release", release_id)

    if event.release_id != release_id:
        raise APIException(
            code=ErrorCode.INVALID_RELEASE,
            message=f"Release ID mismatch: path has '{release_id}', event has '{event.release_id}'."
        )
    event_hash = default_orchestrator.submit_decryption_event(event)
    return {
        "status": "SUCCESS",
        "event_id": event.event_id,
        "event_hash": event_hash,
        "release_id": release_id,
        "recipient_id": event.recipient_id
    }
