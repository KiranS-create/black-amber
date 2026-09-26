from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status

from apps.api.config import config
from apps.api.errors import APIException, ErrorCode
from apps.api.models import CreateReleaseRequest, DecryptRequest, DecryptionResponse
from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    Actor,
    get_current_actor,
    require_recipient_access,
    require_role,
)
from core.ledger.ledger import EvidenceEvent
from core.release import DocumentRelease, ReleaseRecipientPackage

router = APIRouter(prefix="/releases", tags=["Releases"])

@router.post("", response_model=DocumentRelease)
def create_release(
    req: CreateReleaseRequest,
    actor: Actor = Depends(require_role(["authority", "system"]))
):
    """
    Create a quantum-resistant multi-recipient document release.
    Performs ML-KEM-768 key encapsulation and AES-256-GCM authenticated envelope encryption.
    Requires 'authority' or 'system' role.
    """
    return default_orchestrator.create_release(req)

@router.get("", response_model=List[DocumentRelease])
def list_releases(actor: Actor = Depends(require_role(["authority", "auditor", "system"]))):
    """List all created document releases."""
    return default_orchestrator.list_releases()

@router.get("/{release_id}", response_model=DocumentRelease)
def get_release(
    release_id: str,
    actor: Actor = Depends(require_role(["authority", "auditor", "system"]))
):
    """Retrieve full release metadata including encrypted recipient packages."""
    return default_orchestrator.get_release(release_id)

@router.get("/{release_id}/packages/{recipient_id}", response_model=ReleaseRecipientPackage)
def get_recipient_package(
    release_id: str,
    recipient_id: str,
    actor: Actor = Depends(get_current_actor)
):
    """
    Retrieve isolated encrypted package for a specific authorized recipient.
    Enforces IDOR boundary preventing cross-recipient package exfiltration.
    """
    require_recipient_access(recipient_id, actor)
    return default_orchestrator.get_recipient_package(release_id, recipient_id)

@router.post("/{release_id}/decrypt", response_model=DecryptionResponse)
def decrypt_release_package(
    release_id: str,
    req: DecryptRequest,
    actor: Actor = Depends(get_current_actor)
):
    """
    Decrypt recipient package:
    - In decentralized mode: simulated local oracle with caller verification.
    - Requires caller to be the designated recipient or system.
    """
    require_recipient_access(req.recipient_id, actor)
    return default_orchestrator.decrypt_release_package(release_id, req.recipient_id)

@router.post("/{release_id}/provenance", status_code=status.HTTP_201_CREATED)
def submit_release_provenance(
    release_id: str,
    event: EvidenceEvent,
    actor: Actor = Depends(get_current_actor)
):
    """
    Decentralized Provenance Ingestion:
    Accepts a client-side signed EvidenceEvent, cryptographically verifies the ML-DSA-65 signature
    against the recipient's enrolled public key, and appends it to the immutable ledger.
    """
    require_recipient_access(event.recipient_id, actor)
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
