# SIH26237 — Security Architecture & Threat Model Specification

**Status**: Baseline Threat Model & Defense-in-Depth Specification  
**Version**: 1.0.0  
**Authors**: Agent 8 (Principal Application Security Engineer & Red-Team Auditor)  
**Classification**: Engineering & Security Architecture Standard  

---

## 1. System Overview & Security Principles

SIH26237 provides an enterprise-grade document distribution, watermarking, traitor-tracing, and forensic leak attribution platform. The architecture is built upon post-quantum cryptographic primitives (NIST FIPS 203 `ML-KEM-768`, NIST FIPS 204 `ML-DSA-65`), symmetric authenticated envelope encryption (`AES-256-GCM`), symbol-symmetric traitor-tracing (`Symmetric Tardos Codes`), multi-layer physical watermarking (`DSSS + Reed-Solomon + OpenCV ArUco`), and a hash-chained tamper-evident audit ledger (`SHA-256`).

### Core Security Axioms
1. **Zero-Trust Fail-Closed Attribution**: Under no circumstances may ambiguity, carrier degradation, malformed payloads, or conflicting signals force an attribution. If evidence does not meet strict statistical and cryptographic thresholds, the system MUST abstain (`INSUFFICIENT_EVIDENCE`, `NO_SIGNAL`, or `CONFLICT`).
2. **Key Isolation & Decentralized Decryption**: Recipient private keys are the sovereign property of the recipient. The central distribution server MUST NOT generate, store, or hold custody of recipient private decapsulation (`ML-KEM`) or signing (`ML-DSA`) keys.
3. **Cryptographic Target Binding**: All forensic artifacts, watermark payloads, provenance events, and ledger records are bound to a strict tuple: `(document_id, release_id, recipient_id, document_hash)`.
4. **Anti-Double-Counting**: Lineage-derived and correlated evidence channels must never be additively summed to artificially inflate attribution confidence.
5. **Tamper-Evident Non-Repudiation**: Decryption provenance events must be sequentially linked in a cryptographic hash chain and digitally signed by the recipient before physical release.

---

## 2. Threat Model: Threat Actors & Attack Vectors

The SIH26237 threat model defines six primary threat actors operating against the system boundaries:

```
+-----------------------------------------------------------------------------------------------+
|                                      THREAT ACTOR TAXONOMY                                    |
+---------------------+-------------------------------+-----------------------------------------+
| Actor               | Capabilities                  | Primary Objectives                      |
+---------------------+-------------------------------+-----------------------------------------+
| A. Malicious        | Legitimate recipient with     | Leak document without attribution;      |
|    Recipient        | valid private keys and        | alter carrier to destroy watermark;     |
|                     | traceable release copy        | blame another recipient.                |
+---------------------+-------------------------------+-----------------------------------------+
| B. Colluding        | Coalition of 2 to c           | Intersect multiple watermarked copies;  |
|    Recipients       | recipients sharing copies     | perform majority voting, splicing,      |
|                     | of same release               | or min/max symbol erasure.              |
+---------------------+-------------------------------+-----------------------------------------+
| C. External         | Network-adjacent attacker     | Upload hostile artifacts; perform DoS;  |
|    Attacker         | interacting with API;         | exploit parsing flaws; forge evidence;  |
|                     | no recipient private keys     | tamper with analysis requests.          |
+---------------------+-------------------------------+-----------------------------------------+
| D. Compromised      | Access to server storage,     | Rewrite audit ledger; inject fabricated |
|    Operator         | database, and configuration   | provenance events; manipulate fusion    |
|                     |                               | policy parameters to frame recipients.  |
+---------------------+-------------------------------+-----------------------------------------+
| E. Malicious        | Weaponized PDF/image/ZIP;     | Cause parser crashes, buffer overflows, |
|    Artifact         | decompression bombs,          | infinite recursion, or heap exhaustion  |
|                     | deeply nested structures      | during carrier processing.              |
+---------------------+-------------------------------+-----------------------------------------+
| F. Replay           | Intercepted prior valid       | Replay previous decryption signatures;  |
|    Attacker         | evidence bundles or events    | cross-contaminate releases; inflate     |
|                     |                               | prior scores with duplicate records.    |
+---------------------+-------------------------------+-----------------------------------------+
```

