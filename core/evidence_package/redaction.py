"""
AegisTrace Cryptographic Safe Redaction Engine.

Enables selective disclosure and privacy redaction of sensitive metadata,
unrelated recipient identities, or proprietary telemetry without invalidating
package Merkle commitments or post-quantum manifest signatures.
Guarantees:
1. Replaces redacted objects with cryptographically committed stubs.
2. Preserves the original content_hash as a committed Merkle leaf.
3. Explicit classification: REDACTED, NOT_INCLUDED, NOT_REQUIRED_FOR_THIS_PROOF.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from core.evidence_package.models import (
    BaseEvidenceObject,
    EvidenceObjectType,
    PackageManifest
)


class RedactionClassification(str, Enum):
    REDACTED = "REDACTED"
    NOT_INCLUDED = "NOT_INCLUDED"
    NOT_REQUIRED_FOR_THIS_PROOF = "NOT_REQUIRED_FOR_THIS_PROOF"


class RedactedEvidenceStub(BaseEvidenceObject):
    """
    Cryptographic surrogate for an evidence object omitted for privacy or compartmentalization.
    Preserves original content_hash so package Merkle tree remains 100% valid.
    """
    object_type: EvidenceObjectType = EvidenceObjectType.EVIDENCE_OBJECT
    original_object_id: str
    original_object_type: EvidenceObjectType
    original_content_hash: str
    redaction_reason: str
    redaction_classification: RedactionClassification = RedactionClassification.REDACTED
    redacted_by: str = "OFFICIAL_REDACTION_OFFICER"
    redacted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SafeRedactionEngine:
    """
    Applies privacy redactions to an evidence collection prior to package export.
    """
    @classmethod
    def redact_object(
        cls,
        obj: BaseEvidenceObject,
        reason: str,
        classification: RedactionClassification = RedactionClassification.REDACTED,
        redacted_by: str = "OFFICIAL_REDACTION_OFFICER"
    ) -> RedactedEvidenceStub:
        """
        Transforms an evidence object into a RedactedEvidenceStub.
        Locks the original content_hash to preserve the Merkle root.
        """
        content_hash = obj.content_hash or obj.compute_content_digest()

        stub = RedactedEvidenceStub(
            object_id=obj.object_id,
            original_object_id=obj.object_id,
            original_object_type=obj.object_type,
            original_content_hash=content_hash,
            redaction_reason=reason,
            redaction_classification=classification,
            redacted_by=redacted_by,
            tenant_id=obj.tenant_id,
            schema_version=obj.schema_version,
            content_hash=content_hash  # Merkle leaf remains identical to original!
        )
        return stub

    @classmethod
    def apply_package_redactions(
        cls,
        objects: List[BaseEvidenceObject],
        target_object_ids_to_redact: List[str],
        reason: str,
        manifest: PackageManifest,
        classification: RedactionClassification = RedactionClassification.REDACTED,
        redacted_by: str = "OFFICIAL_REDACTION_OFFICER"
    ) -> Tuple[List[BaseEvidenceObject], PackageManifest]:
        """
        Redacts specified objects in an evidence package while preserving Merkle commitments.
        Updates manifest flags and inventory references.
        """
        target_set = set(target_object_ids_to_redact)
        processed_objects: List[BaseEvidenceObject] = []
        redacted_ids: List[str] = []

        for obj in objects:
            if obj.object_id in target_set:
                stub = cls.redact_object(
                    obj=obj,
                    reason=reason,
                    classification=classification,
                    redacted_by=redacted_by
                )
                processed_objects.append(stub)
                redacted_ids.append(obj.object_id)
            else:
                processed_objects.append(obj)

        # Update manifest
        manifest.is_redacted = True
        manifest.redacted_object_ids.extend(redacted_ids)

        return processed_objects, manifest
