"""
SIH26237 - Multi-Format Evidence Package Integration.
Assembles verifiable RFC 8785 canonical evidence packages binding original artifact identities,
validated formats, canonical representations, carrier identities, and watermark observations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import hashlib

from core.formats.models import (
    OriginalArtifactIdentity,
    ForensicCarrierIdentity,
    ForensicCarrier,
    SecurityValidationResult
)
from core.formats.canonical import CanonicalDocument
from core.evidence_package.canonical import canonical_json_dumps, compute_content_hash
from core.evidence_package.models import BaseEvidenceObject, EvidenceObjectType


class MultiFormatArtifactEvidence(BaseEvidenceObject):
    """
    Formal evidence object preserving multi-format forensic binding.
    """
    object_type: EvidenceObjectType = EvidenceObjectType.ARTIFACT
    original_artifact_id: str
    original_file_hash: str        # Bitwise SHA-256 of original file
    detected_format: str
    declared_extension: str
    validated_mime: str
    adapter_version: str
    security_status: str           # "PASSED", "FAIL_CLOSED"
    canonical_content_digest: str  # Semantic content SHA-256
    carrier_identities: List[Dict[str, Any]] = Field(default_factory=list)
    extraction_results: Optional[Dict[str, Any]] = None
    transformation_chain: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        artifact: OriginalArtifactIdentity,
        canonical_doc: CanonicalDocument,
        sec_result: SecurityValidationResult,
        carriers: List[ForensicCarrier],
        extraction_obs: Optional[Dict[str, Any]] = None,
        transformations: Optional[List[Dict[str, Any]]] = None
    ) -> 'MultiFormatArtifactEvidence':
        carrier_meta = [
            {
                "carrier_id": c.carrier_id,
                "component_type": c.component_type,
                "component_index": c.component_index,
                "rendering_profile": c.rendering_profile,
                "dimensions": f"{c.width_px}x{c.height_px}"
            }
            for c in carriers
        ]

        obj = cls(
            object_id=f"ev_art_{artifact.artifact_id}",
            tenant_id=artifact.tenant_id,
            original_artifact_id=artifact.artifact_id,
            original_file_hash=artifact.original_hash,
            detected_format=artifact.detected_format,
            declared_extension=artifact.declared_extension,
            validated_mime=artifact.validated_mime,
            adapter_version=artifact.parser_adapter_version,
            security_status="PASSED" if sec_result.is_safe else "FAIL_CLOSED",
            canonical_content_digest=canonical_doc.compute_content_digest(),
            carrier_identities=carrier_meta,
            extraction_results=extraction_obs,
            transformation_chain=transformations or []
        )
        obj.content_hash = obj.compute_content_digest()
        return obj