---

## 3. Threat Matrix & Detailed Attack Scenarios

### Actor A: Malicious Recipient
- **Vector A1 (Carrier Manipulation)**: The recipient subjects their traceable copy to heavy printing, crumpling, geometric shearing, rescanning, and digital recompression (e.g. JPEG Q=10).
  - *Defense*: DSSS spread-spectrum modulation combined with ArUco perspective rectification and Reed-Solomon $(n, k)$ error correction. If bit error rate exceeds correction capacity, the decoder outputs `NO_SIGNAL` or `PARTIAL` rather than guessing.
- **Vector A2 (Transplantation / Framing)**: The recipient extracts the watermark footer or ArUco fiducials and embeds them into an unrelated top-secret document to falsely attribute it.
  - *Defense*: Watermark payload codec includes CRC32 and cryptographic document binding `(document_id, release_id)`. Mismatched document IDs return `INVALID`, causing immediate fail-closed abstention.

### Actor B: Colluding Recipients
- **Vector B1 (Collusion Attacks)**: A coalition of $c \le 3$ colluders align their document pages. At each location where pixels differ, they randomize, average, or erase symbols.
  - *Defense*: Symmetric Tardos Fingerprinting Codes. Secret column biases $p_j \in [t, 1-t]$ drawn from the continuous arcsine distribution ensure that the expected score for innocent recipients is zero ($E[S_{\text{innocent}}] = 0$) under any collusion strategy. Guilty colluders accumulate score $\sum_{k \in C} E[S_k] \ge \frac{2}{\pi} m$. If multiple colluders cross threshold $Z = \sqrt{2m \ln(N / \epsilon_1)}$, the system reports `COLLUSION_DETECTED` with formal false-alarm bound $\epsilon_1 \le 10^{-4}$.

### Actor C: External Attacker
- **Vector C1 (Decryption Endpoint Oracle)**: An unauthenticated attacker calls `POST /releases/{id}/decrypt` specifying a target recipient ID.
  - *Vulnerability in current prototype*: Server executes decryption and signs on behalf of the recipient.
  - *Target Architecture*: Decentralized client-side decryption. The server only hosts encrypted packages (`ReleaseRecipientPackage`). Decryption and signing occur strictly on client hardware; the client submits only the signed `EvidenceEvent` back to the server.
- **Vector C2 (Unrestricted Resource Consumption / DoS)**: Submitting huge payloads (500MB+) via JSON base64.
  - *Defense*: Enforce strict payload limits at the reverse proxy and FastAPI middleware layer ($50 \text{ MB}$ max). Reject payloads exceeding the threshold before base64 decoding.

### Actor D: Compromised Operator
- **Vector D1 (Ledger Tampering / History Rewriting)**: An operator modifies an entry in the SQLite database or disk to frame or exonerate a suspect.
  - *Defense*: Hash-chained ledger where event $i$ contains `previous_event_hash` = $\text{SHA256}(\text{Event}_{i-1})$. Periodic chain verification (`/ledger/verify`) immediately detects broken links, reordering, event duplication, or altered fields.

### Actor E: Malicious Artifact
- **Vector E1 (Decompression Bombs & Nested Objects)**: Attacker uploads a tiny PDF that decompresses to 10GB of null bytes or contains circular indirect object references (`1 0 obj << /Parent 1 0 R >>`).
  - *Defense*: Sandboxed parsing with strict recursion depth limits, timeout watchdog (5 seconds per artifact), and memory ceiling per worker process.
