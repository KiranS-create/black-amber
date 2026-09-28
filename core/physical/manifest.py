"""
SIH26237 - Physical Laboratory Run Manifest & Cryptographic Attestation
Constructs immutable, cryptographically hashed laboratory run manifests binding
environment, hardware inventory, software/algorithm versions, and execution parameters.
"""

import hashlib
import json
import socket
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from core.physical.discovery import HardwareInventory, DeviceStatus


class LaboratoryRunManifest(BaseModel):
    """
    Immutable specification of a physical laboratory validation execution run.
    """
    run_id: str
    operator: str = "AEGISTRACE_LAB_OPERATOR_AIRGAP"
    host_identifier: str = Field(default_factory=socket.gethostname)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hardware_inventory: HardwareInventory
    software_version: str = "1.0.0-pqc-aegistrace"
    watermark_version: str = "DSSS-2D-Spatial-v2.1"
    crypto_version: str = "NIST-FIPS-203-MLKEM768 / NIST-FIPS-204-MLDSA65"
    policy_version: str = "AegisTrace-ForensicDecisionPolicy-v2"
    random_seed: int = 26237
    epistemic_classification: str = "NOT_VERIFIED"  # "PHYSICAL" or "NOT_VERIFIED" (SIMULATION_ONLY)
    manifest_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def compute_manifest_hash(self) -> str:
        """Computes SHA-256 over canonical JSON of manifest excluding manifest_hash."""
        data = self.model_dump(exclude={"manifest_hash"})
        canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Verifies that manifest_hash matches computed hash."""
        if not self.manifest_hash:
            return False
        return self.manifest_hash == self.compute_manifest_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes manifest to dict."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LaboratoryRunManifest":
        """Deserializes manifest from dict."""
        return cls.model_validate(data)

    def finalize(self) -> "LaboratoryRunManifest":
        """Calculates and binds the immutable manifest hash."""
        self.manifest_hash = self.compute_manifest_hash()
        return self


class RunManifestFactory:
    """Factory for instantiating verified laboratory run manifests."""

    @classmethod
    def create_run_manifest(
        cls,
        inventory: HardwareInventory,
        operator: str = "AEGISTRACE_LAB_OPERATOR_AIRGAP",
        random_seed: int = 26237,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> LaboratoryRunManifest:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_id = f"run_phys_lab_{ts}_{random_seed}"

        classification = "GENUINE_HARDWARE_GROUNDED" if inventory.is_physical_lab_ready else "NOT_VERIFIED"

        manifest = LaboratoryRunManifest(
            run_id=run_id,
            operator=operator,
            hardware_inventory=inventory,
            random_seed=random_seed,
            epistemic_classification=classification,
            metadata=custom_metadata or {}
        )
        return manifest.finalize()

    @classmethod
    def create_manifest(
        cls,
        inventory: HardwareInventory,
        operator: str = "AEGISTRACE_LAB_OPERATOR_AIRGAP",
        random_seed: int = 26237,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> LaboratoryRunManifest:
        """Alias for create_run_manifest."""
        return cls.create_run_manifest(
            inventory=inventory,
            operator=operator,
            random_seed=random_seed,
            custom_metadata=custom_metadata
        )

