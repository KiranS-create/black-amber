"""
Test Suite: Controlled Tamper Attack & Fail-Closed Verifier Rejection.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber
"""

import json
import pytest
from pathlib import Path
from core.demo.golden_case import GoldenDemoEngine
from core.evidence_package.models import VerificationStatus


def test_tamper_attack_fail_closed(tmp_path):
    """
    Assert that the OfflineEvidenceVerifier strictly fails closed upon detecting
    any cryptographic mutation (Merkle root forgery) in the evidence package.
    """
    demo_dir = tmp_path / "golden_run_tamper"
    engine = GoldenDemoEngine(demo_dir=demo_dir)

    engine.start()
    engine.distribute()
    engine.leak()
    engine.investigate()
    res_ver = engine.verify()
    assert res_ver["verification_status"] == VerificationStatus.VERIFIED.value

    # Inject tamper attack
    res_tamper = engine.tamper()
    assert res_tamper["status"] == "PASS"
    assert res_tamper["verifier_verdict"] == VerificationStatus.INVALID.value
    assert res_tamper["rejection_confirmed"] is True
    assert len(res_tamper["detected_errors"]) > 0

    tamper_json = json.loads((demo_dir / "tamper.json").read_text(encoding="utf-8"))
    assert tamper_json["tamper_attack_type"] == "MERKLE_ROOT_FORGERY"
    assert tamper_json["verifier_rejected"] is True

    # Restore pristine package
    res_restore = engine.restore()
    assert res_restore["status"] == "PASS"
    assert res_restore["verifier_verdict"] == VerificationStatus.VERIFIED.value

    engine.reset()
