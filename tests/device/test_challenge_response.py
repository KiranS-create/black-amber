"""
Unit tests for AegisTrace Device Attestation Challenge-Response Engine.

Verifies:
- 256-bit cryptographically secure fresh nonces
- Single-use validation (replay attack prevention)
- Time-to-live and expiration enforcement
- Multi-tenant boundary isolation (cross-tenant nonce injection rejection)
- Device-binding boundary enforcement (cross-device nonce replay rejection)
- Unknown / forged nonce rejection
"""

import time
import pytest
from datetime import datetime, timezone, timedelta

from core.device.challenge import ChallengeManager, AttestationChallenge


def test_challenge_generation():
    mgr = ChallengeManager(default_ttl_seconds=60)
    ch = mgr.create_challenge(device_id="dev_001", organization_id="org_gov")

    assert ch.device_id == "dev_001"
    assert ch.organization_id == "org_gov"
    assert len(ch.nonce_hex) == 64  # 32 bytes = 64 hex characters
    assert ch.used is False
    assert ch.challenge_id.startswith("chal_")


def test_challenge_successful_validation_and_consumption():
    mgr = ChallengeManager()
    ch = mgr.create_challenge(device_id="dev_001", organization_id="org_gov")

    # First validation succeeds
    valid, reason = mgr.validate_nonce(
        nonce_hex=ch.nonce_hex,
        device_id="dev_001",
        organization_id="org_gov",
        consume=True,
    )
    assert valid is True
    assert reason is None

    # Immediate second validation fails due to single-use replay prevention
    valid2, reason2 = mgr.validate_nonce(
        nonce_hex=ch.nonce_hex,
        device_id="dev_001",
        organization_id="org_gov",
        consume=True,
    )
    assert valid2 is False
    assert reason2 == "NONCE_REUSED_REPLAY_ATTACK"


def test_challenge_device_mismatch():
    mgr = ChallengeManager()
    ch = mgr.create_challenge(device_id="dev_real", organization_id="org_gov")

    # Attacker tries to use real device's nonce for rogue device
    valid, reason = mgr.validate_nonce(
        nonce_hex=ch.nonce_hex,
        device_id="dev_rogue",
        organization_id="org_gov",
        consume=True,
    )
    assert valid is False
    assert reason == "DEVICE_ID_MISMATCH"


def test_challenge_organization_mismatch():
    mgr = ChallengeManager()
    ch = mgr.create_challenge(device_id="dev_001", organization_id="org_internal")

    # Attacker tries to use internal nonce in external tenant
    valid, reason = mgr.validate_nonce(
        nonce_hex=ch.nonce_hex,
        device_id="dev_001",
        organization_id="org_external",
        consume=True,
    )
    assert valid is False
    assert reason == "ORGANIZATION_MISMATCH"


def test_challenge_expiration():
    # Challenge with 1 second TTL
    mgr = ChallengeManager(default_ttl_seconds=1)
    ch = mgr.create_challenge(device_id="dev_exp", organization_id="org_gov", ttl_seconds=1)

    time.sleep(1.2)

    valid, reason = mgr.validate_nonce(
        nonce_hex=ch.nonce_hex,
        device_id="dev_exp",
        organization_id="org_gov",
        consume=True,
    )
    assert valid is False
    assert reason == "CHALLENGE_EXPIRED"


def test_challenge_unknown_nonce():
    mgr = ChallengeManager()
    bogus_nonce = "00" * 32

    valid, reason = mgr.validate_nonce(
        nonce_hex=bogus_nonce,
        device_id="dev_001",
        organization_id="org_gov",
    )
    assert valid is False
    assert reason == "CHALLENGE_NOT_FOUND"


def test_challenge_cleanup_expired():
    mgr = ChallengeManager()
    # Create an expired challenge manually
    ch = mgr.create_challenge(device_id="dev_clean", organization_id="org_gov", ttl_seconds=0)
    time.sleep(0.01)

    cleaned = mgr.cleanup_expired()
    assert cleaned >= 1
    assert ch.challenge_id not in mgr._challenges
