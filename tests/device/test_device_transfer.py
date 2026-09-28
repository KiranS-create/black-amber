"""
SIH26237 - Test Device File Transfer Integrity
==============================================
Validates that file transfers preserve exact SHA-256 bitwise equality
and corruption or mismatch is detected immediately.
"""

import pytest
import hashlib
from core.physical.device_transfer import (
    DeviceTransferEngine,
    TransferMechanism,
    TransferDirection,
    DeviceTransferRecord
)
from core.physical.epistemic import EpistemicStatus


def test_device_transfer_hash_integrity():
    """Verify bit-identical file transfer preserves SHA-256 hash."""
    payload = b"CRITICAL_FORENSIC_DISPATCH_BYTES_12345"
    rec = DeviceTransferEngine.execute_transfer(
        payload_bytes=payload,
        filename="dispatch.bin",
        artifact_id="ART-DISPATCH-99",
        direction=TransferDirection.LAPTOP_TO_PHONE,
        source_device="laptop_workstation",
        dest_device="phone_rf8n927pm9n",
        mechanism=TransferMechanism.DEVICE_STAGING
    )

    assert rec.status == "SUCCESS"
    assert rec.is_hash_identical is True
    assert rec.source_hash == rec.destination_hash
    assert rec.source_hash == hashlib.sha256(payload).hexdigest()
    assert rec.source_byte_length == len(payload)
    assert rec.epistemic_status == EpistemicStatus.DEVICE_IN_LOOP


def test_device_transfer_corruption_detection():
    """Verify any 1-bit alteration during transfer results in HASH_MISMATCH."""
    payload = b"UNALTERED_SECRET_CONTENT"
    rec = DeviceTransferEngine.execute_transfer(
        payload_bytes=payload,
        filename="corrupted.bin",
        artifact_id="ART-CORRUPT-01",
        direction=TransferDirection.PHONE_TO_LAPTOP,
        source_device="phone_rf8n927pm9n",
        dest_device="laptop_workstation",
        mechanism=TransferMechanism.DEVICE_STAGING,
        simulate_corruption=True
    )

    assert rec.status == "HASH_MISMATCH"
    assert rec.is_hash_identical is False
    assert rec.source_hash != rec.destination_hash
