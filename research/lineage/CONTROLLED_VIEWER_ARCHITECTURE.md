# Controlled Viewer Boundary: Architecture & Implementation

## 1. Overview & Security Objectives

The **Controlled Viewer** (`core/lineage/viewer.py`) represents the execution perimeter where protected documents are rendered and manipulated. Its primary security goals are:

1. **Prevent Unmonitored Plaintext Exposure:** Raw master plaintext is never written to disk or exposed to client processes without cryptographic encapsulation.
2. **Dynamic Session Binding:** Every view session composites an ephemeral, pseudonymous visual and spatial watermark (`sf_...`) unique to that specific viewing instance.
3. **Mandatory Export Interception:** Users cannot download, print, or save an un-tracked copy. Any export action dynamically generates a derivative child copy instance, records a signed transition receipt, and re-fingerprints the exported payload.
4. **Hardware Attestation Honesty:** In local environments without TPM or Secure Enclave chips, the system strictly outputs `DEVICE_UNATTESTED` rather than faking hardware security.

---

## 2. In-Memory Decryption Architecture

Documents at rest in AegisTrace storage are encrypted using standard **AES-256-GCM** (NIST SP 800-38D).

```
               [AES-256-GCM Encrypted Document Store]
                                 │
                                 ▼
                     [Authenticated AccessSession]
                                 │ (Session Active Check)
                                 ▼
    [Ephemeral In-Memory Decryption: AES-256-GCM Decrypt]
                                 │
                                 ▼
         [Dynamic Session Watermark Layer: sf_...]
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
[Screen Rendering Boundary]                 [Controlled Export Boundary]
(Visual Overlay sf_...)                     (Re-fingerprint & Child Copy)
```

### Protocol Steps:
1. `viewer.register_master_document(doc_id, plaintext)` encrypts the document with an ephemeral 256-bit symmetric key and stores `nonce || tag || ciphertext`.
2. When a recipient views the document, `viewer.open_session(copy_id, identity_id)` creates an `AccessSession` with an expiration window and generates a unique session watermark key:
   $$\text{session\_fingerprint\_key} = \text{"sf\_"} + \text{os.urandom(12).hex()}$$
3. `viewer.render_view(session_id)` asserts that the session is valid and active, decrypts the ciphertext in RAM, and overlays the session watermark.

---

## 3. Dynamic Session Watermarking (`sf_...`)

If an attacker captures the screen using an out-of-band mechanism (e.g. mobile phone camera or OS-level screen capture tool):
- The rendered display contains the session watermark token: `AEGIS:sf_<hex>:cpy_<hex>`.
- When the captured image is recovered, AegisTrace extracts `sf_...`.
- `LineageService.find_session_by_fingerprint(...)` resolves the exact `AccessSession`, authenticated user identity, timestamp, and device.
- Even without access to the digital file, the leak is cryptographically pinned to the specific viewing session.

---

## 4. Controlled Export Boundary & Re-Fingerprinting

When a user initiates an export (PDF, Image, Print):
1. The request is intercepted by `ControlledViewer.controlled_export(...)`.
2. The viewer invokes `LineageService.export_copy(...)` to mint a new child `CopyInstance` (depth $d+1$) in the lineage graph.
3. An `ExportEvent` receipt is signed with **ML-DSA-65**.
4. The master bytes are decrypted and re-fingerprinted with the child copy's unique fingerprint reference (`exp_fp_...`).
5. Only the re-fingerprinted artifact is returned to the user.

Any subsequent leak of this exported file carries the child fingerprint, proving that it originated from that specific export operation rather than the parent session.

---

## 5. Device Binding & Attestation Honesty

AegisTrace models device identity through `DeviceBindingProvider` (`core/lineage/device.py`):

### Honesty Invariant:
- In environments without physical hardware security modules (local developer laptops, standard CI/CD runners, cloud VMs without vTPM), the system utilizes `LocalSoftwareDeviceProvider`.
- It registers an ML-DSA-65 keypair and signs challenges, but explicitly returns:
  $$\text{attestation\_status} = \text{DeviceAttestationStatus.DEVICE\_UNATTESTED}$$
  $$\text{platform\_type} = \text{PlatformType.SOFTWARE\_LOCAL}$$
- The system **NEVER** claims `DEVICE_ATTESTED` when hardware attestation is absent.
- In production hardware-enforced environments, TPM 2.0 or Apple Secure Enclave quotes provide verifiable cryptographic attestation.

---

## 6. External Enterprise Telemetry Integration

To elevate an attribution from Level 4 (Copy Lineage) to Level 5 (Resolved Human Identity), independent external corroboration is mandatory:

The `ExternalTelemetryProvider` (`core/lineage/telemetry.py`) correlates:
- **EDR Events:** Process executions (e.g. `SnippingTool.exe`, `curl.exe`).
- **DLP Events:** Removable media writes (e.g. USB flash drive exfiltration).
- **CASB / Network Events:** Unauthorized cloud storage uploads.

If corroborating telemetry matches the candidate principal within the leak time window, the confidence score is elevated and attribution is confirmed at Level 5. If no corroboration exists, the attribution remains strictly bounded at Level 4.
