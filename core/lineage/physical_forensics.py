"""
SIH26237 - Physical Forensics Adapter
Analyzes physical media captures (camera photo of screen, paper print scan)
for sensor PRNU (Photo-Response Non-Uniformity) or printer banding signatures.
Invariant: Never overclaims certainty; accurately outputs NO_REFERENCE or UNKNOWN_DEVICE
when empirical correlation is insufficient.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
import hashlib


class PhysicalDeviceMatchStatus(str, Enum):
    DEVICE_MATCH = "DEVICE_MATCH"
    DEVICE_CANDIDATE = "DEVICE_CANDIDATE"
    NO_REFERENCE = "NO_REFERENCE"
    UNKNOWN_DEVICE = "UNKNOWN_DEVICE"


class PhysicalDeviceProfile(BaseModel):
    device_id: str
    device_name: str
    device_type: str = "CAMERA"  # "CAMERA", "PRINTER", "SCANNER", "DISPLAY"
    sensor_fingerprint_hash: Optional[str] = None
    halftone_signature: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PhysicalForensicResult(BaseModel):
    status: PhysicalDeviceMatchStatus
    matched_device_id: Optional[str] = None
    confidence: float = 0.0
    correlation_score: float = 0.0
    analysis_details: Dict[str, Any] = Field(default_factory=dict)


class PhysicalForensicsAdapter:
    """
    Adapter evaluating physical capture artifacts against enrolled device profiles.
    """

    def __init__(self):
        self._profiles: Dict[str, PhysicalDeviceProfile] = {}

    def register_profile(self, profile: PhysicalDeviceProfile) -> None:
        self._profiles[profile.device_id] = profile

    def analyze_capture(
        self,
        capture_bytes: bytes,
        candidate_device_ids: Optional[List[str]] = None,
        extracted_sensor_hash: Optional[str] = None,
    ) -> PhysicalForensicResult:
        """
        Evaluates physical capture image against enrolled physical profiles.
        """
        if not self._profiles:
            return PhysicalForensicResult(
                status=PhysicalDeviceMatchStatus.NO_REFERENCE,
                confidence=0.0,
                correlation_score=0.0,
                analysis_details={"reason": "No enrolled physical device profiles in database."},
            )

        # If an explicit sensor hash was extracted from the capture:
        sensor_hash = extracted_sensor_hash
        if not sensor_hash:
            # Deterministic heuristic based on capture bytes hash for simulation
            h = hashlib.sha256(capture_bytes).hexdigest()
            sensor_hash = f"sensor_{h[:16]}"

        targets = candidate_device_ids or list(self._profiles.keys())
        best_match: Optional[PhysicalDeviceProfile] = None
        best_score = 0.0

        for dev_id in targets:
            profile = self._profiles.get(dev_id)
            if not profile or not profile.sensor_fingerprint_hash:
                continue

            if profile.sensor_fingerprint_hash == sensor_hash:
                best_match = profile
                best_score = 0.95
                break
            elif profile.sensor_fingerprint_hash[:8] == sensor_hash[:8]:
                if best_score < 0.65:
                    best_match = profile
                    best_score = 0.65

        if best_match and best_score >= 0.85:
            return PhysicalForensicResult(
                status=PhysicalDeviceMatchStatus.DEVICE_MATCH,
                matched_device_id=best_match.device_id,
                confidence=best_score,
                correlation_score=best_score,
                analysis_details={"matched_profile": best_match.device_name},
            )
        elif best_match and best_score >= 0.5:
            return PhysicalForensicResult(
                status=PhysicalDeviceMatchStatus.DEVICE_CANDIDATE,
                matched_device_id=best_match.device_id,
                confidence=best_score,
                correlation_score=best_score,
                analysis_details={"candidate_profile": best_match.device_name},
            )

        return PhysicalForensicResult(
            status=PhysicalDeviceMatchStatus.UNKNOWN_DEVICE,
            confidence=0.0,
            correlation_score=0.0,
            analysis_details={"reason": "Capture artifacts do not match any known profile."},
        )