- **Vector E2 (MIME & Extension Confusion)**: Uploading Windows PE executable (`.exe` or `MZ` header) disguised as a `.pdf`.
  - *Defense*: `sniff_mime_type()` inspects magic bytes (`%PDF`, `\x89PNG`, `\xff\xd8\xff`). Rejects unsupported binaries with HTTP 415.

### Actor F: Replay Attacker
- **Vector F1 (Evidence Duplication / Replay)**: Submitting the same evidence observation multiple times in an inquiry to inflate log-likelihood ratio.
  - *Defense*: `EvidenceDependencyGraph.deduplicate_observations()` calculates deterministic signal payload fingerprints:
    $$\text{FP} = \text{SHA256}(\text{family} \parallel \text{primary\_candidate} \parallel \text{scores} \parallel \text{target\_binding})$$
    Duplicates are collapsed prior to scoring.
- **Vector F2 (Event ID Replay on Ledger)**: Re-submitting an existing signed provenance event.
  - *Defense*: `TamperEvidentLedger.append_event()` tracks `_seen_event_ids: Set[str]`. Replays are rejected with `ValueError("Replay detected: duplicate event_id rejected")`.

---

## 4. Multi-Layer Defense-in-Depth Model

```
+------------------------------------------------------------------------------------+
| LAYER 1: NETWORK & PERIMETER GATEWAY                                               |
| - Reverse proxy TLS termination                                                    |
| - Strict CORS policy (explicit allowed origins, disallow wildcard credentials)     |
| - Rate limiting (10 req/sec per IP, 2 analysis jobs/min per tenant)                |
| - Request size limits (50 MB HTTP body ceiling)                                    |
+------------------------------------------------------------------------------------+
                                          |
                                          v
+------------------------------------------------------------------------------------+
| LAYER 2: API SANITIZATION & IDENTITY CONTROL                                       |
| - Input validation via Pydantic V2 schemas with bounded numeric ranges             |
| - Path sanitization: regex whitelist [a-zA-Z0-9_\-\.], no path traversal          |
| - Magic-byte MIME sniffing (PDF, PNG, JPEG)                                        |
| - Nonce-based authentication headers (HMAC / Bearer JWT)                           |
+------------------------------------------------------------------------------------+
                                          |
                                          v
+------------------------------------------------------------------------------------+
| LAYER 3: POST-QUANTUM CRYPTOGRAPHIC ISOLATION                                      |
| - Key generation and private key custody strictly isolated to client edge          |
| - ML-KEM-768 FIPS 203 encapsulation with domain-separated HKDF-SHA256             |
| - AES-256-GCM envelope encryption with authenticated Associated Data               |
| - ML-DSA-65 FIPS 204 digital signatures on all provenance events                   |
+------------------------------------------------------------------------------------+
                                          |
                                          v
+------------------------------------------------------------------------------------+
| LAYER 4: PHYSICAL WATERMARK & TRAITOR-TRACING ENGINE                              |
| - 4-corner ArUco fiducials for geometric perspective rectification                 |
| - Reed-Solomon ECC $(n, k)$ with CRC32 payload verification                        |
| - 2D DSSS spatial/frequency modulation                                             |
| - Symmetric Tardos fingerprinting with continuous arcsine biases                   |
+------------------------------------------------------------------------------------+
                                          |
                                          v
+------------------------------------------------------------------------------------+
| LAYER 5: FORENSIC MULTI-CHANNEL EVIDENCE FUSION                                    |
| - Target binding verification: (doc_id, release_id, artifact_hash)                 |
| - Attack-aware reliability calibration (PSNR, SSIM, crop discounting)              |
| - Dependency graph with anti-double-counting (gamma=0.65 for partially dependent)  |
| - Fail-Closed Decision Policy: S >= 6.0, Delta >= 2.5, Conflict >= 5.0             |
+------------------------------------------------------------------------------------+
                                          |
                                          v
+------------------------------------------------------------------------------------+
| LAYER 6: TAMPER-EVIDENT AUDIT LEDGER                                               |
| - Sequential SHA-256 hash chaining                                                |
| - Anti-replay unique event IDs and 16-byte random nonces                           |
| - Recipient public key anchoring & offline verifiable proofs                       |
+------------------------------------------------------------------------------------+
```

