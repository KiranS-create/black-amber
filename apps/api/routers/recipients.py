from typing import List, Optional
from fastapi import APIRouter, Depends, status

from apps.api.models import EnrollRecipientRequest, PublicRecipient
from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    SecurityPrincipal,
    require_role,
    get_current_actor,
    validate_id_format,
)

router = APIRouter(prefix="/recipients", tags=["Recipients"])

@router.post("", response_model=PublicRecipient, status_code=status.HTTP_201_CREATED)
def enroll_recipient(
    req: EnrollRecipientRequest,
    actor: SecurityPrincipal = Depends(require_role(["administrator", "authority", "system"]))
):
    """
    Enroll a new recipient, generating ML-KEM-768 and ML-DSA-65 post-quantum keypairs.
    Supports enrolling an enterprise identity_id from the directory, or a custom name.
    Returns only public cryptographic identities (private keys remain protected).
    Requires 'administrator', 'authority', or 'system' role.
    """
    if req.recipient_id:
        validate_id_format(req.recipient_id, "recipient_id")
    if req.identity_id:
        validate_id_format(req.identity_id, "identity_id")

    return default_orchestrator.enroll_recipient(
        name=req.name,
        recipient_id=req.recipient_id,
        identity_id=req.identity_id
    )

@router.get("", response_model=List[PublicRecipient])
def list_recipients(actor: SecurityPrincipal = Depends(get_current_actor)):
    """List all enrolled public recipients and their public keys."""
    return default_orchestrator.list_recipients()

@router.get("/{recipient_id}", response_model=PublicRecipient)
def get_recipient(recipient_id: str, actor: SecurityPrincipal = Depends(get_current_actor)):
    """Get public cryptographic identity for a specific recipient."""
    validate_id_format(recipient_id, "recipient_id")
    return default_orchestrator.get_recipient(recipient_id)

@router.post("/{recipient_id}/revoke", response_model=PublicRecipient)
def revoke_recipient(
    recipient_id: str,
    actor: SecurityPrincipal = Depends(require_role(["administrator", "authority", "system"]))
):
    """
    Revoke a recipient principal.
    Prevents future releases while strictly preserving historical forensic attribution.
    Requires 'administrator', 'authority', or 'system' role.
    """
    validate_id_format(recipient_id, "recipient_id")
    return default_orchestrator.revoke_recipient(recipient_id)
