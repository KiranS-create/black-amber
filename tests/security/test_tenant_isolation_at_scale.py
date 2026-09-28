"""
Security and Multi-Tenant Isolation Verification at Scale.

Validates that high volume in Tenant A (10,000+ entities) does not leak or contaminate
Tenant B (small enterprise or defense enclave):
- Lineage boundary enforcement
- Tamper-evident ledger event query partitioning
- Federated identity resolution scope
- Telemetry store partitioning
- Forensic investigation dossier fail-closed isolation
"""

import pytest
import hashlib
from datetime import datetime, timezone

from core.lineage.scale import SparseLineageIndex, SparseLineageNode
from core.ledger.scale import ScalableLedger
from core.ledger.ledger import EvidenceEvent
from core.identity.federated import FederatedIdentityDirectory
from core.identity.models import Identity, IdentityStatus
from core.telemetry.scale import ScalableTelemetryProvider
from core.attribution.investigation import ForensicInvestigationEngine


def test_cross_tenant_isolation_under_scale_differential():
    lineage = SparseLineageIndex()
    ledger = ScalableLedger(checkpoint_interval=100)
    id_dir = FederatedIdentityDirectory()
    telemetry = ScalableTelemetryProvider()

    tenant_large = "tenant_enterprise_mega"
    tenant_small = "tenant_defense_enclave"

    # Populate 5,000 items in tenant_large
    prev_h_large = ledger.get_last_event_hash()
    for i in range(5000):
        cid = f"cpy_l_{i:05d}"
        rid = f"rec_l_{i % 500:03d}"
        uid = f"usr_l_{i % 500:03d}"

        lineage.insert_node(SparseLineageNode(
            copy_id=cid,
            parent_copy_id=None,
            document_id="doc_large",
            recipient_id=rid,
            tenant_id=tenant_large
        ))

        if i % 10 == 0:
            ev = EvidenceEvent(
                event_id=f"ev_l_{i:05d}",
                timestamp="2026-09-27T12:00:00Z",
                event_type="DECRYPTION_EVENT",
                document_id="doc_large",
                release_id="rel_large",
                recipient_id=rid,
                artifact_hash=f"art_l_{i}",
                evidence_hash=f"evh_l_{i}",
                algorithm="ML-DSA-65",
                signature="sig",
                previous_event_hash=prev_h_large
            )
            prev_h_large = ledger.append_event(ev, tenant_id=tenant_large)

        if i < 500:
            id_dir.cache_identity(Identity(
                identity_id=uid,
                provider="entra",
                provider_subject=f"sub_{uid}",
                display_name=f"Large User {i}",
                email=f"user_{i}@mega.com",
                organization_id=tenant_large,
                status=IdentityStatus.ACTIVE
            ), tenant_id=tenant_large)
            id_dir.bind_recipient(rid, uid, tenant_id=tenant_large)

        telemetry.ingest_record(
            event_id=f"tel_l_{i:05d}",
            event_type="FILE_ACCESS",
            source_system="EDR",
            timestamp_epoch=1700000000.0 + i,
            copy_id=cid,
            tenant_id=tenant_large
        )

    # Populate 5 items in tenant_small
    prev_h_small = ledger.get_last_event_hash()
    for j in range(5):
        cid_s = f"cpy_s_{j}"
        rid_s = f"rec_s_{j}"
        uid_s = f"usr_s_{j}"

        lineage.insert_node(SparseLineageNode(
            copy_id=cid_s,
            parent_copy_id=None,
            document_id="doc_small",
            recipient_id=rid_s,
            tenant_id=tenant_small
        ))

        ev_s = EvidenceEvent(
            event_id=f"ev_s_{j}",
            timestamp="2026-09-27T12:00:00Z",
            event_type="DECRYPTION_EVENT",
            document_id="doc_small",
            release_id="rel_small",
            recipient_id=rid_s,
            artifact_hash=f"art_s_{j}",
            evidence_hash=f"evh_s_{j}",
            algorithm="ML-DSA-65",
            signature="sig",
            previous_event_hash=prev_h_small
        )
        prev_h_small = ledger.append_event(ev_s, tenant_id=tenant_small)

        id_dir.cache_identity(Identity(
            identity_id=uid_s,
            provider="local",
            provider_subject=f"sub_{uid_s}",
            display_name=f"Small User {j}",
            email=f"user_{j}@enclave.gov",
            organization_id=tenant_small,
            status=IdentityStatus.ACTIVE
        ), tenant_id=tenant_small)
        id_dir.bind_recipient(rid_s, uid_s, tenant_id=tenant_small)

        telemetry.ingest_record(
            event_id=f"tel_s_{j}",
            event_type="FILE_ACCESS",
            source_system="EDR",
            timestamp_epoch=1700000000.0 + j,
            copy_id=cid_s,
            tenant_id=tenant_small
        )

    # 1. Assert Lineage counts and zero cross-visibility
    assert lineage.count(tenant_large) == 5000
    assert lineage.count(tenant_small) == 5
    assert lineage.get_node("cpy_l_00001", tenant_id=tenant_small) is None
    assert lineage.get_node("cpy_s_1", tenant_id=tenant_large) is None

    # 2. Assert Ledger isolation
    assert ledger.count(tenant_large) == 500
    assert ledger.count(tenant_small) == 5
    assert ledger.find_decryption_event("rec_l_001", "rel_large", tenant_id=tenant_small) is None
    assert ledger.find_decryption_event("rec_s_1", "rel_small", tenant_id=tenant_large) is None

    # 3. Assert Identity isolation
    s_cross, st_cross = id_dir.resolve_recipient("rec_l_001", tenant_id=tenant_small)
    assert s_cross is None
    assert st_cross == "NOT_FOUND"

    # 4. Assert Telemetry isolation
    assert len(telemetry.query_by_copy_id("cpy_l_00001", tenant_id=tenant_small)) == 0

    # 5. Assert Forensic Investigation Engine fail-closed behavior across tenants
    engine = ForensicInvestigationEngine(lineage, ledger, id_dir, telemetry)
    # Attempt to investigate Tenant Large copy from Tenant Small scope
    dossier_fail = engine.investigate_copy("cpy_l_00001", tenant_id=tenant_small)
    assert dossier_fail.fail_closed_reason == "COPY_NOT_FOUND_IN_LINEAGE"
    assert dossier_fail.recipient_id is None
    assert dossier_fail.resolved_identity_id is None
