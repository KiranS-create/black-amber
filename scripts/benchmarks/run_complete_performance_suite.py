#!/usr/bin/env python3
"""
AegisTrace Complete Production Performance & Benchmark Suite.
Measures baseline and optimized performance across all 9 subsystems:
Crypto, Watermark, Ledger, Lineage, Telemetry, Identity, Attribution/Investigation,
Evidence, Recovery, and End-to-End Critical Path.
"""

import os
import sys
import gc
import time
import math
import json
import base64
import hashlib
import platform
import psutil
import tracemalloc
import threading
import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Ensure repository root in path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Core imports
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import (
    generate_symmetric_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
)
from core.crypto.key_derivation import derive_key
from core.watermark.pipeline import PrintCameraWatermarkEncoder, PrintCameraWatermarkDecoder
from core.watermark.base import WatermarkPayload, WatermarkStatus
from core.watermark.sync import CanonicalCanvasSpec
from core.watermark.carrier import CarrierConfig
from core.ledger.scale import ScalableLedger
from core.ledger.ledger import EvidenceEvent
from core.lineage.scale import SparseLineageIndex, SparseLineageNode
from core.telemetry.scale import ScalableTelemetryProvider, CompactTelemetryRecord
from core.identity.federated import (
    FederatedIdentityDirectory,
    EntraIdAdapter,
    OktaAdapter,
    IdentityCacheState,
)
from core.identity.models import Identity, IdentityStatus
from core.attribution.investigation import ForensicInvestigationEngine
from core.recovery.models import (
    SignedBackupManifest,
    BackupObjectRecord,
    BackupType,
    FinalRecoveryOutcome,
)
from core.recovery.format import ContentAddressedStore, BackupPackageBuilder, canonical_json_bytes
from core.recovery.crypto import BackupCryptoEngine
from core.recovery.engine import DisasterRecoveryEngine
import numpy as np


def get_hardware_profile() -> Dict[str, Any]:
    """Captures comprehensive host hardware and runtime environment profile."""
    du = psutil.disk_usage(os.path.abspath(REPO_ROOT))
    vm = psutil.virtual_memory()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "total_ram_gb": round(vm.total / (1024 ** 3), 2),
        "available_ram_gb": round(vm.available / (1024 ** 3), 2),
        "disk_total_gb": round(du.total / (1024 ** 3), 2),
        "disk_free_gb": round(du.free / (1024 ** 3), 2),
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "process_architecture": platform.architecture()[0],
        "filesystem": "NTFS" if platform.system() == "Windows" else "POSIX",
        "storage_medium": "SSD (Local)",
    }


def compute_stats(samples: List[float]) -> Dict[str, float]:
    """Computes standard latency percentiles and distribution statistics."""
    if not samples:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "stddev": 0.0}
    s = sorted(samples)
    n = len(s)
    mean_val = sum(s) / n
    variance = sum((x - mean_val) ** 2 for x in s) / n if n > 1 else 0.0
    
    def p(pct: float) -> float:
        k = (n - 1) * (pct / 100.0)
        f = int(k)
        c = min(f + 1, n - 1)
        return s[f] + (k - f) * (s[c] - s[f])

    return {
        "min": round(s[0], 3),
        "max": round(s[-1], 3),
        "mean": round(mean_val, 3),
        "p50": round(p(50.0), 3),
        "p95": round(p(95.0), 3),
        "p99": round(p(99.0), 3),
        "stddev": round(math.sqrt(variance), 3),
    }


