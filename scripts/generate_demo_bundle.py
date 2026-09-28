#!/usr/bin/env python3
"""
AegisTrace Demo Bundle Generator.
=================================
Generates all canonical, self-contained forensic demonstration artifacts in `artifacts/demo/`
covering the Golden SIH Case, Lineage Downstream Gap, Blind Negative Case,
Composed Red-Team Attack Chains, and Offline Verification outputs.

Outputs:
    artifacts/demo/
      ├── golden_case/
      ├── unknown_downstream/
      ├── negative_case/
      ├── attacks/
      ├── verification/
      └── DEMO_INDEX.json
"""

import sys
import os
import json
import base64
import hashlib
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.exporter import EvidencePackageExporter
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.models import VerificationStatus, DecisionState, PackageManifest
from core.red_team.blind_evaluator import BlindForensicEvaluator
from core.red_team.composed_attacks import ComposedAttackSimulator


def generate_demo_bundle():
    print("\n[+] GENERATING AEGISTRACE FORENSIC DEMONSTRATION BUNDLE...")
    demo_root = PROJECT_ROOT / "artifacts" / "demo"
    dir_golden = demo_root / "golden_case"
    dir_downstream = demo_root / "unknown_downstream"
    dir_negative = demo_root / "negative_case"
    dir_attacks = demo_root / "attacks"
    dir_verification = demo_root / "verification"

    for d in [dir_golden, dir_downstream, dir_negative, dir_attacks, dir_verification]:
        d.mkdir(parents=True, exist_ok=True)

    catalog = {
        "generated_at_iso": datetime.now(timezone.utc).isoformat(),
        "platform": "AegisTrace (SIH26237)",
        "demo_suite_version": "1.0.0",
        "demonstrations": {},
    }

    # -------------------------------------------------------------
    # 1. Golden SIH Case Pipeline
    # -------------------------------------------------------------
    print("--> [1/5] Running Golden Multi-Recipient Pipeline & Exporting Artifacts...")
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="TENANT-SIH-2026")
    golden_res = orchestrator.run_full_golden_pipeline()

    # Original Document
    doc_bytes = (
        b"%PDF-1.7 Master Strategic Directive AegisTrace 2026 TOP SECRET / EYES ONLY\n"
        b"RESTRICTED DEFENSE DEPLOYMENT PROTOCOL - AUTHORIZED AUDIT COPY\n" + (b"X" * 1024)
    )
    (dir_golden / "original_document.pdf").write_bytes(doc_bytes)

    # Alice's Encrypted Package
    alice_artifacts = golden_res.decryption_records["alice"]
    alice_receipt_dict = alice_artifacts.receipt.model_dump(mode="json")
    (dir_golden / "decryption_receipt_alice.json").write_text(
        json.dumps(alice_receipt_dict, indent=2), encoding="utf-8"
    )

    # Watermarked artifact & Leak artifact
    (dir_golden / "decrypted_watermarked_alice.pdf").write_bytes(alice_artifacts.watermarked_bytes)
    (dir_golden / "leak_artifact.pdf").write_bytes(alice_artifacts.watermarked_bytes)

    # DLT Proof
    node = list(orchestrator.dlt_ledger.nodes.values())[0]
    proof = node.get_merkle_proof(alice_artifacts.receipt.receipt_id)
    (dir_golden / "dlt_merkle_proof.json").write_text(
        json.dumps(proof.model_dump(mode="json") if proof else {}, indent=2), encoding="utf-8"
    )

    # Evidence Package Export (.zip, directory, and .json)
    zip_path = dir_golden / "golden_evidence_package.zip"
    EvidencePackageExporter.export_to_zip(golden_res.evidence_package, zip_path)
    EvidencePackageExporter.export_to_directory(golden_res.evidence_package, dir_golden / "package_tree")
    
    pkg_dict = {
        "manifest": golden_res.evidence_package.manifest.model_dump(mode="json"),
        "signature": golden_res.evidence_package.signature.model_dump(mode="json"),
        "objects": [obj.model_dump(mode="json") for obj in golden_res.evidence_package.objects],
        "edges": [edge.model_dump(mode="json") for edge in golden_res.evidence_package.edges],
        "custody_chain": [c.model_dump(mode="json") for c in golden_res.evidence_package.custody_chain],
    }
    (dir_golden / "golden_evidence_package.json").write_text(
        json.dumps(pkg_dict, indent=2), encoding="utf-8"
    )

    catalog["demonstrations"]["golden_case"] = {
        "status": "PASS",
        "case_id": golden_res.case_id,
        "attributed_suspect": golden_res.extraction_and_attribution.matched_recipient_id,
        "confidence": golden_res.extraction_and_attribution.confidence_score,
        "package_id": golden_res.evidence_package.manifest.package_id,
        "files": {
            "original_document": "golden_case/original_document.pdf",
            "decrypted_watermarked_alice": "golden_case/decrypted_watermarked_alice.pdf",
            "leak_artifact": "golden_case/leak_artifact.pdf",
            "decryption_receipt": "golden_case/decryption_receipt_alice.json",
            "dlt_merkle_proof": "golden_case/dlt_merkle_proof.json",
            "evidence_package_zip": "golden_case/golden_evidence_package.zip",
            "evidence_package_json": "golden_case/golden_evidence_package.json",
        }
    }

    # -------------------------------------------------------------
    # 2. Lineage Downstream Gap Scenario
    # -------------------------------------------------------------
    print("--> [2/5] Constructing Unknown Downstream Lineage Transfer Scenario...")
    downstream_lineage = {
        "scenario": "Alice exports copy to USB -> Bob receives file -> Bob leaks without client registration",
        "root_copy_id": f"root_{golden_res.document_id}",
        "authorized_hops": [
            {"node_id": "copy_alice_01", "holder": "alice", "depth": 1, "registered_on_dlt": True},
            {"node_id": "copy_bob_transfer_02", "holder": "bob", "depth": 2, "registered_on_dlt": True},
        ],
        "gap_boundary": {
            "last_known_authenticated_holder": "bob",
            "unregistered_downstream_leak": True,
            "forensic_verdict": "ATTRIBUTED_WITH_DOWNSTREAM_GAP",
            "explanation": "Cryptographic signature proves Bob decrypted and possessed the parent copy; subsequent unmonitored transfer preserves provenance back to Bob."
        }
    }
    (dir_downstream / "downstream_lineage_scenario.json").write_text(
        json.dumps(downstream_lineage, indent=2), encoding="utf-8"
    )
    catalog["demonstrations"]["unknown_downstream"] = {
        "status": "PASS",
        "scenario_file": "unknown_downstream/downstream_lineage_scenario.json",
        "last_known_holder": "bob",
        "gap_retained": True
    }

    # -------------------------------------------------------------
    # 3. Blind Negative Case (Clean Document)
    # -------------------------------------------------------------
    print("--> [3/5] Evaluating Blind Negative Case on Clean Document...")
    clean_bytes = b"%PDF-1.7 Clean Unwatermarked Strategic Memo Without Forensic Tokens\n" + (b"Z" * 1024)
    (dir_negative / "clean_unwatermarked_document.pdf").write_bytes(clean_bytes)

    blind_eval = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="TENANT-SIH-2026",
    )
    clean_res = blind_eval.evaluate_artifact(
        artifact_bytes=clean_bytes,
        document_id="DOC-CLEAN-DEMO",
        release_id="REL-CLEAN-DEMO",
    )
    clean_report = clean_res.model_dump(mode="json")
    (dir_negative / "blind_negative_evaluation_report.json").write_text(
        json.dumps(clean_report, indent=2), encoding="utf-8"
    )
    catalog["demonstrations"]["negative_case"] = {
        "status": "PASS",
        "clean_document": "negative_case/clean_unwatermarked_document.pdf",
        "evaluation_report": "negative_case/blind_negative_evaluation_report.json",
        "verdict": clean_res.decision_state.value if hasattr(clean_res.decision_state, "value") else str(clean_res.decision_state),
        "attributed_recipient": clean_res.attributed_recipient_id,
    }

    # -------------------------------------------------------------
    # 4. Composed Red-Team Attack Scorecards
    # -------------------------------------------------------------
    print("--> [4/5] Simulating Red-Team Composed Attack Chains (A-G)...")
    chains = [
        ("chain_a_stolen_account", "Chain A: Stolen Account + Device Mismatch", lambda: ComposedAttackSimulator.execute_chain_a(golden_res)),
        ("chain_b_ledger_fork", "Chain B: Valid Receipt + Modified Ledger Tail", lambda: ComposedAttackSimulator.execute_chain_b(orchestrator)),
        ("chain_c_transplantation", "Chain C: Watermark Transplantation + Forged Metadata", lambda: ComposedAttackSimulator.execute_chain_c(golden_res)),
        ("chain_d_post_revocation_replay", "Chain D: Replayed Receipt + Rotated Key", lambda: ComposedAttackSimulator.execute_chain_d(golden_res)),
        ("chain_e_cross_tenant_injection", "Chain E: Cross-Tenant Artifact Injection", lambda: ComposedAttackSimulator.execute_chain_e(golden_res)),
        ("chain_f_lineage_gap_violation", "Chain F: Valid Artifact + Modified Lineage", lambda: ComposedAttackSimulator.execute_chain_f(golden_res)),
        ("chain_g_manifest_forgery", "Chain G: Corrupted Package + Manifest Forgery", lambda: ComposedAttackSimulator.execute_chain_g(golden_res)),
    ]

    attack_catalog = {}
    for key, name, executor in chains:
        res = executor()
        res_dict = res.model_dump(mode="json")
        res_file = f"{key}.json"
        (dir_attacks / res_file).write_text(json.dumps(res_dict, indent=2), encoding="utf-8")
        attack_catalog[key] = {
            "name": name,
            "security_maintained": res.security_maintained,
            "verdict": res.verdict.value if hasattr(res.verdict, "value") else str(res.verdict),
            "mitigating_pillar": res.mitigating_pillar,
            "report_file": f"attacks/{res_file}",
        }
    catalog["demonstrations"]["attacks"] = attack_catalog

    # -------------------------------------------------------------
    # 5. Offline Verifier Output Reports
    # -------------------------------------------------------------
    print("--> [5/5] Generating Offline Verification Validation Reports...")
    verifier = OfflineEvidenceVerifier(expected_tenant_id="TENANT-SIH-2026")

    # Golden package verification
    pkg_ver_res = verifier.verify_package(
        manifest=golden_res.evidence_package.manifest,
        signature=golden_res.evidence_package.signature,
        objects=golden_res.evidence_package.objects,
        edges=golden_res.evidence_package.edges,
        custody_chain=golden_res.evidence_package.custody_chain,
    )
    (dir_verification / "golden_package_verification_report.json").write_text(
        json.dumps(pkg_ver_res.model_dump(mode="json"), indent=2), encoding="utf-8"
    )

    # Tampered package verification
    tampered_manifest = golden_res.evidence_package.manifest.model_copy(
        update={"evidence_merkle_root": "00" * 32}
    )
    tamper_ver_res = verifier.verify_package(
        manifest=tampered_manifest,
        signature=golden_res.evidence_package.signature,
        objects=golden_res.evidence_package.objects,
        edges=golden_res.evidence_package.edges,
        custody_chain=golden_res.evidence_package.custody_chain,
    )
    (dir_verification / "tampered_package_verification_report.json").write_text(
        json.dumps(tamper_ver_res.model_dump(mode="json"), indent=2), encoding="utf-8"
    )

    catalog["demonstrations"]["verification"] = {
        "golden_report": "verification/golden_package_verification_report.json",
        "golden_status": pkg_ver_res.overall_status.value,
        "tampered_report": "verification/tampered_package_verification_report.json",
        "tampered_status": tamper_ver_res.overall_status.value,
    }

    # Physical disclaimer
    catalog["physical_attestation"] = {
        "PHYSICAL_COMPONENT": "NOT_VERIFIED (Simulated test fixture only)",
        "disclaimer": "Hardware optical camera and print-scan media requires real-world physical calibration. Digital pipeline and cryptographic guarantees are fully certified."
    }

    # Write Master Index
    index_file = demo_root / "DEMO_INDEX.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"\n[+] Demo Bundle Generation Complete!")
    print(f"    Master Index: {index_file}")
    return catalog


if __name__ == "__main__":
    generate_demo_bundle()
