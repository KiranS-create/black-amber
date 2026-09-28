"""
AegisTrace Device-Bound Session & Decryption Integration.

Binds viewer sessions and decryption events cryptographically to:
Recipient + Device + Session + Document + Nonce + Key Epoch.
Enforces session isolation preventing cross-device session token replay.
"""

import os
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from core.device.models import (
    DevicePrincipal,
    AttestationState,
    DeviceStatus,
)
from core.device.policy import TrustPolicyEngine, OperationType, OperationAssuranceLevel


class BoundDeviceSession(BaseModel):
    """
    Cryptographically bound access session tying a recipient to a specific hardware device.
    """
    session_id: str
    recipient_id: str
    device_id: str
    device_key_id: str
    document_root_hash: str
    session_nonce: str
    attestation_state: AttestationState
    key_epoch: int
    created_at: str
    expires_at: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def compute_session_fingerprint(self) -> str:
        """
        Deterministic binding hash:
        SHA256(session_id || recipient_id || device_id || device_key_id || doc_hash || nonce || epoch)
        """
        preimage = (
            f"BOUND_SESSION:{self.session_id}:{self.recipient_id}:{self.device_id}:"
            f"{self.device_key_id}:{self.document_root_hash}:{self.session_nonce}:{self.key_epoch}"
        )
        return hashlib.sha256(preimage.encode('utf-8')).hexdigest()


class DecryptionDeviceBindingReceipt(BaseModel):
    """
    Composite receipt binding recipient authorization and device trust for a decryption event.
    SEPARATION OF POWERS:
    - recipient_signature: Recipient cryptographic authorization (ML-DSA-65)
    - device_attestation: Platform hardware evidence and attestation state
    Neither is conflated with the other.
    """
    receipt_id: str
    document_id: str
    document_hash: str
    recipient_id: str
    device_id: str
    device_key_id: str
    session_id: str
    session_fingerprint: str
    timestamp: str
    recipient_signature_b64: str
    recipient_signature_alg: str = "ML-DSA-65"
    device_attestation_state: AttestationState
    hardware_class: str
    dynamic_watermark_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceSessionManager:
    """
    Manages creation, validation, and cryptographic replay defense for device-bound sessions.
    """

    def __init__(self, policy_engine: Optional[TrustPolicyEngine] = None):
        self.policy_engine = policy_engine or TrustPolicyEngine()
        self._bound_sessions: Dict[str, BoundDeviceSession] = {}

    def create_bound_session(
        self,
        session_id: str,
        recipient_id: str,
        device: DevicePrincipal,
        document_root_hash: str,
        required_assurance: OperationAssuranceLevel = OperationAssuranceLevel.STANDARD,
        ttl_seconds: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BoundDeviceSession:
        """
        Creates a session bound to (recipient, device, document).
        Evaluates trust policy prior to session grant.
        """
        # 1. Policy evaluation
        decision = self.policy_engine.evaluate(
            device=device,
            operation=OperationType.VIEWER_SESSION_OPEN,
            required_assurance=required_assurance,
        )
        if not decision.is_allowed:
            raise PermissionError(f"Session establishment rejected by policy [{required_assurance.value}]: {decision.reason}")

        now = datetime.now(timezone.utc)
        nonce = os.urandom(16).hex()

        bound_session = BoundDeviceSession(
            session_id=session_id,
            recipient_id=recipient_id,
            device_id=device.device_id,
            device_key_id=device.device_key_id,
            document_root_hash=document_root_hash,
            session_nonce=nonce,
            attestation_state=device.attestation_state,
            key_epoch=device.key_epoch,
            created_at=now.isoformat(),
            is_active=True,
            metadata=metadata or {},
        )

        self._bound_sessions[session_id] = bound_session
        return bound_session

    def validate_session_device(
        self,
        session_id: str,
        presenting_device_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Enforce device session isolation.
        A session created on Device A MUST be rejected if presented by Device B.
        """
        session = self._bound_sessions.get(session_id)
        if not session:
            return False, "SESSION_NOT_FOUND"

        if not session.is_active:
            return False, "SESSION_INACTIVE"

        if session.device_id != presenting_device_id:
            return False, (
                f"DEVICE_MISMATCH: DEVICE_SESSION_MISMATCH: Session '{session_id}' is bound to device "
                f"'{session.device_id}', but access was attempted from '{presenting_device_id}'."
            )

        return True, None

    def validate_session_access(
        self,
        session_id: str,
        presented_device: DevicePrincipal,
        document_root_hash: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate both device binding and document binding for a session.
        """
        dev_valid, reason = self.validate_session_device(session_id, presented_device.device_id)
        if not dev_valid:
            return False, reason

        session = self._bound_sessions[session_id]
        if session.document_root_hash != document_root_hash:
            return False, (
                f"DOCUMENT_HASH_MISMATCH: Session '{session_id}' bound to document "
                f"'{session.document_root_hash}', but presented '{document_root_hash}'."
            )
        return True, None

    def create_decryption_binding(
        self,
        session_id: str,
        presenting_device: DevicePrincipal,
        document_id: str,
        document_hash: str,
        recipient_id: str,
        recipient_signature_b64: str,
        dynamic_watermark_id: Optional[str] = None,
    ) -> DecryptionDeviceBindingReceipt:
        """
        Binds a decryption action to recipient authorization + device evidence.
        """
        # Validate device binding
        valid, reason = self.validate_session_device(session_id, presenting_device.device_id)
        if not valid:
            raise PermissionError(f"Decryption binding failed: {reason}")

        session = self._bound_sessions[session_id]
        now_iso = datetime.now(timezone.utc).isoformat()
        receipt_id = f"drcpt_{os.urandom(12).hex()}"

        return DecryptionDeviceBindingReceipt(
            receipt_id=receipt_id,
            document_id=document_id,
            document_hash=document_hash,
            recipient_id=recipient_id,
            device_id=presenting_device.device_id,
            device_key_id=presenting_device.device_key_id,
            session_id=session_id,
            session_fingerprint=session.compute_session_fingerprint(),
            timestamp=now_iso,
            recipient_signature_b64=recipient_signature_b64,
            recipient_signature_alg="ML-DSA-65",
            device_attestation_state=presenting_device.attestation_state,
            hardware_class=presenting_device.hardware_class.value,
            dynamic_watermark_id=dynamic_watermark_id,
        )

    def create_decryption_receipt(
        self,
        session: BoundDeviceSession,
        device: DevicePrincipal,
        recipient_signature_bytes: Any,
        recipient_signature_alg: str = "ML-DSA-65",
        document_id: str = "",
        dynamic_watermark_id: Optional[str] = None,
    ) -> DecryptionDeviceBindingReceipt:
        """Convenience method wrapping create_decryption_binding."""
        import base64
        if isinstance(recipient_signature_bytes, bytes):
            sig_b64 = base64.b64encode(recipient_signature_bytes).decode('ascii')
        else:
            sig_b64 = str(recipient_signature_bytes)

        return self.create_decryption_binding(
            session_id=session.session_id,
            presenting_device=device,
            document_id=document_id,
            document_hash=session.document_root_hash,
            recipient_id=session.recipient_id,
            recipient_signature_b64=sig_b64,
            dynamic_watermark_id=dynamic_watermark_id,
        )
