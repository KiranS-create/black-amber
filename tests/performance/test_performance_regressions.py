"""
SIH26237 - Automated Performance Regression Tests & Latency Guards.
Validates that runtime latency, memory footprint, and algorithmic complexity
remain within strict performance budgets across all core subsystems.
"""

import time
import sys
import numpy as np
import pytest

from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import encrypt_aes_gcm, decrypt_aes_gcm
from core.crypto.key_derivation import derive_key
from core.watermark.pipeline import PrintCameraWatermarkEncoder, PrintCameraWatermarkDecoder
from core.watermark.base import WatermarkPayload, WatermarkStatus
from core.ledger.scale import ScalableLedger
from core.ledger.ledger import EvidenceEvent
from core.lineage.scale import SparseLineageIndex, SparseLineageNode, LineageTraversalState
from core.telemetry.scale import ScalableTelemetryProvider, CompactTelemetryRecord
from core.identity.federated import FederatedIdentityDirectory, LocalDirectoryAdapter, CompactIdentityRecord
from core.identity.models import Identity, IdentityStatus
from core.attribution.investigation import ForensicInvestigationEngine


class TestPerformanceRegressions:
    """Automated guards against latency, throughput, and memory bloat regressions."""

    def test_post_quantum_crypto_budget(self):
        """Verify ML-KEM-768 and ML-DSA-65 operations execute within production latency budgets."""
        # ML-KEM Keygen + Encaps + Decaps
        t0 = time.perf_counter()
        kem_kp = MLKEM768.generate_keypair()
        enc = MLKEM768.encapsulate(kem_kp.public_key_bytes)
        ss2 = MLKEM768.decapsulate(kem_kp.private_key_bytes, enc.ciphertext)
        kem_duration_ms = (time.perf_counter() - t0) * 1000.0

        assert enc.shared_secret == ss2
        assert kem_duration_ms < 350.0, f"ML-KEM operations exceeded latency budget: {kem_duration_ms:.2f}ms"

        # ML-DSA Sign + Verify
        t0 = time.perf_counter()
        sig_kp = MLDSA65.generate_keypair()
        payload = b"AegisTrace Performance Regression Payload"
        sig = MLDSA65.sign(sig_kp.private_key_bytes, payload)
        valid = MLDSA65.verify(sig_kp.public_key_bytes, payload, sig)
        dsa_duration_ms = (time.perf_counter() - t0) * 1000.0

        assert valid is True
        assert dsa_duration_ms < 1500.0, f"ML-DSA operations exceeded latency budget: {dsa_duration_ms:.2f}ms"

    def test_watermark_encode_decode_budget_and_fidelity(self):
        """Verify watermark embed & extract maintains 100% bit fidelity and sub-second execution."""
        encoder = PrintCameraWatermarkEncoder()
        decoder = PrintCameraWatermarkDecoder()
        canvas = np.full((1000, 800, 3), 245, dtype=np.uint8)
        codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128-bit Tardos/fingerprint codeword
        payload = WatermarkPayload(
            document_id="doc_perf",
            release_id="rel_budget_guard",
            recipient_id="usr_perf_test",
            codeword=codeword
        )

        t0 = time.perf_counter()
        wm_canvas = encoder.encode(canvas, payload)
        embed_ms = (time.perf_counter() - t0) * 1000.0

        assert embed_ms < 400.0, f"Watermark embedding exceeded latency budget: {embed_ms:.2f}ms"

        t0 = time.perf_counter()
        observation = decoder.decode(
            wm_canvas,
            expected_document_id="doc_perf",
            expected_release_id="rel_budget_guard",
            expected_codeword_length=128
        )
        extract_ms = (time.perf_counter() - t0) * 1000.0

        assert extract_ms < 300.0, f"Watermark extraction exceeded latency budget: {extract_ms:.2f}ms"
        assert observation.status == WatermarkStatus.RECOVERED
        assert observation.is_valid is True
        assert observation.observed_symbols == codeword

    def test_ledger_append_and_query_budget(self):
        """Verify ScalableLedger satisfies O(1) indexed lookups with < 100 µs latency."""
        ledger = ScalableLedger(checkpoint_interval=100)
        tenant = "tenant_perf_guard"

        prev_hash = "0" * 64
        for i in range(500):
            ev = EvidenceEvent(
                event_id=f"ev_perf_{i:04d}",
                timestamp="2026-09-27T12:00:00Z",
                event_type="DOCUMENT_RELEASED",
                document_id="doc_perf_ledger",
                release_id="rel_perf_ledger",
                recipient_id=f"rec_{(i % 10):03d}",
                device_id="dev_001",
                ip_address="192.168.1.1",
                algorithm="ML-DSA-65",
                artifact_hash="a" * 64,
                evidence_hash="e" * 64,
                signature="s" * 128,
                previous_event_hash=prev_hash
            )
            prev_hash = ledger.append_event(ev, tenant_id=tenant)

        # O(1) Lookup benchmark
        t0 = time.perf_counter()
        ev = ledger.get_event("ev_perf_0250", tenant_id=tenant)
        lookup_us = (time.perf_counter() - t0) * 1_000_000.0

        assert ev is not None
        assert lookup_us < 100.0, f"Ledger lookup exceeded latency budget: {lookup_us:.2f}µs"

    def test_sparse_lineage_slotted_memory_and_deep_traversal(self):
        """Verify SparseLineageNode uses compact slots and traverses 1,000 hops non-recursively in < 10 ms."""
        node = SparseLineageNode("c1", None, "d1", "r1")
        # Ensure __dict__ is eliminated
        assert not hasattr(node, "__dict__"), "SparseLineageNode has __dict__; slots failed"

        index = SparseLineageIndex()
        tenant = "tenant_lineage_perf"

        # Construct 1,000-hop ancestor chain
        prev_copy = None
        for i in range(1000):
            cid = f"copy_chain_{i:04d}"
            n = SparseLineageNode(
                copy_id=cid,
                parent_copy_id=prev_copy,
                document_id="doc_lineage_chain",
                recipient_id=f"rec_{i:04d}",
                tenant_id=tenant,
                depth=i
            )
            index.insert_node(n)
            prev_copy = cid

        t0 = time.perf_counter()
        result = index.traverse_ancestors(prev_copy, tenant_id=tenant, max_hops=1000)
        traversal_ms = (time.perf_counter() - t0) * 1000.0

        assert result.state == LineageTraversalState.VALID
        assert result.depth == 999
        assert traversal_ms < 10.0, f"Deep lineage traversal exceeded budget: {traversal_ms:.2f}ms"

    def test_scalable_telemetry_indexed_window_query_budget(self):
        """Verify ScalableTelemetryProvider executes bisect window queries on 5,000 records in < 15 ms."""
        provider = ScalableTelemetryProvider()
        tenant = "tenant_telemetry_perf"

        records = []
        for i in range(5000):
            records.append({
                "event_id": f"tel_{i:05d}",
                "event_type": "ACCESS",
                "source_system": "EDR",
                "timestamp_epoch": 1000.0 + i * 0.1,
                "tenant_id": tenant,
                "copy_id": f"copy_{i % 50}"
            })
        provider.ingest_batch(records, tenant_id=tenant)

        t0 = time.perf_counter()
        results = provider.query_time_window(1100.0, 1200.0, tenant_id=tenant)
        query_ms = (time.perf_counter() - t0) * 1000.0

        assert len(results) > 0
        assert query_ms < 15.0, f"Telemetry time-window query exceeded budget: {query_ms:.2f}ms"

    def test_federated_identity_email_indexed_lookup(self):
        """Verify FederatedProviderAdapter inverted email lookup resolves in < 100 µs."""
        adapter = LocalDirectoryAdapter(tenant_id="tenant_idp_perf")
        for i in range(2000):
            ident = Identity(
                identity_id=f"usr_idp_{i:04d}",
                provider="local_directory",
                provider_subject=f"sub_{i:04d}",
                display_name=f"User {i}",
                email=f"user_{i:04d}@aegistrace.corp",
                organization_id="tenant_idp_perf",
                department="Forensics",
                status=IdentityStatus.ACTIVE,
                created_at="2026-09-27T00:00:00Z"
            )
            adapter.add_identity(ident)

        t0 = time.perf_counter()
        found = adapter.search_by_email("user_1500@aegistrace.corp")
        lookup_us = (time.perf_counter() - t0) * 1_000_000.0

        assert found is not None
        assert found.identity_id == "usr_idp_1500"
        assert lookup_us < 100.0, f"Identity email search exceeded budget: {lookup_us:.2f}µs"
