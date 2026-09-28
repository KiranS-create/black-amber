# Forensic Attribution Levels & The Fundamental Impossibility Boundary

## 1. Hierarchical Attribution Levels

AegisTrace defines five strictly hierarchical forensic attribution levels. Higher levels require increasingly specific and corroborated evidence. **The system enforces an absolute constraint: if only evidence for Level $k$ is established, the system is mathematically and procedurally forbidden from claiming Level $k+1$.**

```
▲ Level 5: Human Identity Resolved (Corroborating Telemetry Required)
│ Level 4: Controlled Lineage Identified (Multi-Hop Graph & Signed Receipts)
│ Level 3: Specific Copy Instance Identified (Copy-Bound Fingerprint)
│ Level 2: Original Recipient Identified (Initial Issuance Fingerprint)
│ Level 1: Document Detected (Canonical Hash / Master Payload Recovered)
```

### Detailed Level Specifications:

| Level | Name | Definitive Evidence Required | Allowable Claims |
| :--- | :--- | :--- | :--- |
| **Level 1** | **DOCUMENT_DETECTED** | Canonical master document hash matches, or document watermark payload extracted without recipient binding. | Document belongs to the enterprise catalog. No recipient or holder can be accused. |
| **Level 2** | **ORIGINAL_RECIPIENT_IDENTIFIED** | Tardos fingerprint or watermark payload matches a recipient's initial issuance record. No downstream forwarding records exist. | The artifact was originally issued to Recipient $R_0$. Downstream dissemination cannot be proven. |
| **Level 3** | **COPY_INSTANCE_IDENTIFIED** | Embedded fingerprint resolves uniquely to a specific derivative copy instance (`cpy_...`), but the full ancestry path has not yet been verified. | Specific copy instance identified. Custody attributed to the copy's designated holder. |
| **Level 4** | **LINEAGE_IDENTIFIED** | Full directed acyclic graph from root to leaf verified with valid ML-DSA-65 transition receipts (`ForwardingEvent` / `ExportEvent`). | Unbroken chain of controlled custody proven: $R_0 \to R_1 \to \dots \to R_n$. |
| **Level 5** | **HUMAN_IDENTITY_RESOLVED** | Level 4 lineage AND independent external corroborating telemetry (EDR process execution, DLP USB write, screenshot log, or physical sensor match). | Specific individual performed the exfiltration action. |

---

## 2. The Fundamental Impossibility Boundary

A foundational principle of cryptographic forensics is:
> **The Impossibility Boundary:** If an actor receives an exact bitwise document copy and passes that same bitstream through an uncontrolled channel (e.g. personal email, thumb drive, messaging app, dark web forum) without interacting with an identity-bound or attestation-enforced platform, the leaked artifact alone *cannot* reveal the downstream actor.

### Canonical Concrete Case Study:
Consider the following dissemination sequence:
1. **Master Document** created by Issuer.
2. Initial Copy ($C_0$) issued to **Alice** inside AegisTrace (controlled).
3. Alice uses AegisTrace to share the document to **Bob** ($C_1$), generating a cryptographically signed `ForwardingEvent` receipt (controlled).
4. Bob copies the exact bitstream of $C_1$ to an external USB stick and hands it to **Unknown X** (uncontrolled, out-of-band).
5. Unknown X passes the file to **Unknown Y** (uncontrolled).
6. Unknown Y posts the file on a public forum.

### How AegisTrace Responds (Honesty Invariant):
When the public leak is ingested and analyzed:
1. AegisTrace extracts the watermark/fingerprint embedded in $C_1$.
2. It queries `LineageStorage` and finds $C_1$ assigned to Bob, derived from Alice ($C_0$).
3. It verifies Alice's ML-DSA-65 signature on the forwarding receipt.
4. **Attribution Boundary Decision:**
   - **Attribution Level:** Strictly capped at `LEVEL_4_LINEAGE_IDENTIFIED` (or `LEVEL_3`) in the absence of independent telemetry.
   - **Last Known Controlled Holder:** **Bob** (`rec_bob_contractor`).
   - **Forensic Boundary State:** `LAST_KNOWN_HOLDER` and `UNKNOWN_DOWNSTREAM_ACTOR`.
   - **Attribution Summary Output:**
     > *"Attributed to last known controlled custodian 'rec_bob_contractor' (Downstream uncontrolled leakage detected; intermediary not personally accused)."*
   - **Guilt Assessment:** AegisTrace explicitly **REFUSES** to claim that Bob personally committed the leak. Bob is identified as the *last verified custodian* within the controlled boundary.
   - **Downstream Inventions:** AegisTrace strictly **REFUSES** to invent downstream identities (Unknown X or Unknown Y).
   - **Elevation to Level 5:** ONLY when independent external corroborating telemetry (EDR process execution logs, CASB cloud events, DLP removable media writes, or physical camera PRNU sensor matching) explicitly confirms Bob's or an external actor's physical action does the multi-channel Bayesian Evidence Fusion Engine legitimately elevate the finding to `LEVEL_5_HUMAN_IDENTITY_RESOLVED`.

---

## 3. Forensic Boundary States

The `ForensicBoundaryState` enum categorizes the boundary between controlled and uncontrolled custody:

| Boundary State | Forensic Meaning | Action Required |
| :--- | :--- | :--- |
| `ATTRIBUTED_TO_CONTROLLED_ACTOR` | Leak occurred directly from a controlled session or actor. | Initiate compliance/incident response protocol. |
| `LAST_KNOWN_HOLDER` | Chain of controlled custody verified up to actor $K$, after which uncontrolled leakage occurred. | Interrogate custodian $K$ regarding downstream dissemination. |
| `LINEAGE_CONTINUES` | Active intermediate node in controlled lineage graph. | Continue lineage traversal. |
| `LINEAGE_BROKEN` | Cryptographic signature failure, cycle, missing parent, or cross-document contamination. | Abstain from attribution; flag tampering investigation. |
| `UNKNOWN_DOWNSTREAM_ACTOR` | Artifact passed through out-of-band channels after last controlled holder. | Acknowledge impossibility of resolving downstream identities without external telemetry. |
| `IDENTITY_UNRESOLVED` | Cryptographic principal confirmed, but enterprise directory lookup is unavailable/pending. | Display principal ID; preserve cryptographic attribution pending directory sync. |
| `INSUFFICIENT_EVIDENCE` | Signals below Bayesian attribution threshold or margin. | Mandatory abstention (`should_abstain = True`). |
| `CONFLICT` | Multi-source disagreement (e.g. watermark and Tardos point to different recipients). | Mandatory fail-closed abstention. |
| `ABSTAINED` | Intentional abstention per decision policy. | Report abstention rationale to forensic investigator. |

---

## 4. Summary: Scientific Integrity as a Product Feature

In forensic and legal settings, overclaiming certainty destroys credibility. AegisTrace’s strict adherence to the Fundamental Impossibility Boundary and hierarchical attribution levels guarantees that every finding presented in court or an executive briefing is mathematically airtight, reproducible, and impervious to cross-examination challenge.