---

## 5. Evidence Fusion Policy & Fail-Closed State Machine

The attribution decision engine operates as a deterministic, fail-closed finite state machine:

```
                          [ Incoming Evidence Bundle ]
                                       |
                                       v
                    +------------------------------------+
                    | Check Target Binding Consistency   |
                    +------------------------------------+
                               /               \
                       (Mismatch)             (Valid)
                             /                   \
                            v                     v
                    [ STATE: CONFLICT ]     +-----------------------------------+
                    (Cross-doc contamination| Deduplicate Observations          |
                     Abstain immediately)   +-----------------------------------+
                                                          |
                                                          v
                                            +-----------------------------------+
                                            | Reliability Calibration           |
                                            | (Attack degradation discounting)  |
                                            +-----------------------------------+
                                                          |
                                                          v
                                            +-----------------------------------+
                                            | Compute Fused Scores via Graph    |
                                            +-----------------------------------+
                                                          |
                                         +----------------+----------------+
                                        /                                   \
                                  (No Candidates)                     (Candidates Found)
                                       /                                     \
                                      v                                       v
                             [ STATE: NO_SIGNAL ]           +-----------------------------------+
                                                            | Primary Crypto Corroboration?     |
                                                            +-----------------------------------+
                                                                   /                    \
                                                                 (No)                  (Yes)
                                                                 /                        \
                                                                v                          v
                                                  [ STATE: INSUFFICIENT_EVIDENCE ]  +---------------+
                                                  (Non-crypto channels alone cannot | Check Conflict|
                                                   force attribution)               +---------------+
                                                                                           /     \
                                                         (Contradictory sources >= 5.0)   /       \ (No conflict)
                                                                                         v         v
                                                                                [ CONFLICT ]  +-------------+
                                                                                              | S1 >= 6.0 & |
                                                                                              | Delta >= 2.5|
                                                                                              +-------------+
                                                                                                /         \
                                                                                              (No)        (Yes)
                                                                                              /             \
                                                                                             v               v
                                                                                [ INSUFFICIENT_EVID ]  [ ATTRIBUTED ]
```

---

## 6. Zero-Trust Key Lifecycle Architecture

To resolve the critical vulnerability where the distribution server acts as a decryption oracle holding recipient private keys, the production architecture specifies a decentralized key lifecycle:

1. **Enrollment**:
   - The recipient device generates an `ML-KEM-768` keypair and an `ML-DSA-65` keypair locally in hardware (TPM / Secure Enclave).
   - Only `PublicRecipient` (`kem_public_key_b64`, `dsa_public_key_b64`) is transmitted to the server via `POST /recipients`.
   - Private keys NEVER leave the recipient's secure boundary.
2. **Release Distribution**:
   - Authority issues a document release.
   - The server encapsulates $K_{doc}$ using each recipient's public key.
   - The server stores only the encrypted package `ReleaseRecipientPackage`.
3. **Decryption & Provenance**:
   - The recipient downloads their encrypted package via `GET /releases/{id}/packages/{recipient_id}`.
   - Decapsulation, symmetric decryption, and watermark embedding occur entirely on the client workstation.
   - The client signs a `DECRYPTION_EVENT` using their private `ML-DSA-65` key.
   - The client submits the signed event to `POST /evidence/decryption-events` to register on the ledger.
4. **Verification**:
   - Anyone can verify the event using the recipient's public key stored in the immutable enrollment record.
   - The server is mathematically incapable of forging a recipient's signature.
