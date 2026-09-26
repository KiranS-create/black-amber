from typing import List
from fastapi import APIRouter, Depends, status

from apps.api.models import EnrollRecipientRequest, PublicRecipient
from apps.api.orchestrator import default_orchestrator
from apps.api.security import Actor, require_role, get_current_actor

router = APIRouter(prefix="/recipients", tags=["Recipients"])

@router.post("", response_model=PublicRecipient, status_code=status.HTTP_201_CREATED)
def enroll_recipient(
    req: EnrollRecipientRequest,
    actor: Actor = Depends(require_role(["authority", "system"]))
):
    """
    Enroll a new recipient, generating ML-KEM-768 and ML-DSA-65 post-quantum keypairs.
    Returns only public cryptographic identities (private keys remain protected).
    Requires 'authority' or 'system' role.
    """
    return default_orchestrator.enroll_recipient(name=req.name, recipient_id=req.recipient_id)

@router.get("", response_model=List[PublicRecipient])
def list_recipients(actor: Actor = Depends(get_current_actor)):
    """List all enrolled public recipients and their public keys."""
    return default_orchestrator.list_recipients()

@router.get("/{recipient_id}", response_model=PublicRecipient)
def get_recipient(recipient_id: str, actor: Actor = Depends(get_current_actor)):
    """Get public cryptographic identity for a specific recipient."""
    return default_orchestrator.get_recipient(recipient_id)