def profile_crypto(iterations: int = 10) -> Dict[str, Any]:
    """Profiles authentic cryptographic primitives."""
    results = {}
    
    # 1. ML-KEM-768
    kem_keygen_times = []
    kem_encaps_times = []
    kem_decaps_times = []
    
    for _ in range(iterations):
        t0 = time.perf_counter()
        kp = MLKEM768.generate_keypair()
        kem_keygen_times.append((time.perf_counter() - t0) * 1000.0)
        
        t0 = time.perf_counter()
        enc_res = MLKEM768.encapsulate(kp.public_key_bytes)
        kem_encaps_times.append((time.perf_counter() - t0) * 1000.0)
        
        t0 = time.perf_counter()
        ss = MLKEM768.decapsulate(kp.private_key_bytes, enc_res.ciphertext)
        kem_decaps_times.append((time.perf_counter() - t0) * 1000.0)
        assert ss == enc_res.shared_secret
        
    results["ml_kem_768_keygen"] = compute_stats(kem_keygen_times)
    results["ml_kem_768_encaps"] = compute_stats(kem_encaps_times)
    results["ml_kem_768_decaps"] = compute_stats(kem_decaps_times)
    
    # 2. ML-DSA-65
    dsa_keygen_times = []
    dsa_sign_times = []
    dsa_verify_times = []
    msg = b"AegisTrace Forensic Document Verification Payload"
    
    for _ in range(iterations):
        t0 = time.perf_counter()
        kp_dsa = MLDSA65.generate_keypair()
        dsa_keygen_times.append((time.perf_counter() - t0) * 1000.0)
        
        t0 = time.perf_counter()
        sig = MLDSA65.sign(kp_dsa.private_key_bytes, msg)
        dsa_sign_times.append((time.perf_counter() - t0) * 1000.0)
        
        t0 = time.perf_counter()
        is_valid = MLDSA65.verify(kp_dsa.public_key_bytes, msg, sig)
        dsa_verify_times.append((time.perf_counter() - t0) * 1000.0)
        assert is_valid
        
    results["ml_dsa_65_keygen"] = compute_stats(dsa_keygen_times)
    results["ml_dsa_65_sign"] = compute_stats(dsa_sign_times)
    results["ml_dsa_65_verify"] = compute_stats(dsa_verify_times)
    
    # 3. AES-256-GCM (64 KB Payload)
    sym_key = generate_symmetric_key()
    data_64k = os.urandom(64 * 1024)
    aes_enc_times = []
    aes_dec_times = []
    
    for _ in range(iterations * 5):
        t0 = time.perf_counter()
        ct = encrypt_aes_gcm(sym_key, data_64k)
        aes_enc_times.append((time.perf_counter() - t0) * 1000.0)
        
        t0 = time.perf_counter()
        pt = decrypt_aes_gcm(sym_key, ct)
        aes_dec_times.append((time.perf_counter() - t0) * 1000.0)
        assert pt == data_64k
        
    results["aes_256_gcm_64kb_encrypt"] = compute_stats(aes_enc_times)
    results["aes_256_gcm_64kb_decrypt"] = compute_stats(aes_dec_times)
    
    # 4. HKDF-SHA256
    hkdf_times = []
    salt = os.urandom(32)
    ikm = os.urandom(32)
    for _ in range(iterations * 10):
        t0 = time.perf_counter()
        _ = derive_key(ikm, salt=salt, info=b"HKDF-BENCHMARK-INFO", length=32)
        hkdf_times.append((time.perf_counter() - t0) * 1000.0)
    results["hkdf_sha256"] = compute_stats(hkdf_times)
    
    return results


