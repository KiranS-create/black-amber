from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status

from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    Actor,
    get_current_actor,
    require_recipient_access,
    require_role,
)
from core.ledger.ledger import EvidenceEvent

router = APIRouter(prefix="/evidence", tags=["Evidence & Audit"])

@router.get("/{release_id}", response_model=List[EvidenceEvent])
def get_release_evidence(
    release_id: str,
    actor: Actor = Depends(require_role(["authority", "auditor", "system"]))
):
    """
    Retrieve all immutable, cryptographically signed decryption provenance events
    recorded in the tamper-evident ledger for a given release.
    """
    return default_orchestrator.get_release_evidence(release_id)

@router.post("/decryption-events", status_code=status.HTTP_201_CREATED)
def submit_decryption_event(
    event: EvidenceEvent,
    actor: Actor = Depends(get_current_actor)
):
    """
    Decentralized Decryption Event Ingestion:
    Submits a client-signed EvidenceEvent. The server cryptographically verifies the
    ML-DSA-65 post-quantum signature against the recipient's enrolled public identity
    before appending the event to the tamper-evident ledger.
    """
    require_recipient_access(event.recipient_id, actor)
    event_hash = default_orchestrator.submit_decryption_event(event)
    return {
        "status": "SUCCESS",
        "event_id": event.event_id,
        "event_hash": event_hash,
        "release_id": event.release_id,
        "recipient_id": event.recipient_id
    }
