"""
AegisTrace Offline Signed Telemetry Bundles.

Enables secure, air-gapped, and tamper-evident transport of forensic telemetry
records using cryptographic manifests and HMAC/signature verification.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import List, Dict, Any, Tuple, Union, Optional, Set

from core.telemetry.event import ForensicEvent
from core.telemetry.models import IntegrityLevel


import os
import base64
from core.crypto.signatures import MLDSA65


class TelemetryBundleManager:
    """
    Creates and verifies cryptographically signed offline telemetry export bundles.
    Supports both HMAC-SHA256 and Post-Quantum ML-DSA-65 signatures with anti-replay nonces.
    """
    _seen_nonces: Set[str] = set()

    @classmethod
    def reset_anti_replay_cache(cls) -> None:
        """Clears seen nonces (primarily for isolated test fixtures)."""
        cls._seen_nonces.clear()

    @staticmethod
    def _compute_events_digest(events: List[ForensicEvent]) -> str:
        """Deterministic digest of all events in the bundle."""
        fingerprints = [ev.compute_event_fingerprint() for ev in sorted(events, key=lambda x: x.event_id)]
        combined = ":".join(fingerprints).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    @classmethod
    def create_bundle(
        cls,
        events: List[ForensicEvent],
        signing_key: bytes,
        signer_id: str = "AEGISTRACE_SEC_OPS",
        nonce: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a signed bundle dictionary containing events and cryptographic manifest."""
        now = datetime.now(timezone.utc)
        events_digest = cls._compute_events_digest(events)
        bundle_nonce = nonce or os.urandom(16).hex()

        manifest = {
            "version": "1.0",
            "signer_id": signer_id,
            "created_at": now.isoformat(),
            "event_count": len(events),
            "events_digest": events_digest,
            "bundle_nonce": bundle_nonce,
        }

        # Sign manifest
        manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
        signature = hmac.new(signing_key, manifest_bytes, hashlib.sha256).hexdigest()

        return {
            "manifest": manifest,
            "signature": signature,
            "events": [json.loads(ev.model_dump_json()) for ev in events],
        }

    @classmethod
    def export_bundle_json(
        cls,
        events: List[ForensicEvent],
        signing_key: bytes,
        signer_id: str = "AEGISTRACE_SEC_OPS",
    ) -> str:
        bundle = cls.create_bundle(events, signing_key, signer_id)
        return json.dumps(bundle, indent=2)

    @classmethod
    def import_and_verify_bundle(
        cls,
        bundle_data: Union[str, Dict[str, Any]],
        signing_key: bytes,
        enforce_anti_replay: bool = False,
    ) -> Tuple[List[ForensicEvent], bool]:
        """
        Import and verify an offline signed telemetry bundle.
        Returns:
            (events, is_valid)
        If tampered, replayed, or signature invalid, all imported events are marked
        with IntegrityLevel.UNTRUSTED and is_valid is False.
        """
        if isinstance(bundle_data, str):
            bundle = json.loads(bundle_data)
        else:
            bundle = bundle_data

        manifest = bundle.get("manifest", {})
        claimed_sig = bundle.get("signature", "")
        raw_events = bundle.get("events", [])
        nonce = manifest.get("bundle_nonce")

        # Check anti-replay if enabled
        if enforce_anti_replay and nonce:
            if nonce in cls._seen_nonces:
                # Replay detected
                events = [ForensicEvent.model_validate(ed) for ed in raw_events]
                for ev in events:
                    ev.integrity_status = IntegrityLevel.UNTRUSTED
                    ev.source_reliability = 0.0
                return events, False
            cls._seen_nonces.add(nonce)

        # 1. Verify manifest signature
        manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
        expected_sig = hmac.new(signing_key, manifest_bytes, hashlib.sha256).hexdigest()
        sig_valid = hmac.compare_digest(claimed_sig, expected_sig)

        # 2. Parse events
        events: List[ForensicEvent] = []
        for ed in raw_events:
            events.append(ForensicEvent.model_validate(ed))

        # 3. Verify events digest
        computed_digest = cls._compute_events_digest(events)
        digest_valid = (computed_digest == manifest.get("events_digest"))

        is_valid = sig_valid and digest_valid

        if not is_valid:
            # Mark all events as UNTRUSTED
            for ev in events:
                ev.integrity_status = IntegrityLevel.UNTRUSTED
                ev.source_reliability = 0.0

        return events, is_valid

    @classmethod
    def create_mldsa_bundle(
        cls,
        events: List[ForensicEvent],
        signing_private_key: bytes,
        signer_public_key: bytes,
        signer_id: str = "AEGISTRACE_PQC_AUTHORITY",
        nonce: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a Post-Quantum ML-DSA-65 digitally signed offline bundle."""
        now = datetime.now(timezone.utc)
        events_digest = cls._compute_events_digest(events)
        bundle_nonce = nonce or os.urandom(16).hex()

        manifest = {
            "version": "2.0-PQC",
            "signer_id": signer_id,
            "created_at": now.isoformat(),
            "event_count": len(events),
            "events_digest": events_digest,
            "bundle_nonce": bundle_nonce,
            "signer_public_key_b64": base64.b64encode(signer_public_key).decode("utf-8"),
        }

        manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
        sig_bytes = MLDSA65.sign(signing_private_key, manifest_bytes)
        signature_b64 = base64.b64encode(sig_bytes).decode("utf-8")

        return {
            "manifest": manifest,
            "signature_pqc": signature_b64,
            "algorithm": "ML-DSA-65",
            "events": [json.loads(ev.model_dump_json()) for ev in events],
        }

    @classmethod
    def import_and_verify_mldsa_bundle(
        cls,
        bundle_data: Union[str, Dict[str, Any]],
        expected_public_key: Optional[bytes] = None,
        enforce_anti_replay: bool = True,
    ) -> Tuple[List[ForensicEvent], bool]:
        """
        Verify Post-Quantum ML-DSA-65 digitally signed offline bundle.
        """
        if isinstance(bundle_data, str):
            bundle = json.loads(bundle_data)
        else:
            bundle = bundle_data

        manifest = bundle.get("manifest", {})
        sig_b64 = bundle.get("signature_pqc", "")
        raw_events = bundle.get("events", [])
        nonce = manifest.get("bundle_nonce")

        # Anti-replay check
        if enforce_anti_replay and nonce:
            if nonce in cls._seen_nonces:
                events = [ForensicEvent.model_validate(ed) for ed in raw_events]
                for ev in events:
                    ev.integrity_status = IntegrityLevel.UNTRUSTED
                    ev.source_reliability = 0.0
                return events, False
            cls._seen_nonces.add(nonce)

        # Retrieve public key
        pub_bytes = expected_public_key
        if not pub_bytes and "signer_public_key_b64" in manifest:
            pub_bytes = base64.b64decode(manifest["signer_public_key_b64"])

        if not pub_bytes or not sig_b64:
            events = [ForensicEvent.model_validate(ed) for ed in raw_events]
            for ev in events:
                ev.integrity_status = IntegrityLevel.UNTRUSTED
            return events, False

        # Verify ML-DSA signature
        manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
        sig_bytes = base64.b64decode(sig_b64)
        sig_valid = MLDSA65.verify(pub_bytes, manifest_bytes, sig_bytes)

        events = [ForensicEvent.model_validate(ed) for ed in raw_events]
        computed_digest = cls._compute_events_digest(events)
        digest_valid = (computed_digest == manifest.get("events_digest"))

        is_valid = sig_valid and digest_valid
        if not is_valid:
            for ev in events:
                ev.integrity_status = IntegrityLevel.UNTRUSTED
                ev.source_reliability = 0.0

        return events, is_valid
