"""
SIH26237 - Device Binding & Hardware Attestation Provider
Defines hardware binding abstractions, enrollment, challenge-response attestation,
and local software fallbacks.
Invariant: Never fakes hardware attestation in local software environments.
"""

import os
import base64
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timezone

from core.crypto.signatures import MLDSA65
from core.lineage.models import (
    DeviceBinding,
    DeviceAttestationStatus,
    PlatformType,
)


class DeviceBindingProvider(ABC):
    """
    Abstract interface for device identity enrollment, attestation,
    and hardware-rooted signing.
    """

    @abstractmethod
    def enroll_device(
        self,
        platform_type: PlatformType = PlatformType.SOFTWARE_LOCAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeviceBinding:
        """Enrolls a device and registers its public key material."""
        pass

    @abstractmethod
    def attest_device(
        self,
        device_id: str,
        challenge: bytes,
    ) -> Tuple[DeviceAttestationStatus, bytes]:
        """
        Validates hardware attestation status against a challenge nonce.
        Returns (status, attestation_evidence).
        """
        pass

    @abstractmethod
    def sign_with_device(self, device_id: str, payload: bytes) -> bytes:
        """Signs receipt payload with device private key."""
        pass


class LocalSoftwareDeviceProvider(DeviceBindingProvider):
    """
    Standard device binding provider for software environments lacking
    hardware security modules (TPM / Apple Secure Enclave / Android StrongBox).
    Honesty Invariant: Strictly reports DEVICE_UNATTESTED and SOFTWARE_LOCAL.
    """

    def __init__(self):
        self._devices: Dict[str, DeviceBinding] = {}
        self._keypairs: Dict[str, Tuple[bytes, bytes]] = {}  # device_id -> (priv, pub)

    def enroll_device(
        self,
        platform_type: PlatformType = PlatformType.SOFTWARE_LOCAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeviceBinding:
        device_id = f"dev_{os.urandom(8).hex()}"
        key_id = f"dkey_{os.urandom(8).hex()}"
        kp = MLDSA65.generate_keypair()
        pub_key, priv_key = kp.public_key_bytes, kp.private_key_bytes

        binding = DeviceBinding(
            device_id=device_id,
            device_key_id=key_id,
            attestation_status=DeviceAttestationStatus.DEVICE_UNATTESTED,
            platform_type=PlatformType.SOFTWARE_LOCAL,
            public_key_b64=base64.b64encode(pub_key).decode('ascii'),
            enrolled_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )
        self._devices[device_id] = binding
        self._keypairs[device_id] = (priv_key, pub_key)
        return binding

    def attest_device(
        self,
        device_id: str,
        challenge: bytes,
    ) -> Tuple[DeviceAttestationStatus, bytes]:
        if device_id not in self._devices:
            raise ValueError(f"Device '{device_id}' is not enrolled.")

        # Software key signs challenge, but status is explicitly UNATTESTED
        priv_key, _ = self._keypairs[device_id]
        sig = MLDSA65.sign(priv_key, challenge)
        return DeviceAttestationStatus.DEVICE_UNATTESTED, sig

    def sign_with_device(self, device_id: str, payload: bytes) -> bytes:
        if device_id not in self._devices:
            raise ValueError(f"Device '{device_id}' is not enrolled.")
        priv_key, _ = self._keypairs[device_id]
        return MLDSA65.sign(priv_key, payload)

    def get_device(self, device_id: str) -> Optional[DeviceBinding]:
        return self._devices.get(device_id)


class SimulatedHardwareEnclaveProvider(DeviceBindingProvider):
    """
    Simulation provider for testing hardware-attested environments (TPM 2.0 / Secure Enclave).
    Emulates cryptographically verified hardware root of trust.
    """

    def __init__(self, platform_type: PlatformType = PlatformType.TPM):
        self.platform_type = platform_type
        self._devices: Dict[str, DeviceBinding] = {}
        self._keypairs: Dict[str, Tuple[bytes, bytes]] = {}

    def enroll_device(
        self,
        platform_type: Optional[PlatformType] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeviceBinding:
        plat = platform_type or self.platform_type
        device_id = f"dev_hw_{os.urandom(8).hex()}"
        key_id = f"dkey_hw_{os.urandom(8).hex()}"
        kp = MLDSA65.generate_keypair()
        pub_key, priv_key = kp.public_key_bytes, kp.private_key_bytes

        binding = DeviceBinding(
            device_id=device_id,
            device_key_id=key_id,
            attestation_status=DeviceAttestationStatus.DEVICE_ATTESTED,
            platform_type=plat,
            public_key_b64=base64.b64encode(pub_key).decode('ascii'),
            enrolled_at=datetime.now(timezone.utc).isoformat(),
            metadata={"enclave_cert": "VALID_ENCLAVE_SIMULATION", **(metadata or {})},
        )
        self._devices[device_id] = binding
        self._keypairs[device_id] = (priv_key, pub_key)
        return binding

    def attest_device(
        self,
        device_id: str,
        challenge: bytes,
    ) -> Tuple[DeviceAttestationStatus, bytes]:
        if device_id not in self._devices:
            raise ValueError(f"Device '{device_id}' is not enrolled.")
        priv_key, _ = self._keypairs[device_id]
        sig = MLDSA65.sign(priv_key, challenge)
        return DeviceAttestationStatus.DEVICE_ATTESTED, sig

    def sign_with_device(self, device_id: str, payload: bytes) -> bytes:
        if device_id not in self._devices:
            raise ValueError(f"Device '{device_id}' is not enrolled.")
        priv_key, _ = self._keypairs[device_id]
        return MLDSA65.sign(priv_key, payload)
