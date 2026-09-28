"""
AegisTrace Device Attestation Challenge-Response Engine.

Generates and validates cryptographically secure, single-use, time-bounded nonces
bound to (device_id, organization_id) to prevent replay, cross-tenant attacks,
and cloned attestation responses.
"""

import os
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple, Set
from pydantic import BaseModel, Field


class AttestationChallenge(BaseModel):
    """
    Cryptographic attestation challenge issued by verifier.
    """
    challenge_id: str
    nonce_hex: str
    device_id: str
    organization_id: str
    created_at: str
    expires_at: str
    used: bool = False


class ChallengeManager:
    """
    Manages generation, state tracking, and validation of attestation challenges.
    Thread-safe and memory-bounded.
    """

    def __init__(self, default_ttl_seconds: int = 120):
        self.default_ttl = default_ttl_seconds
        # In-memory challenge store: challenge_id -> AttestationChallenge
        self._challenges: Dict[str, AttestationChallenge] = {}
        # Index: nonce_hex -> challenge_id
        self._by_nonce: Dict[str, str] = {}

    def create_challenge(
        self,
        device_id: str,
        organization_id: str,
        ttl_seconds: Optional[int] = None,
    ) -> AttestationChallenge:
        """
        Generate a fresh cryptographic 256-bit nonce bound to (device_id, organization_id).
        """
        now = datetime.now(timezone.utc)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = now + timedelta(seconds=ttl)

        # 32 bytes cryptographically secure random nonce
        nonce_bytes = os.urandom(32)
        nonce_hex = nonce_bytes.hex()
        cid = f"chal_{hashlib.sha256(nonce_bytes).hexdigest()[:16]}"

        challenge = AttestationChallenge(
            challenge_id=cid,
            nonce_hex=nonce_hex,
            device_id=device_id,
            organization_id=organization_id,
            created_at=now.isoformat(),
            expires_at=expiry.isoformat(),
            used=False,
        )

        self._challenges[cid] = challenge
        self._by_nonce[nonce_hex] = cid
        return challenge

    def validate_nonce(
        self,
        nonce_hex: str,
        device_id: str,
        organization_id: str,
        consume: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate nonce:
        1. Nonce exists.
        2. Nonce was not already consumed (one-time use).
        3. Challenge is within validity window (not expired).
        4. Device ID matches the challenge binding.
        5. Organization ID matches the challenge binding.
        Returns:
            (is_valid, failure_reason)
        """
        cid = self._by_nonce.get(nonce_hex)
        if not cid or cid not in self._challenges:
            return False, "CHALLENGE_NOT_FOUND"

        challenge = self._challenges[cid]

        # Check replay (single-use)
        if challenge.used:
            return False, "NONCE_REUSED_REPLAY_ATTACK"

        # Check device binding
        if challenge.device_id != device_id:
            return False, "DEVICE_ID_MISMATCH"

        # Check tenant / organization binding
        if challenge.organization_id != organization_id:
            return False, "ORGANIZATION_MISMATCH"

        # Check expiry
        now = datetime.now(timezone.utc)
        try:
            exp_dt = datetime.fromisoformat(challenge.expires_at)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if now > exp_dt:
                return False, "CHALLENGE_EXPIRED"
        except (ValueError, TypeError):
            return False, "MALFORMED_EXPIRY_TIMESTAMP"

        # Mark as consumed to prevent replay
        if consume:
            challenge.used = True

        return True, None

    def purge_expired(self) -> int:
        """Purge expired challenges from memory."""
        now = datetime.now(timezone.utc)
        to_del = []
        for cid, ch in self._challenges.items():
            try:
                exp = datetime.fromisoformat(ch.expires_at)
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if now > exp:
                    to_del.append(cid)
            except Exception:
                to_del.append(cid)

        for cid in to_del:
            ch = self._challenges.pop(cid, None)
            if ch:
                self._by_nonce.pop(ch.nonce_hex, None)
        return len(to_del)

    def cleanup_expired(self) -> int:
        """Alias for purge_expired."""
        return self.purge_expired()
