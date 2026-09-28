"""
AegisTrace Device Attestation Providers.
"""

from core.device.providers.base import verify_device_signature
from core.device.providers.tpm import TPMAttestationProvider
from core.device.providers.apple import AppleSecureEnclaveProvider
from core.device.providers.android import AndroidStrongBoxProvider
from core.device.providers.webauthn import WebAuthnDeviceProvider
from core.device.providers.software import LocalSoftwareDeviceProvider

__all__ = [
    "verify_device_signature",
    "TPMAttestationProvider",
    "AppleSecureEnclaveProvider",
    "AndroidStrongBoxProvider",
    "WebAuthnDeviceProvider",
    "LocalSoftwareDeviceProvider",
]
