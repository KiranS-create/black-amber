"""
AegisTrace Telemetry Privacy & Data Minimization.

Implements privacy-preserving pseudonymization, PII redaction, and retention
expiry enforcement for sensitive external telemetry feeds.
"""

from datetime import datetime, timezone
import hashlib
import hmac
from typing import List, Dict, Any, Optional

from core.telemetry.event import ForensicEvent


class TelemetryPrivacyManager:
    """
    Manages pseudonymization, PII sanitization, and retention enforcement.
    """

    def __init__(self, privacy_salt: bytes = b"aegistrace_telemetry_salt_2026"):
        self.salt = privacy_salt

    def pseudonymize_identifier(self, identifier: str) -> str:
        """Deterministic salted HMAC-SHA256 pseudonym for account/actor IDs."""
        if not identifier:
            return ""
        digest = hmac.new(self.salt, identifier.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"anon-{digest[:16]}"

    def pseudonymize_ip(self, ip_address: str) -> str:
        """Truncates host bits (subnets /24 for IPv4) or hashes IP."""
        if not ip_address:
            return ""
        parts = ip_address.split(".")
        if len(parts) == 4:
            # Mask last octet
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return self.pseudonymize_identifier(ip_address)

    def redact_event(self, event: ForensicEvent) -> ForensicEvent:
        """
        Produce a privacy-minimized copy of the ForensicEvent:
        - Pseudonymizes subject_id
        - Masks network_id IP
        - Strips sensitive raw parameters (passwords, auth tokens, file contents)
        """
        redacted_payload = event.raw_payload.copy()
        # Strip high-risk keys
        for key in ["password", "token", "auth_token", "user_agent", "process_path", "attachment_filename"]:
            if key in redacted_payload:
                redacted_payload[key] = "[REDACTED]"

        anon_subj = self.pseudonymize_identifier(event.subject_id) if event.subject_id else None
        anon_net = self.pseudonymize_ip(event.network_id) if event.network_id else None

        return ForensicEvent(
            event_id=f"redacted-{event.event_id}",
            timestamp=event.timestamp,
            event_type=event.event_type,
            source_system=event.source_system,
            subject_type=event.subject_type,
            subject_id=anon_subj,
            device_id=event.device_id,
            network_id=anon_net,
            resource_id=event.resource_id,
            artifact_hash=event.artifact_hash,
            copy_id=event.copy_id,
            session_id=None,  # Strip session ID for privacy
            parent_event_id=event.parent_event_id,
            location_metadata={"country": event.location_metadata.get("country", "CONFIDENTIAL")},
            integrity_status=event.integrity_status,
            source_reliability=event.source_reliability,
            raw_payload=redacted_payload,
        )

    def purge_expired_events(
        self,
        events: List[ForensicEvent],
        current_time: Optional[datetime] = None,
        retention_days: int = 90,
    ) -> List[ForensicEvent]:
        """
        Filter out telemetry events whose age exceeds the retention policy window.
        """
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        valid_events = []
        for ev in events:
            ts = ev.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age_days = (now - ts).total_seconds() / 86400.0
            if age_days <= retention_days:
                valid_events.append(ev)
        return valid_events
