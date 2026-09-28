"""
AegisTrace Evidence Package Exporter & Archive Parser.

Serializes and deserializes complete evidence packages to and from directory trees
or compressed ZIP archives for offline transport and independent verification.
Guarantees:
1. Canonical JSON formatting for all serialized files.
2. Type-safe re-hydration of all 17 evidence object categories.
3. Zero dependency on live databases or network storage.
"""

import json
import os
import zipfile
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from core.evidence_package.models import (
    BaseEvidenceObject,
    EvidenceObjectType,
    PackageManifest,
    PackageSignature,
    CaseObject,
    ArtifactEvidenceObject,
    WatermarkEvidenceObject,
    DecryptionReceiptObject,
    RecipientIdentityProofObject,
    DeviceEvidenceObject,
    SessionEvidenceObject,
    LineageEvidenceObject,
    LedgerProofObject,
    TelemetryEvidenceObject,
    ChainOfCustodyEvent,
    AttributionDecisionObject,
    DependencyEdge
)
from core.evidence_package.builder import EvidencePackage
from core.evidence_package.canonical import canonical_json_dumps, canonical_json_bytes
from core.evidence_package.redaction import RedactedEvidenceStub


OBJECT_TYPE_MAP = {
    EvidenceObjectType.CASE.value: CaseObject,
    EvidenceObjectType.ARTIFACT.value: ArtifactEvidenceObject,
    EvidenceObjectType.WATERMARK_EVIDENCE.value: WatermarkEvidenceObject,
    EvidenceObjectType.DECRYPTION_RECEIPT.value: DecryptionReceiptObject,
    EvidenceObjectType.RECIPIENT_IDENTITY_PROOF.value: RecipientIdentityProofObject,
    EvidenceObjectType.DEVICE_EVIDENCE.value: DeviceEvidenceObject,
    EvidenceObjectType.SESSION_EVIDENCE.value: SessionEvidenceObject,
    EvidenceObjectType.LINEAGE_EVIDENCE.value: LineageEvidenceObject,
    EvidenceObjectType.LEDGER_PROOF.value: LedgerProofObject,
    EvidenceObjectType.TELEMETRY_EVIDENCE.value: TelemetryEvidenceObject,
    EvidenceObjectType.CHAIN_OF_CUSTODY_EVENT.value: ChainOfCustodyEvent,
    EvidenceObjectType.ATTRIBUTION_DECISION.value: AttributionDecisionObject,
    EvidenceObjectType.DEPENDENCY_EDGE.value: DependencyEdge,
}


def deserialize_evidence_object(data: Dict[str, Any]) -> BaseEvidenceObject:
    """Deserializes raw JSON dictionary into strongly typed BaseEvidenceObject subclass."""
    if data.get("object_id", "").startswith("redacted_") or "original_object_id" in data:
        return RedactedEvidenceStub(**data)

    obj_type_str = data.get("object_type", "")
    cls = OBJECT_TYPE_MAP.get(obj_type_str, BaseEvidenceObject)
    return cls(**data)


