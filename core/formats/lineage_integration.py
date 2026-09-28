"""
SIH26237 - Multi-Format Forensic Lineage Integration.
Binds original artifact identities, format validation stages, canonical representations,
rendered carriers, and distributed watermarked copies into the existing Sparse Lineage DAG.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from core.lineage.scale import SparseLineageIndex, SparseLineageNode, LineageTraversalState
from core.formats.models import (
    OriginalArtifactIdentity,
    ForensicCarrierIdentity,
    ForensicCarrier
)
from core.formats.canonical import CanonicalDocument


class MultiFormatLineageBridge:
    """
    Emits multi-format transformation events into the existing SparseLineageIndex.
    """

    def __init__(self, lineage_index: Optional[SparseLineageIndex] = None):
        self.lineage_index = lineage_index or SparseLineageIndex()

    def record_artifact_ingest(
        self,
        artifact: OriginalArtifactIdentity,
        tenant_id: Optional[str] = None
    ) -> SparseLineageNode:
        """Records initial pristine artifact ingestion node."""
        tenant = tenant_id or artifact.tenant_id
        node = SparseLineageNode(
            copy_id=artifact.artifact_id,
            parent_copy_id=None,
            document_id=artifact.artifact_id,
            recipient_id="SYSTEM_INGEST",
            tenant_id=tenant,
            depth=0,
            fingerprint_ref=artifact.original_hash
        )
        self.lineage_index.insert_node(node)
        return node

    def record_carrier_generation(
        self,
        artifact: OriginalArtifactIdentity,
        carrier: ForensicCarrier,
        tenant_id: Optional[str] = None
    ) -> SparseLineageNode:
        """Records rendered visual carrier derived from original artifact."""
        tenant = tenant_id or artifact.tenant_id
        node = SparseLineageNode(
            copy_id=carrier.carrier_id,
            parent_copy_id=artifact.artifact_id,
            document_id=artifact.artifact_id,
            recipient_id="CARRIER_RENDER",
            tenant_id=tenant,
            depth=1,
            fingerprint_ref=f"carrier:{carrier.component_type}:{carrier.component_index}"
        )
        self.lineage_index.insert_node(node)
        return node

    def record_watermarked_distribution(
        self,
        carrier: ForensicCarrier,
        recipient_id: str,
        watermark_codeword_hash: str,
        release_id: str,
        tenant_id: Optional[str] = None
    ) -> SparseLineageNode:
        """Records recipient-specific watermarked copy distribution."""
        dist_copy_id = f"{carrier.carrier_id}_rec_{recipient_id[:8]}"
        tenant = tenant_id or "default_tenant"

        node = SparseLineageNode(
            copy_id=dist_copy_id,
            parent_copy_id=carrier.carrier_id,
            document_id=carrier.parent_artifact_id,
            recipient_id=recipient_id,
            tenant_id=tenant,
            depth=2,
            release_id=release_id,
            fingerprint_ref=watermark_codeword_hash
        )
        self.lineage_index.insert_node(node)
        return node
