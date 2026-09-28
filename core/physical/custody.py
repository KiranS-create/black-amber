"""
SIH26237 - Raw Evidence Preservation & Physical Chain of Custody
Tracks the complete evidentiary lifecycle of physical validation artifacts:
COLLECTED -> PRINTED -> CAPTURED -> IMPORTED -> HASHED -> ANALYZED -> SEALED.
Preserves raw optical captures, intermediate processed images, and forensic outputs in:
artifacts/physical_validation/runs/<RUN_ID>/
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CustodyTransitionEvent(BaseModel):
    """Single transition event in the physical evidence chain of custody."""
    event_id: str
    action: str  # "COLLECTED", "PRINTED", "CAPTURED", "IMPORTED", "HASHED", "ANALYZED", "SEALED"
    artifact_hash: str
    artifact_path: str
    operator: str
    device_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PhysicalChainOfCustodyLedger(BaseModel):
    """Complete chain of custody log for a laboratory validation run."""
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sealed_at: Optional[str] = None
    is_sealed: bool = False
    events: List[CustodyTransitionEvent] = Field(default_factory=list)
    root_custody_hash: Optional[str] = None

    def compute_root_hash(self) -> str:
        """Computes incremental SHA-256 hash over chronological custody events."""
        h = hashlib.sha256(self.run_id.encode())
        for ev in self.events:
            ev_str = f"{ev.event_id}:{ev.action}:{ev.artifact_hash}:{ev.timestamp}"
            h.update(ev_str.encode())
        return h.hexdigest()

    def seal(self) -> "PhysicalChainOfCustodyLedger":
        self.is_sealed = True
        self.sealed_at = datetime.now(timezone.utc).isoformat()
        self.root_custody_hash = self.compute_root_hash()
        return self


class PhysicalChainOfCustodyTracker:
    """
    Manages run directory structure and preserves raw/processed physical evidence.
    """

    def __init__(
        self,
        run_id: str,
        base_dir: Optional[str] = None,
        operator: str = "AEGISTRACE_LAB_OPERATOR_AIRGAP"
    ):
        self.run_id = run_id
        self.operator = operator
        root_path = Path(base_dir or "artifacts/physical_validation/runs")
        self.run_dir = root_path / run_id
        self.raw_dir = self.run_dir / "raw"
        self.processed_dir = self.run_dir / "processed"
        self.results_dir = self.run_dir / "results"

        self._ensure_directories()
        self.ledger = PhysicalChainOfCustodyLedger(run_id=run_id)

    def _ensure_directories(self) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def record_transition(
        self,
        action: str,
        artifact_bytes: bytes,
        filename: str,
        device_id: str = "UNKNOWN_OR_VIRTUAL",
        folder: str = "raw",
        notes: str = ""
    ) -> CustodyTransitionEvent:
        """Saves artifact bytes into specified subfolder and logs custody transition."""
        sha256_hash = hashlib.sha256(artifact_bytes).hexdigest()

        target_folder = self.raw_dir if folder == "raw" else (
            self.processed_dir if folder == "processed" else self.results_dir
        )
        file_path = target_folder / filename
        with open(file_path, "wb") as f:
            f.write(artifact_bytes)

        event = CustodyTransitionEvent(
            event_id=f"cust_{len(self.ledger.events) + 1:04d}",
            action=action,
            artifact_hash=sha256_hash,
            artifact_path=str(file_path.relative_to(self.run_dir.parent.parent.parent)),
            operator=self.operator,
            device_id=device_id,
            notes=notes,
            metadata={"byte_length": len(artifact_bytes)}
        )
        self.ledger.events.append(event)
        return event

    def save_artifact(self, filename: str, artifact_bytes: bytes, folder: str = "raw") -> str:
        """Saves artifact to folder and returns sha256 hex digest."""
        sha256_hash = hashlib.sha256(artifact_bytes).hexdigest()
        target_folder = self.raw_dir if folder == "raw" else (
            self.processed_dir if folder == "processed" else self.results_dir
        )
        file_path = target_folder / filename
        with open(file_path, "wb") as f:
            f.write(artifact_bytes)
        return sha256_hash

    def log_custody_event(
        self,
        action: str,
        device_id: str,
        artifact_hash: str,
        operator: str = "",
        notes: str = "",
        artifact_path: str = ""
    ) -> CustodyTransitionEvent:
        """Logs a custody event without rewriting the artifact file."""
        event = CustodyTransitionEvent(
            event_id=f"cust_{len(self.ledger.events) + 1:04d}",
            action=action,
            artifact_hash=artifact_hash,
            artifact_path=artifact_path or f"runs/{self.run_id}/raw/{artifact_hash[:12]}",
            operator=operator or self.operator,
            device_id=device_id,
            notes=notes,
            metadata={}
        )
        self.ledger.events.append(event)
        return event

    def export_custody_report(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary of the custody ledger."""
        return self.ledger.model_dump(mode="json")

    def save_and_seal_ledger(self) -> str:
        """Seals the custody ledger and writes chain_of_custody.json."""
        self.ledger.seal()
        out_file = self.run_dir / "chain_of_custody.json"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(self.ledger.model_dump_json(indent=2))
        return str(out_file)