class EvidencePackageExporter:
    """
    Exports EvidencePackage to directory or ZIP archive.
    """
    @classmethod
    def export_to_directory(cls, package: EvidencePackage, target_dir: Union[str, Path]) -> str:
        """Exports package to target directory structure."""
        out_path = Path(target_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        objects_dir = out_path / "objects"
        objects_dir.mkdir(parents=True, exist_ok=True)

        edges_dir = out_path / "edges"
        edges_dir.mkdir(parents=True, exist_ok=True)

        custody_dir = out_path / "custody"
        custody_dir.mkdir(parents=True, exist_ok=True)

        # 1. Manifest
        manifest_path = out_path / "manifest.json"
        manifest_path.write_bytes(canonical_json_bytes(package.manifest))

        # 2. Signature
        sig_path = out_path / "signature.json"
        sig_path.write_bytes(canonical_json_bytes(package.signature))

        # 3. Objects
        for obj in package.objects:
            obj_path = objects_dir / f"{obj.object_id}.json"
            obj_path.write_bytes(canonical_json_bytes(obj))

        # 4. Edges
        for edge in package.edges:
            edge_path = edges_dir / f"{edge.object_id}.json"
            edge_path.write_bytes(canonical_json_bytes(edge))

        # 5. Custody Chain
        custody_path = custody_dir / "chain_of_custody.json"
        custody_path.write_bytes(canonical_json_bytes(package.custody_chain))

        return str(out_path)

    @classmethod
    def export_to_zip(cls, package: EvidencePackage, zip_file_path: Union[str, Path]) -> str:
        """Exports package into a portable, compressed ZIP archive."""
        zip_path = Path(zip_file_path)
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Manifest & Signature
            zf.writestr("manifest.json", canonical_json_bytes(package.manifest))
            zf.writestr("signature.json", canonical_json_bytes(package.signature))

            # Objects
            for obj in package.objects:
                zf.writestr(f"objects/{obj.object_id}.json", canonical_json_bytes(obj))

            # Edges
            for edge in package.edges:
                zf.writestr(f"edges/{edge.object_id}.json", canonical_json_bytes(edge))

            # Custody
            zf.writestr("custody/chain_of_custody.json", canonical_json_bytes(package.custody_chain))

        return str(zip_path)

    @classmethod
    def load_from_directory(cls, dir_path: Union[str, Path]) -> EvidencePackage:
        """Loads EvidencePackage from directory."""
        p = Path(dir_path)
        manifest_raw = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
        manifest = PackageManifest(**manifest_raw)

        sig_raw = json.loads((p / "signature.json").read_text(encoding="utf-8"))
        signature = PackageSignature(**sig_raw)

        objects = []
        for obj_file in (p / "objects").glob("*.json"):
            data = json.loads(obj_file.read_text(encoding="utf-8"))
            objects.append(deserialize_evidence_object(data))

        edges = []
        edges_dir = p / "edges"
        if edges_dir.exists():
            for edge_file in edges_dir.glob("*.json"):
                data = json.loads(edge_file.read_text(encoding="utf-8"))
                edges.append(DependencyEdge(**data))

        custody_chain = []
        custody_file = p / "custody" / "chain_of_custody.json"
        if custody_file.exists():
            data_list = json.loads(custody_file.read_text(encoding="utf-8"))
            custody_chain = [ChainOfCustodyEvent(**item) for item in data_list]

        return EvidencePackage(
            manifest=manifest,
            signature=signature,
            objects=objects,
            edges=edges,
            custody_chain=custody_chain
        )

    @classmethod
    def load_from_zip(cls, zip_file_path: Union[str, Path]) -> EvidencePackage:
        """Loads EvidencePackage from ZIP archive."""
        with zipfile.ZipFile(zip_file_path, "r") as zf:
            manifest_raw = json.loads(zf.read("manifest.json").decode("utf-8"))
            manifest = PackageManifest(**manifest_raw)

            sig_raw = json.loads(zf.read("signature.json").decode("utf-8"))
            signature = PackageSignature(**sig_raw)

            objects = []
            edges = []
            custody_chain = []

            for name in zf.namelist():
                if name.startswith("objects/") and name.endswith(".json"):
                    data = json.loads(zf.read(name).decode("utf-8"))
                    objects.append(deserialize_evidence_object(data))
                elif name.startswith("edges/") and name.endswith(".json"):
                    data = json.loads(zf.read(name).decode("utf-8"))
                    edges.append(DependencyEdge(**data))
                elif name == "custody/chain_of_custody.json":
                    data_list = json.loads(zf.read(name).decode("utf-8"))
                    custody_chain = [ChainOfCustodyEvent(**item) for item in data_list]

            return EvidencePackage(
                manifest=manifest,
                signature=signature,
                objects=objects,
                edges=edges,
                custody_chain=custody_chain
            )

    import_from_directory = load_from_directory
    import_from_zip = load_from_zip
