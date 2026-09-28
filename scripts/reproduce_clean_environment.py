#!/usr/bin/env python3
"""
AegisTrace Clean-Room Independent Reproduction Runner.
======================================================
Executes a fully automated, standalone reproduction sequence from scratch.
Verifies source tree integrity, cryptographic algorithms, end-to-end golden pipeline,
blind attribution, and all composed red-team attack chains.

Usage:
    python scripts/reproduce_clean_environment.py [--json]
"""

import sys
import os
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.deployment.startup_self_test import StartupSelfTestRunner
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.models import VerificationStatus, DecisionState
from core.red_team.blind_evaluator import BlindForensicEvaluator
from core.red_team.composed_attacks import ComposedAttackSimulator
from core.red_team.privileged_operator import PrivilegedOperatorAttackSimulator


def verify_source_manifest() -> dict:
    """Verify source files against source_manifest.json."""
    manifest_path = PROJECT_ROOT / "artifacts" / "reproduction" / "source_manifest.json"
    if not manifest_path.exists():
        from scripts.generate_source_manifest import generate_manifest
        generate_manifest()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    files_checked = 0
    mismatches = []

    for rel_path, meta in manifest.get("files", {}).items():
        file_path = PROJECT_ROOT / rel_path
        if not file_path.exists():
            mismatches.append(f"Missing file: {rel_path}")
            continue

        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_sha = hasher.hexdigest()

        if actual_sha != meta["sha256"]:
            mismatches.append(f"Hash mismatch for {rel_path}")
        files_checked += 1

    return {
        "status": "PASS" if not mismatches else "FAIL",
        "files_checked": files_checked,
        "mismatches": mismatches,
    }