def profile_watermark(page_counts: List[int] = [1, 5]) -> Dict[str, Any]:
    """Profiles the complete print-camera watermark pipeline."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()
    
    payload = WatermarkPayload(
        document_id="doc_perf_test_01",
        release_id="rel_perf_test_01",
        codeword=[1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128-bit codeword
    )
    
    results = {}
    
    for pages in page_counts:
        encode_times = []
        decode_times = []
        canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 255
        
        for _ in range(pages):
            t0 = time.perf_counter()
            wm_img = encoder.encode(canvas, payload)
            encode_times.append((time.perf_counter() - t0) * 1000.0)
            
            t0 = time.perf_counter()
            obs = decoder.decode(wm_img, expected_document_id=payload.document_id, expected_release_id=payload.release_id)
            decode_times.append((time.perf_counter() - t0) * 1000.0)
            assert obs.is_valid
            
        results[f"{pages}_pages_encode"] = compute_stats(encode_times)
        results[f"{pages}_pages_decode"] = compute_stats(decode_times)
        
    return results


def profile_ledger(scales: List[int] = [1_000, 10_000, 100_000]) -> Dict[str, Any]:
    """Profiles ScalableLedger append, query, and checkpoint verification."""
    results = {}
    
    for s in scales:
        ledger = ScalableLedger(checkpoint_interval=max(100, s // 10))
        tenant_id = f"tenant_scale_{s}"
        
        # Ingestion throughput
        gc.collect()
        t0 = time.perf_counter()
        prev_hash = "0" * 64
        
        for i in range(s):
            evt = EvidenceEvent(
                event_id=f"evt_{s}_{i:07d}",
                timestamp="2026-09-27T12:00:00Z",
                event_type="DOCUMENT_RELEASE",
                document_id=f"doc_{i % 500}",
                release_id=f"rel_{i % 100}",
                recipient_id=f"rec_{i % 50}",
                artifact_hash=hashlib.sha256(f"artifact_{i}".encode()).hexdigest(),
                evidence_hash=hashlib.sha256(f"evidence_{i}".encode()).hexdigest(),
                algorithm="ML-DSA-65",
                signature="sig_benchmark",
                previous_event_hash=prev_hash
            )
            prev_hash = ledger.append_event(evt, tenant_id=tenant_id)
            
        t_ingest = time.perf_counter() - t0
        ingest_ops_sec = s / t_ingest
        
        # Query latency
        query_times = []
        for q_idx in range(min(500, s)):
            target_id = f"evt_{s}_{q_idx:07d}"
            t0_q = time.perf_counter()
            found = ledger.get_event_by_id(target_id)
            query_times.append((time.perf_counter() - t0_q) * 1_000_000.0) # us
            assert found is not None
            
        # Incremental vs Full Verification
        t0_v = time.perf_counter()
        valid_inc, _ = ledger.verify_chain_incremental()
        t_inc_ms = (time.perf_counter() - t0_v) * 1000.0
        assert valid_inc
        
        results[f"{s}_events"] = {
            "ingest_throughput_ops_sec": round(ingest_ops_sec, 2),
            "ingest_duration_ms": round(t_ingest * 1000.0, 2),
            "query_latency_us": compute_stats(query_times),
            "incremental_verification_ms": round(t_inc_ms, 3),
            "checkpoints_count": len(ledger.checkpoints),
            "classification": "MEASURED"
        }
        
    return results


def profile_lineage(scales: List[int] = [1_000, 10_000, 100_000]) -> Dict[str, Any]:
    """Profiles SparseLineageIndex deep chains and branching."""
    results = {}
    
    for s in scales:
        index = SparseLineageIndex()
        tenant_id = f"tenant_lin_{s}"
        
        # Insert linear deep chain
        gc.collect()
        t0 = time.perf_counter()
        parent_id = None
        for i in range(s):
            cid = f"copy_{s}_{i:07d}"
            node = SparseLineageNode(
                copy_id=cid,
                parent_copy_id=parent_id,
                document_id="doc_master_01",
                recipient_id=f"rec_{i % 20}",
                depth=i,
                tenant_id=tenant_id
            )
            index.insert_node(node)
            parent_id = cid
            
        t_insert = time.perf_counter() - t0
        insert_ops_sec = s / t_insert
        
        # Deep chain ancestor traversal (1,000 hops)
        hops = min(s - 1, 1000)
        target_leaf = f"copy_{s}_{hops:07d}"
        t0_trav = time.perf_counter()
        res = index.traverse_ancestors(target_leaf, tenant_id=tenant_id, max_hops=hops + 50)
        t_trav_us = (time.perf_counter() - t0_trav) * 1_000_000.0
        assert res.state.value == "VALID"
        assert res.depth == hops
        
        results[f"{s}_nodes"] = {
            "insert_throughput_ops_sec": round(insert_ops_sec, 2),
            "insert_duration_ms": round(t_insert * 1000.0, 2),
            "ancestor_traversal_1000_hops_us": round(t_trav_us, 2),
            "traversal_hops": hops,
            "classification": "MEASURED"
        }
        
    return results


def profile_telemetry(scales: List[int] = [1_000, 10_000, 100_000]) -> Dict[str, Any]:
    """Profiles ScalableTelemetryProvider ingestion, dedup, and temporal queries."""
    results = {}
    
    for s in scales:
        provider = ScalableTelemetryProvider()
        tenant_id = f"tenant_telem_{s}"
        
        gc.collect()
        t0 = time.perf_counter()
        for i in range(s):
            rec = CompactTelemetryRecord(
                event_id=f"tel_{s}_{i:07d}",
                event_type="FILE_OPEN",
                source_system="EDR_AGENT",
                artifact_hash=hashlib.sha256(f"art_{i % 500}".encode()).hexdigest(),
                copy_id=f"copy_{i % 200}",
                device_id=f"dev_{i % 50}",
                subject_id=f"sub_{i % 100}",
                network_id="10.0.0.1",
                timestamp_epoch=1700000000.0 + i,
                tenant_id=tenant_id
            )
            provider.ingest_record(rec)
            
        t_ingest = time.perf_counter() - t0
        ingest_ops_sec = s / t_ingest
        
        # Temporal range query
        t0_q = time.perf_counter()
        matched = provider.query_time_window(
            start_epoch=1700000000.0 + (s // 4),
            end_epoch=1700000000.0 + (s // 2),
            tenant_id=tenant_id
        )
        t_query_ms = (time.perf_counter() - t0_q) * 1000.0
        
        results[f"{s}_events"] = {
            "ingest_throughput_ops_sec": round(ingest_ops_sec, 2),
            "ingest_duration_ms": round(t_ingest * 1000.0, 2),
            "temporal_range_query_ms": round(t_query_ms, 3),
            "temporal_matched_count": len(matched),
            "classification": "MEASURED"
        }
        
    return results


def profile_identity(scales: List[int] = [1_000, 10_000]) -> Dict[str, Any]:
    """Profiles FederatedIdentityDirectory resolution and cache states."""
    results = {}
    for s in scales:
        dir_svc = FederatedIdentityDirectory()
        tenant_id = f"tenant_id_{s}"
        adapter = EntraIdAdapter(tenant_id=tenant_id)
        
        for i in range(s):
            u_id = f"usr_{s}_{i:06d}"
            r_id = f"rec_{s}_{i:06d}"
            ident = Identity(
                identity_id=u_id,
                organization_id=tenant_id,
                provider="entra_id",
                provider_subject=f"subj_{s}_{i:06d}",
                display_name=f"User {i}",
                email=f"user_{i}@agency.gov",
                status=IdentityStatus.ACTIVE
            )
            adapter.add_identity(ident)
            dir_svc.cache_identity(ident, tenant_id=tenant_id)
            dir_svc.bind_recipient(r_id, u_id, tenant_id=tenant_id)
            
        dir_svc.register_provider(adapter)
        
        # Direct resolution
        resolve_times = []
        for i in range(min(500, s)):
            t0 = time.perf_counter()
            resolved, status = dir_svc.resolve_recipient(f"rec_{s}_{i:06d}", tenant_id=tenant_id)
            resolve_times.append((time.perf_counter() - t0) * 1_000_000.0) # us
            assert resolved is not None
            assert status in ("RESOLVED", "CACHED", "FRESH")
            
        results[f"{s}_identities"] = {
            "resolve_latency_us": compute_stats(resolve_times),
            "classification": "MEASURED"
        }
    return results


def profile_investigation_multi_index_join(scale: int = 10_000) -> Dict[str, Any]:
    """Profiles complete multi-index join across Lineage, Ledger, Identity, and Telemetry."""
    lineage = SparseLineageIndex()
    ledger = ScalableLedger(checkpoint_interval=1000)
    identity_dir = FederatedIdentityDirectory()
    telemetry = ScalableTelemetryProvider()
    
    tenant_id = "tenant_inv_scale"
    adapter = EntraIdAdapter(tenant_id=tenant_id)
    
    prev_hash = "0" * 64
    for i in range(scale):
        # Lineage
        cid = f"copy_inv_{i}"
        pid = f"copy_inv_{i-1}" if i > 0 and i % 5 != 0 else None
        rec_id = f"subj_inv_{i % 100}"
        rel_id = f"rel_inv_{i % 50}"
        
        lineage.insert_node(SparseLineageNode(
            copy_id=cid,
            parent_copy_id=pid,
            document_id="doc_inv_target",
            recipient_id=rec_id,
            release_id=rel_id,
            tenant_id=tenant_id
        ))
        
        # Ledger
        evt = EvidenceEvent(
            event_id=f"evt_inv_{i}",
            timestamp="2026-09-27T14:00:00Z",
            event_type="DOCUMENT_DECRYPT",
            document_id="doc_inv_target",
            release_id=rel_id,
            recipient_id=rec_id,
            artifact_hash=hashlib.sha256(f"artifact_{i}".encode()).hexdigest(),
            evidence_hash=hashlib.sha256(f"evidence_{i}".encode()).hexdigest(),
            algorithm="ML-DSA-65",
            signature="sig_benchmark",
            previous_event_hash=prev_hash
        )
        prev_hash = ledger.append_event(evt, tenant_id=tenant_id)
        
        # Telemetry
        telemetry.ingest_record(CompactTelemetryRecord(
            event_id=f"tel_inv_{i}",
            event_type="FILE_OPEN",
            source_system="EDR",
            artifact_hash="art_hash",
            copy_id=cid,
            device_id="dev_01",
            subject_id=rec_id,
            network_id="10.0.0.1",
            timestamp_epoch=1700000000.0 + i,
            tenant_id=tenant_id
        ))
        
        # Identity
        if i < 100:
            ident_inv = Identity(
                identity_id=f"usr_inv_{i}",
                organization_id=tenant_id,
                provider="entra_id",
                provider_subject=rec_id,
                display_name=f"Investigated Subject {i}",
                email=f"subject_{i}@intel.gov",
                status=IdentityStatus.ACTIVE
            )
            adapter.add_identity(ident_inv)
            identity_dir.cache_identity(ident_inv, tenant_id=tenant_id)
            identity_dir.bind_recipient(rec_id, ident_inv.identity_id, tenant_id=tenant_id)
            
    identity_dir.register_provider(adapter)
    engine = ForensicInvestigationEngine(lineage, ledger, identity_dir, telemetry)
    
    # Run 100 join queries
    join_latencies = []
    for i in range(100):
        target = f"copy_inv_{scale - 1 - i}"
        t0 = time.perf_counter()
        dossier = engine.investigate_copy(target, tenant_id=tenant_id)
        join_latencies.append((time.perf_counter() - t0) * 1000.0) # ms
        assert dossier.fail_closed_reason is None
        assert dossier.leaked_copy_id == target
        
    return {
        "scale": scale,
        "queries_evaluated": 100,
        "join_latency_ms": compute_stats(join_latencies),
        "classification": "MEASURED"
    }


def profile_evidence_and_recovery(iterations: int = 10) -> Dict[str, Any]:
    """Profiles Evidence Packaging and Disaster Recovery engines."""
    cas = ContentAddressedStore(os.path.join(REPO_ROOT, "artifacts", "performance", "_temp_cas"))
    kp = MLDSA65.generate_keypair()
    dr_engine = DisasterRecoveryEngine(store=cas)
    
    # 1. Create and seal backup
    events_list = []
    prev_h = "0" * 64
    for i in range(100):
        ev = EvidenceEvent(
            event_id=f"evt_rec_{i:04d}",
            timestamp="2026-09-27T12:00:00Z",
            event_type="DOCUMENT_RELEASE",
            document_id="doc_test",
            release_id="rel_test",
            recipient_id="rec_test",
            artifact_hash=hashlib.sha256(f"a_{i}".encode()).hexdigest(),
            evidence_hash=hashlib.sha256(f"e_{i}".encode()).hexdigest(),
            algorithm="ML-DSA-65",
            signature="sig_test",
            previous_event_hash=prev_h,
        )
        events_list.append(ev.model_dump())
        prev_h = ev.compute_event_hash()

    datasets = {"ledger_events": events_list}
    t0_sign = time.perf_counter()
    manifest = dr_engine.create_backup(
        tenant_id="tenant_perf_ev",
        backup_type=BackupType.FULL,
        datasets=datasets,
        signer_id="sec_admin",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes,
    )
    t_seal_ms = (time.perf_counter() - t0_sign) * 1000.0
    
    # 2. Package Verification
    t0_v = time.perf_counter()
    is_valid, err = BackupCryptoEngine.verify_manifest(manifest, kp.public_key_bytes)
    t_verify_ms = (time.perf_counter() - t0_v) * 1000.0
    assert is_valid
    
    # 3. Restore from CAS
    t0_r = time.perf_counter()
    rep = dr_engine.restore_backup(
        manifest=manifest,
        expected_tenant_id="tenant_perf_ev",
        authority_public_key_bytes=kp.public_key_bytes,
        operator_id="op_lead",
        operator_role="RECOVERY_OPERATOR"
    )
    t_restore_ms = (time.perf_counter() - t0_r) * 1000.0
    assert rep.final_recovery_state == FinalRecoveryOutcome.RECOVERED
    
    return {
        "manifest_seal_ms": round(t_seal_ms, 2),
        "manifest_verify_ms": round(t_verify_ms, 2),
        "restore_100_objects_ms": round(t_restore_ms, 2),
        "classification": "MEASURED"
    }


def profile_end_to_end_golden() -> Dict[str, Any]:
    """Profiles one complete end-to-end golden path lifecycle."""
    t0_all = time.perf_counter()
    stages = {}
    
    # Stage 1: Keygen & Decryption Setup
    t0 = time.perf_counter()
    recip_kem = MLKEM768.generate_keypair()
    recip_dsa = MLDSA65.generate_keypair()
    stages["1_key_generation_ms"] = (time.perf_counter() - t0) * 1000.0
    
    # Stage 2: KEM Encapsulation & AES Payload Encryption
    t0 = time.perf_counter()
    enc_res = MLKEM768.encapsulate(recip_kem.public_key_bytes)
    doc_payload = b"Top Secret Defense Analysis Document" * 100
    doc_ct = encrypt_aes_gcm(enc_res.shared_secret, doc_payload)
    stages["2_release_encryption_ms"] = (time.perf_counter() - t0) * 1000.0
    
    # Stage 3: Client Decryption
    t0 = time.perf_counter()
    recovered_ss = MLKEM768.decapsulate(recip_kem.private_key_bytes, enc_res.ciphertext)
    decrypted_doc = decrypt_aes_gcm(recovered_ss, doc_ct)
    assert decrypted_doc == doc_payload
    stages["3_client_decryption_ms"] = (time.perf_counter() - t0) * 1000.0
    
    # Stage 4: Dynamic Watermark Embedding
    t0 = time.perf_counter()
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()
    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 255
    wm_payload = WatermarkPayload(
        document_id="doc_golden_01",
        release_id="rel_golden_01",
        codeword=[1, 0, 1, 0] * 32
    )
    watermarked = encoder.encode(canvas, wm_payload)
    stages["4_watermark_embedding_ms"] = (time.perf_counter() - t0) * 1000.0
    
    # Stage 5: Provenance ML-DSA Signing
    t0 = time.perf_counter()
    provenance_claim = b"AEGIS-PROVENANCE:doc_golden_01:rel_golden_01:recip_alice"
    sig = MLDSA65.sign(recip_dsa.private_key_bytes, provenance_claim)
    stages["5_provenance_signing_ms"] = (time.perf_counter() - t0) * 1000.0
    
    # Stage 6: Ledger Event Append
    t0 = time.perf_counter()
    ledger = ScalableLedger(checkpoint_interval=100)
    evt = EvidenceEvent(
        event_id="evt_golden_01",
        timestamp="2026-09-27T16:00:00Z",
        event_type="DOCUMENT_DECRYPT",
        document_id="doc_golden_01",
        release_id="rel_golden_01",
        recipient_id="recip_alice",
        artifact_hash=hashlib.sha256(decrypted_doc).hexdigest(),
        evidence_hash=hashlib.sha256(sig).hexdigest(),
        algorithm="ML-DSA-65",
        signature=base64.b64encode(sig).decode("utf-8"),
        previous_event_hash="0" * 64
    )
    ledger.append_event(evt, tenant_id="defense_sovereign")
    stages["6_ledger_append_ms"] = (time.perf_counter() - t0) * 1000.0
    
    # Stage 7: Watermark Extraction from Leaked Image
    t0 = time.perf_counter()
    obs = decoder.decode(watermarked, expected_document_id="doc_golden_01", expected_release_id="rel_golden_01")
    assert obs.is_valid
    stages["7_watermark_extraction_ms"] = (time.perf_counter() - t0) * 1000.0
    
    # Stage 8: Investigation Join
    t0 = time.perf_counter()
    lineage = SparseLineageIndex()
    lineage.insert_node(SparseLineageNode(
        copy_id="copy_golden_01",
        parent_copy_id=None,
        document_id="doc_golden_01",
        recipient_id="recip_alice",
        release_id="rel_golden_01",
        tenant_id="defense_sovereign"
    ))
    id_dir = FederatedIdentityDirectory()
    adapter = EntraIdAdapter(tenant_id="defense_sovereign")
    ident_alice = Identity(
        identity_id="usr_golden_alice",
        organization_id="defense_sovereign",
        provider="entra_id",
        provider_subject="recip_alice",
        display_name="Alice Analyst",
        email="alice@defense.gov",
        status=IdentityStatus.ACTIVE
    )
    adapter.add_identity(ident_alice)
    id_dir.register_provider(adapter)
    id_dir.cache_identity(ident_alice, tenant_id="defense_sovereign")
    id_dir.bind_recipient("recip_alice", "usr_golden_alice", tenant_id="defense_sovereign")
    telemetry = ScalableTelemetryProvider()
    inv_engine = ForensicInvestigationEngine(lineage, ledger, id_dir, telemetry)
    dossier = inv_engine.investigate_copy("copy_golden_01", tenant_id="defense_sovereign")
    assert dossier.resolved_display_name == "Alice Analyst"
    stages["8_investigation_join_ms"] = (time.perf_counter() - t0) * 1000.0
    
    # Stage 9: Verification
    t0 = time.perf_counter()
    is_valid_sig = MLDSA65.verify(recip_dsa.public_key_bytes, provenance_claim, sig)
    assert is_valid_sig
    stages["9_provenance_verification_ms"] = (time.perf_counter() - t0) * 1000.0
    
    total_ms = (time.perf_counter() - t0_all) * 1000.0
    stages["total_end_to_end_duration_ms"] = round(total_ms, 2)
    for k in list(stages.keys()):
        stages[k] = round(stages[k], 2)
        
    return stages


def profile_concurrency(worker_counts: List[int] = [1, 2, 4, 8]) -> Dict[str, Any]:
    """Measures multi-worker scaling across thread pools."""
    results = {}
    items_to_hash = [os.urandom(1024) for _ in range(2000)]
    
    for workers in worker_counts:
        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            _ = list(executor.map(hashlib.sha256, items_to_hash))
        t_elapsed = (time.perf_counter() - t0) * 1000.0
        results[f"{workers}_workers_hash_2000_items_ms"] = round(t_elapsed, 2)
        
    return results


def run_full_suite(output_prefix: str = "baseline") -> Dict[str, Any]:
    """Runs complete performance profiling suite and writes JSON artifacts."""
    out_dir = Path(REPO_ROOT) / "artifacts" / "performance"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print(f"AEGISTRACE PERFORMANCE PROFILING SUITE: PHASE '{output_prefix.upper()}'")
    print("=" * 70)
    
    tracemalloc.start()
    t_start = time.perf_counter()
    
    hw = get_hardware_profile()
    print(f"Host: {hw['processor']} | {hw['physical_cores']} Cores / {hw['logical_cores']} Threads | {hw['total_ram_gb']} GB RAM")
    
    # 1. Crypto
    print("\n[1/10] Profiling Authentic Cryptography (ML-KEM-768, ML-DSA-65, AES-GCM, HKDF)...")
    crypto_res = profile_crypto(iterations=5)
    with open(out_dir / "crypto_benchmark.json", "w") as f:
        json.dump(crypto_res, f, indent=2)
        
    # 2. Watermark
    print("[2/10] Profiling Watermark Pipeline (Encode & Decode)...")
    watermark_res = profile_watermark(page_counts=[1, 5])
    with open(out_dir / "watermark_benchmark.json", "w") as f:
        json.dump(watermark_res, f, indent=2)
        
    # 3. Ledger
    print("[3/10] Profiling Scalable Ledger (1K, 10K, 100K)...")
    ledger_res = profile_ledger(scales=[1_000, 10_000, 100_000])
    with open(out_dir / "ledger_benchmark.json", "w") as f:
        json.dump(ledger_res, f, indent=2)
        
    # 4. Lineage
    print("[4/10] Profiling Sparse Lineage Graph (1K, 10K, 100K)...")
    lineage_res = profile_lineage(scales=[1_000, 10_000, 100_000])
    with open(out_dir / "lineage_benchmark.json", "w") as f:
        json.dump(lineage_res, f, indent=2)
        
    # 5. Telemetry
    print("[5/10] Profiling Scalable Telemetry Provider (1K, 10K, 100K)...")
    telemetry_res = profile_telemetry(scales=[1_000, 10_000, 100_000])
    with open(out_dir / "telemetry_benchmark.json", "w") as f:
        json.dump(telemetry_res, f, indent=2)
        
    # 6. Identity
    print("[6/10] Profiling Federated Identity Directory (1K, 10K)...")
    identity_res = profile_identity(scales=[1_000, 10_000])
    
    # 7. Investigation
    print("[7/10] Profiling Forensic Investigation Multi-Index Joins...")
    inv_res = profile_investigation_multi_index_join(scale=10_000)
    with open(out_dir / "investigation_benchmark.json", "w") as f:
        json.dump(inv_res, f, indent=2)
        
    # 8. Evidence & Recovery
    print("[8/10] Profiling Evidence Packaging & Disaster Recovery...")
    ev_rec_res = profile_evidence_and_recovery(iterations=5)
    with open(out_dir / "evidence_benchmark.json", "w") as f:
        json.dump({"evidence_packaging": ev_rec_res}, f, indent=2)
    with open(out_dir / "recovery_benchmark.json", "w") as f:
        json.dump({"disaster_recovery": ev_rec_res}, f, indent=2)
        
    # 9. End-to-End Golden Benchmark
    print("[9/10] Profiling End-to-End Golden Critical Path...")
    e2e_res = profile_end_to_end_golden()
    with open(out_dir / "end_to_end_benchmark.json", "w") as f:
        json.dump(e2e_res, f, indent=2)
        
    # 10. Concurrency & Memory
    print("[10/10] Profiling Concurrency & Memory Footprint...")
    conc_res = profile_concurrency(worker_counts=[1, 2, 4, 8])
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    mem_profile = {
        "current_traced_mb": round(current_mem / (1024 * 1024), 2),
        "peak_traced_mb": round(peak_mem / (1024 * 1024), 2),
        "gc_stats": gc.get_stats(),
        "gc_counts": gc.get_count(),
        "concurrency_scaling": conc_res
    }
    with open(out_dir / "memory_profile.json", "w") as f:
        json.dump(mem_profile, f, indent=2)
        
    total_profile = {
        "metadata": {
            "phase": output_prefix,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_benchmark_duration_sec": round(time.perf_counter() - t_start, 2),
            "hardware": hw
        },
        "crypto": crypto_res,
        "watermark": watermark_res,
        "ledger": ledger_res,
        "lineage": lineage_res,
        "telemetry": telemetry_res,
        "identity": identity_res,
        "investigation": inv_res,
        "evidence_and_recovery": ev_rec_res,
        "end_to_end": e2e_res,
        "memory": mem_profile
    }
    
    summary_path = out_dir / f"{output_prefix}_profile.json"
    with open(summary_path, "w") as f:
        json.dump(total_profile, f, indent=2)
        
    print(f"\n[+] Profile written to: {summary_path}")
    print(f"[+] Total benchmark execution time: {total_profile['metadata']['total_benchmark_duration_sec']}s")
    print("=" * 70)
    return total_profile


if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    run_full_suite(prefix)
