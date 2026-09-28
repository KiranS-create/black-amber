# AegisTrace External Telemetry Architecture

## 1. Executive Summary

AegisTrace incorporates an air-gapped, verifiable telemetry correlation architecture designed to bridge internal cryptographic forensic evidence (ML-KEM/ML-DSA bindings, Tardos fingerprint vectors, and hash-chain audit ledgers) with external operational signals from enterprise sensors and public intelligence feeds.

When an artifact leaves the controlled perimeter of the AegisTrace platform, artifact-level cryptographic markers can establish original distribution provenance. However, understanding downstream handling, secondary distribution, and exfiltration pathways requires correlating heterogeneous telemetry streams:
- **Endpoint Detection & Response (EDR)**: Kernel file read/write, process lineage, child spawns, interactive console logons.
- **Data Loss Prevention (DLP)**: Policy alerts, USB mass-storage transfers, removable media writes, unauthorized exports.
- **Cloud Access Security Broker (CASB) & CloudTrail**: S3 bucket object access, pre-signed URL creation, external cloud sharing links.
- **Identity Providers (IdP)**: Single Sign-On (SSO) authentication, WebAuthn/FIDO2 MFA verification, conditional access policies, impossible travel signals.
- **Network Egress Telemetry**: Flow records, TLS SNI proxies, firewall logs, VPN gateways, Tor exit correlation.
- **Print Spoolers & Physical Scanning**: Spooler event logs, yellow tracking dots (Machine Identification Codes / MIC).
- **Physical Device Forensics**: Camera sensor Photo Response Non-Uniformity (PRNU), hardware TPM attestation.
- **Public Drops & Leak Intelligence**: Public pastebins, open code repositories, file dumps, anonymous drop services.

---

## 2. Ingestion & Normalization Layer

Enterprise operational telemetry arrives in diverse formats (JSON logs, Windows Event Logs, Syslog RFC 5424, Zeek TSV, CloudTrail JSON). AegisTrace enforces a strictly typed, canonical representation via the `ForensicEvent` model:

```
+-----------------------------------------------------------------------------------+
|                                 ForensicEvent                                     |
+--------------------+--------------------------------------------------------------+
| event_id           | Unique deterministic event identifier                        |
| timestamp          | UTC-normalized datetime (ISO 8601 with tzinfo)               |
| event_type         | Normalized action (FILE_READ, USB_WRITE, EGRESS_FLOW, etc.)  |
| source_system      | TelemetrySource enum (EDR, DLP, IDP, NETWORK, USB, etc.)     |
| subject_type       | Classification: ACCOUNT, DEVICE, NETWORK, HARDWARE, etc.     |
| subject_id         | Subject identifier (pseudonymized account or device serial)  |
| device_id          | Hardware serial, enrolled UUID, or workstation hostname      |
| network_id         | Source/egress IP address, CIDR, or MAC address               |
| resource_id        | Canonical resource path, URI, or target object key           |
| artifact_hash      | SHA-256 digest of original or derivative document            |
| copy_id            | Cryptographic copy ID / watermark symbol tag                 |
| session_id         | Authenticated logon / API session token ID                   |
| integrity_status   | IntegrityLevel (CRYPTOGRAPHICALLY_VERIFIED to UNTRUSTED)     |
| source_reliability | Channel reliability prior in [0.0, 1.0]                      |
| raw_payload        | Preserved unmutated original sensor fields                   |
+--------------------+--------------------------------------------------------------+
```

### Deterministic Event Fingerprinting
To guarantee tamper detection and idempotency, every `ForensicEvent` computes a canonical fingerprint:
$$\text{Fingerprint} = \text{SHA-256}\Big(\text{CanonicalJSON}\big(\{ts, source, type, subj, dev, net, res, hash, copy, sess\}\big)\Big)$$

---

## 3. Pluggable Telemetry Provider Architecture

The `ExternalTelemetryProvider` abstract base class defines the querying contract for forensic telemetry lookups:
- `query_by_artifact_hash(hash, start, end)`
- `query_by_copy_id(copy_id, start, end)`
- `query_by_device_id(device_id, start, end)`
- `query_by_actor(actor_id, start, end)`
- `query_by_network(network_id, start, end)`

### High-Performance In-Memory Store (`InMemoryTelemetryProvider`)
To achieve zero-dependency air-gapped operation during forensic investigations, the platform provides an optimized in-memory store featuring:
1. **Multi-Attribute Inverted Indexing**: Hash tables indexed by SHA-256 artifact hash, copy ID, actor account ID, device serial, and source system.
2. **Chronological Index**: Bisection-based timeline array supporting $O(\log N)$ time-range window slicing.
3. **Throughput**: Ingestion exceeds 160,000 to 250,000 events/second on standard laptop hardware; query latencies remain sub-millisecond for datasets up to 100,000 events.

---

## 4. Offline Signed Telemetry Bundles

In disconnected air-gapped field deployments (e.g. military, intelligence, or courtroom investigations), telemetry cannot be fetched live from SIEM APIs. AegisTrace implements `TelemetryBundleManager` for cryptographically verified offline exports:

1. **Manifest Construction**:
   - `created_at`: Export timestamp
   - `signer_id`: Forensic investigator or authority identity
   - `event_count`: Number of serialized records
   - `events_digest`: $\text{SHA-256}\Big(\bigoplus_{i=1}^n \text{Fingerprint}(e_i)\Big)$
2. **Cryptographic Sealing**:
   - The manifest is signed using HMAC-SHA256 or ML-DSA-65 post-quantum digital signature.
3. **Fail-Closed Verification**:
   - If signature verification fails, or if a single byte in any event payload is altered, all imported events are automatically marked `IntegrityLevel.UNTRUSTED` and assigned `source_reliability = 0.0`.
   - The downstream engine immediately enters the `ABSTAINED` state.