def run_reproduction_suite() -> dict:
    """Run all independent reproduction checks and return comprehensive report."""
    start_time = time.perf_counter()
    report = {
        "reproduction_timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "platform": "AegisTrace (SIH26237)",
        "python_runtime": f"{sys.version.split()[0]} ({sys.platform})",
        "stages": {},
        "overall_status": "PASS",
    }

    all_passed = True

    # -------------------------------------------------------------
    # Stage 1: Source Tree Integrity
    # -------------------------------------------------------------
    print("\n--> [Stage 1/6] Auditing Canonical Source Tree Integrity...")
    t0 = time.perf_counter()
    manifest_result = verify_source_manifest()
    dt1 = (time.perf_counter() - t0) * 1000
    report["stages"]["1_source_tree_integrity"] = {
        "status": manifest_result["status"],
        "duration_ms": round(dt1, 2),
        "files_verified": manifest_result["files_checked"],
        "mismatches": manifest_result["mismatches"],
    }
    if manifest_result["status"] != "PASS":
        all_passed = False

    # -------------------------------------------------------------
    # Stage 2: Startup Self-Tests
    # -------------------------------------------------------------
    print("--> [Stage 2/6] Executing Cryptographic & Runtime Self-Tests...")
    t0 = time.perf_counter()
    runner = StartupSelfTestRunner(repo_root=PROJECT_ROOT)
    st_report = runner.run_all(fail_closed=False)
    dt2 = (time.perf_counter() - t0) * 1000
    st_pass = st_report.get("overall_status") == "PASS"
    report["stages"]["2_startup_self_tests"] = {
        "status": "PASS" if st_pass else "FAIL",
        "duration_ms": round(dt2, 2),
        "checks_run": len(st_report.get("checks", {})),
        "details": {k: v.get("status") for k, v in st_report.get("checks", {}).items()},
    }
    if not st_pass:
        all_passed = False

    # -------------------------------------------------------------
    # Stage 3: End-to-End Golden Pipeline Execution
    # -------------------------------------------------------------
    print("--> [Stage 3/6] Executing 24-Step Multi-Recipient Golden Pipeline...")
    t0 = time.perf_counter()
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="TENANT-REPRODUCTION-2026")
    golden_res = orchestrator.run_full_golden_pipeline()
    dt3 = (time.perf_counter() - t0) * 1000
    attrib = golden_res.extraction_and_attribution
    pipe_pass = (
        attrib.decision_state == DecisionState.ATTRIBUTED
        and attrib.matched_recipient_id == "alice"
        and golden_res.verification_result.overall_status == VerificationStatus.VERIFIED
    )
    report["stages"]["3_golden_pipeline"] = {
        "status": "PASS" if pipe_pass else "FAIL",
        "duration_ms": round(dt3, 2),
        "case_id": golden_res.case_id,
        "attributed_recipient": attrib.matched_recipient_id,
        "decision_state": attrib.decision_state.value if hasattr(attrib.decision_state, "value") else str(attrib.decision_state),
        "confidence_score": attrib.confidence_score,
        "dlt_receipt_verified": attrib.is_signature_valid and attrib.is_ledger_proof_valid,
        "merkle_root": golden_res.evidence_package.manifest.evidence_merkle_root,
    }
    if not pipe_pass:
        all_passed = False

    # -------------------------------------------------------------
    # Stage 4: Independent Offline Evidence Package Verification
    # -------------------------------------------------------------
    print("--> [Stage 4/6] Verifying Offline Evidence Package Invariants...")
    t0 = time.perf_counter()
    verifier = OfflineEvidenceVerifier(expected_tenant_id="TENANT-REPRODUCTION-2026")
    pkg_res = verifier.verify_package(
        manifest=golden_res.evidence_package.manifest,
        signature=golden_res.evidence_package.signature,
        objects=golden_res.evidence_package.objects,
        edges=golden_res.evidence_package.edges,
        custody_chain=golden_res.evidence_package.custody_chain,
    )
    dt4 = (time.perf_counter() - t0) * 1000
    pkg_pass = pkg_res.overall_status == VerificationStatus.VERIFIED
    report["stages"]["4_offline_verification"] = {
        "status": "PASS" if pkg_pass else "FAIL",
        "duration_ms": round(dt4, 2),
        "package_id": pkg_res.package_id,
        "overall_status": pkg_res.overall_status.value,
        "manifest_signature_valid": pkg_res.manifest_signature_valid,
        "merkle_root_valid": pkg_res.merkle_root_valid,
        "object_hashes_valid": pkg_res.object_hashes_valid,
        "dependency_graph_valid": pkg_res.dependency_graph_valid,
        "recipient_signature_valid": pkg_res.recipient_signature_valid,
        "ledger_proof_valid": pkg_res.ledger_proof_valid,
        "custody_chain_valid": pkg_res.custody_chain_valid,
        "decision_consistent": pkg_res.decision_consistent,
    }
    if not pkg_pass:
        all_passed = False

    # -------------------------------------------------------------
    # Stage 5: Blind Negative Case & Signal Separation
    # -------------------------------------------------------------
    print("--> [Stage 5/6] Executing Blind Signal Separation & Negative Testing...")
    t0 = time.perf_counter()
    blind_eval = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="TENANT-REPRODUCTION-2026",
    )
    # Clean doc test
    clean_bytes = b"UNWATERMARKED_SECRET_DOCUMENT_REPRODUCTION_NEGATIVE_FIXTURE_2026"
    clean_res = blind_eval.evaluate_artifact(
        artifact_bytes=clean_bytes,
        document_id="DOC-REPRO-CLEAN",
        release_id="REL-REPRO-CLEAN",
    )
    clean_pass = (
        clean_res.decision_state in (DecisionState.NO_SIGNAL, DecisionState.ABSTAINED)
        and clean_res.attributed_recipient_id is None
    )

    # Bob's artifact blind evaluation (should attribute to Bob, not Alice)
    bob_artifacts = golden_res.decryption_records["bob"]
    bob_res = blind_eval.evaluate_artifact(
        artifact_bytes=bob_artifacts.watermarked_bytes,
        document_id=golden_res.document_id,
        release_id=golden_res.release_id,
    )
    bob_pass = (
        bob_res.decision_state == DecisionState.ATTRIBUTED
        and bob_res.attributed_recipient_id == "bob"
    )

    dt5 = (time.perf_counter() - t0) * 1000
    blind_pass = clean_pass and bob_pass
    report["stages"]["5_blind_evaluation"] = {
        "status": "PASS" if blind_pass else "FAIL",
        "duration_ms": round(dt5, 2),
        "clean_doc_decision": clean_res.decision_state.value if hasattr(clean_res.decision_state, "value") else str(clean_res.decision_state),
        "clean_doc_attributed": clean_res.attributed_recipient_id,
        "bob_blind_decision": bob_res.decision_state.value if hasattr(bob_res.decision_state, "value") else str(bob_res.decision_state),
        "bob_blind_attributed": bob_res.attributed_recipient_id,
    }
    if not blind_pass:
        all_passed = False

    # -------------------------------------------------------------
    # Stage 6: Composed Attack Chains A through G
    # -------------------------------------------------------------
    print("--> [Stage 6/6] Running Composed Red-Team Attack Chains (A-G)...")
    t0 = time.perf_counter()
    attack_results = {}
    attacks_blocked = True

    chains = [
        ("chain_a_stolen_account", lambda: ComposedAttackSimulator.execute_chain_a(golden_res)),
        ("chain_b_ledger_fork", lambda: ComposedAttackSimulator.execute_chain_b(orchestrator)),
        ("chain_c_transplantation", lambda: ComposedAttackSimulator.execute_chain_c(golden_res)),
        ("chain_d_post_revocation_replay", lambda: ComposedAttackSimulator.execute_chain_d(golden_res)),
        ("chain_e_cross_tenant_injection", lambda: ComposedAttackSimulator.execute_chain_e(golden_res)),
        ("chain_f_lineage_gap_violation", lambda: ComposedAttackSimulator.execute_chain_f(golden_res)),
        ("chain_g_manifest_forgery", lambda: ComposedAttackSimulator.execute_chain_g(golden_res)),
    ]

    for chain_key, executor in chains:
        res = executor()
        attack_results[chain_key] = {
            "security_maintained": res.security_maintained,
            "verdict": res.verdict.value if hasattr(res.verdict, "value") else str(res.verdict),
            "mitigating_pillar": res.mitigating_pillar,
            "errors": res.evidence_errors,
        }
        if not res.security_maintained:
            attacks_blocked = False

    dt6 = (time.perf_counter() - t0) * 1000
    report["stages"]["6_composed_attack_chains"] = {
        "status": "PASS" if attacks_blocked else "FAIL",
        "duration_ms": round(dt6, 2),
        "total_chains_tested": len(chains),
        "chains_neutralized": sum(1 for c in attack_results.values() if c["security_maintained"]),
        "chains": attack_results,
    }
    if not attacks_blocked:
        all_passed = False

    total_duration_s = time.perf_counter() - start_time
    report["overall_status"] = "PASS" if all_passed else "FAIL"
    report["total_duration_seconds"] = round(total_duration_s, 3)

    # Save to disk
    out_dir = PROJECT_ROOT / "artifacts" / "reproduction"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "reproduction_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def main():
    print("=" * 75)
    print("  AEGISTRACE CLEAN-ROOM INDEPENDENT REPRODUCTION RUNNER")
    print("  Smart India Hackathon 2026 — Zero-Trust PQC Forensic Platform")
    print("=" * 75)

    report = run_reproduction_suite()

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
        return 0 if report["overall_status"] == "PASS" else 1

    print("\n" + "=" * 75)
    print("  INDEPENDENT REPRODUCTION EXECUTION SCORECARD")
    print("=" * 75)
    for stage_name, stage_data in report["stages"].items():
        st = stage_data.get("status", "UNKNOWN")
        dur = stage_data.get("duration_ms", 0.0)
        st_color = f"[\033[92mPASS\033[0m]" if st == "PASS" else f"[\033[91m{st}\033[0m]"
        title = stage_name.replace("_", " ").title()
        print(f"  {st_color} {title:<42} ({dur:>7.1f} ms)")

    print("-" * 75)
    print(f"  Overall Reproduction Status: {report['overall_status']}")
    print(f"  Total Execution Time:        {report['total_duration_seconds']:.2f} seconds")
    print(f"  Physical Attestation:        NOT_VERIFIED (Simulated optical test fixture)")
    print(f"  Reproduction Report Path:    artifacts/reproduction/reproduction_report.json")
    print("=" * 75 + "\n")

    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
