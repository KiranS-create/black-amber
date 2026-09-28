"""
Forensic Investigation Multi-Index Join Query Path for AegisTrace.

Executes end-to-end multi-index join across:
Watermark Marker -> Copy Lineage -> Decryption Event -> Cryptographic Principal
-> Federated Identity -> Host/Endpoint Telemetry -> Chain of Custody Dossier.

Designed to execute in sub-millisecond to low single-digit milliseconds across
1,000,000 events without full table scans or unbounded recursion.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time

from core.lineage.scale import SparseLineageIndex, SparseLineageNode
from core.ledger.scale import ScalableLedger
from core.identity.federated import FederatedIdentityDirectory
from core.telemetry.scale import ScalableTelemetryProvider, CompactTelemetryRecord


@dataclass
class ForensicInvestigationDossier:
    """Consolidated forensic investigation dossier produced by multi-index join."""
    investigation_id: str
    tenant_id: str
    query_timestamp_epoch: float
    leaked_copy_id: str
    root_release_id: str
    lineage_depth: int
    ancestor_path: List[str]
    descendant_copies: List[str]
    recipient_id: Optional[str]
    decryption_event_id: Optional[str]
    decryption_event_hash: Optional[str]
    resolved_identity_id: Optional[str]
    resolved_display_name: Optional[str]
    resolved_email: Optional[str]
    identity_status: Optional[str]
    telemetry_events_count: int
    correlated_telemetry: List[Dict[str, Any]]
    execution_time_ms: float
    fail_closed_reason: Optional[str] = None


class ForensicInvestigationEngine:
    """
    Orchestrates high-performance forensic multi-index joins across scaled sub-systems.
    """
    def __init__(
        self,
        lineage_index: SparseLineageIndex,
        ledger: ScalableLedger,
        identity_directory: FederatedIdentityDirectory,
        telemetry_provider: ScalableTelemetryProvider
    ):
        self.lineage_index = lineage_index
        self.ledger = ledger
        self.identity_directory = identity_directory
        self.telemetry_provider = telemetry_provider

    def investigate_copy(
        self,
        copy_id: str,
        tenant_id: str = "default_tenant",
        telemetry_window_seconds: float = 3600.0
    ) -> ForensicInvestigationDossier:
        """
        Executes complete multi-index join for a target copy_id.
        """
        t0 = time.perf_counter()
        investigation_id = f"inv_{copy_id}_{int(time.time())}"

        # 1. Lineage lookup & iterative ancestor traversal
        copy_node = self.lineage_index.get_node(copy_id, tenant_id=tenant_id)
        if not copy_node:
            t_elapsed = (time.perf_counter() - t0) * 1000.0
            return ForensicInvestigationDossier(
                investigation_id=investigation_id,
                tenant_id=tenant_id,
                query_timestamp_epoch=time.time(),
                leaked_copy_id=copy_id,
                root_release_id="UNKNOWN",
                lineage_depth=0,
                ancestor_path=[],
                descendant_copies=[],
                recipient_id=None,
                decryption_event_id=None,
                decryption_event_hash=None,
                resolved_identity_id=None,
                resolved_display_name=None,
                resolved_email=None,
                identity_status=None,
                telemetry_events_count=0,
                correlated_telemetry=[],
                execution_time_ms=t_elapsed,
                fail_closed_reason="COPY_NOT_FOUND_IN_LINEAGE"
            )

        ancestor_res = self.lineage_index.traverse_ancestors(copy_id, tenant_id=tenant_id)
        ancestor_ids = ancestor_res.path
        descendant_res = self.lineage_index.traverse_descendants_bfs(copy_id, tenant_id=tenant_id)
        descendant_ids = descendant_res.path

        root_node = self.lineage_index.get_node(ancestor_res.root_copy_id, tenant_id=tenant_id) if ancestor_res.root_copy_id else copy_node
        recipient_id = copy_node.recipient_id

        # 2. Ledger lookup: find signed provenance decryption event
        decryption_event = self.ledger.find_decryption_event(
            recipient_id=recipient_id,
            release_id=copy_node.release_id,
            document_id=copy_node.document_id,
            tenant_id=tenant_id
        )

        decryption_event_id = decryption_event.event_id if decryption_event else None
        decryption_event_hash = decryption_event.compute_event_hash() if decryption_event else None

        # 3. Federated Identity resolution
        resolved_summary, id_status = self.identity_directory.resolve_recipient(
            recipient_id=recipient_id,
            tenant_id=tenant_id
        )

        # 4. Telemetry join: find telemetry for this copy and recipient
        telemetry_recs = self.telemetry_provider.query_by_copy_id(copy_id, tenant_id=tenant_id)
        telemetry_dicts = [
            {
                "event_id": r.event_id,
                "event_type": r.event_type,
                "source_system": r.source_system,
                "device_id": r.device_id,
                "timestamp_epoch": r.timestamp_epoch
            }
            for r in telemetry_recs
        ]

        t_elapsed = (time.perf_counter() - t0) * 1000.0

        return ForensicInvestigationDossier(
            investigation_id=investigation_id,
            tenant_id=tenant_id,
            query_timestamp_epoch=time.time(),
            leaked_copy_id=copy_id,
            root_release_id=root_node.release_id,
            lineage_depth=len(ancestor_ids),
            ancestor_path=ancestor_ids,
            descendant_copies=descendant_ids,
            recipient_id=recipient_id,
            decryption_event_id=decryption_event_id,
            decryption_event_hash=decryption_event_hash,
            resolved_identity_id=resolved_summary.identity_id if resolved_summary else None,
            resolved_display_name=resolved_summary.display_name if resolved_summary else None,
            resolved_email=resolved_summary.email if resolved_summary else None,
            identity_status=id_status,
            telemetry_events_count=len(telemetry_dicts),
            correlated_telemetry=telemetry_dicts,
            execution_time_ms=t_elapsed,
            fail_closed_reason=None
        )
