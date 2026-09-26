# SIH26237 — Hackathon Judge Experience & Cognitive Flow Analysis

**Author:** Agent 7 (Principal Frontend Engineer + Demo UX Architect)  
**Target Audience:** Smart India Hackathon (SIH) Technical & Executive Evaluation Panels  
**Scope:** `research/frontend/`

---

## 1. Judging Psychology & Cognitive Challenges

In top-tier competitions like the Smart India Hackathon, evaluators review dozens of complex security, cloud, and cryptography architectures in tight time slots (typically 5 to 10 minutes total, including Q&A). 

Common pitfalls in cryptographic project presentations:
1. **The "Black Box Terminal" Trap:** Running CLI commands in a terminal where strings of hex hashes fly by, leaving non-specialist judges unable to distinguish real cryptographic integrity from mock print statements.
2. **The "Theoretical Slide" Trap:** Spending 8 minutes explaining ML-KEM math or Tardos Dirichlet distributions on slides without demonstrating live software in action.
3. **The "Fragile Cloud Demo" Trap:** Relying on live internet connections or unverified cloud endpoints that fail due to venue Wi-Fi congestion.
4. **The "Unsubstantiated Overclaim" Trap:** Claiming "zero false accusations" or "100% security" without providing bounded false alarm bounds ($\epsilon_1$) or fail-closed failure states.

---

## 2. Key Hackathon Evaluation Criteria & Frontend Answers

| Evaluation Dimension | Weight | What the Judges Want to See | How Our Frontend Delivers |
| :--- | :--- | :--- | :--- |
| **Technical Innovation & Depth** | 25% | Standardized Post-Quantum Cryptography & Multi-Layer Forensic Engineering | Interactive key explorer for `ML-KEM-768` (FIPS 203) and `ML-DSA-65` (FIPS 204), envelope encryption viewer, Tardos continuous score visualizer, and Bayesian fusion mathematical breakdown. |
| **Problem Statement Alignment** | 25% | Solves unauthorized document leakage with non-repudiation and immutable provenance | Clear visual flow: Enrolment $\rightarrow$ Multi-Recipient Release $\rightarrow$ Signed Decryption Provenance $\rightarrow$ Leak Attribution. |
| **Robustness & Adversarial Testing** | 20% | Does the system break under attack? Does it falsely accuse innocent users? | Dedicated **Adversarial Attack Lab** and fail-closed test matrix demonstrating explicit abstention (`ABSTAIN`, `NO_SIGNAL`, `INSUFFICIENT_EVIDENCE`, `CONFLICT`) on forgeries, tampering, and unwatermarked files. |
| **UI/UX & Operational Polish** | 15% | Professional, responsive, polished operator interface | Modern dark-mode cybersecurity theme, interactive ledger tamper simulator, responsive layout, intuitive visual graphs, clear data origin badges (`REAL_BACKEND_RESULT` vs `SIMULATED_DEMO_SCENARIO`). |
| **Live Demonstration Quality** | 15% | Flawless, convincing live execution without crashes | Dual-mode connectivity (live backend + offline-first mock fallback), step-by-step guided **Judge Walkthrough** with 1-click execution. |

---

## 3. Demo Time Budgets

### A. 3-Minute Lightning Pitch
- **0:00 - 0:30 (Context):** Explain the challenge of multi-recipient document distribution and the analog leak hole (screenshot/photo).
- **0:30 - 1:30 (Live Flow):** Run the 6-stage Judge Walkthrough (Enrolment $\rightarrow$ Release $\rightarrow$ Decrypt $\rightarrow$ Ledger $\rightarrow$ Leak Analysis).
- **1:30 - 2:30 (Adversarial Defense):** Demonstrate the Tamper-Evident Ledger tamper simulator and Fail-Closed abstention on forged markers.
- **2:30 - 3:00 (Impact & Wrap-up):** Export the Technical Evidence & Provenance Report and summarize PQC standardization.

### B. 7-Minute Deep-Dive Presentation
- **0:00 - 1:00:** Problem statement, threat model, and post-quantum necessity (FIPS 203/204).
- **1:00 - 2:30:** Live enrollment and multi-recipient hybrid envelope encryption (AES-256-GCM + ML-KEM-768).
- **2:30 - 3:30:** Decryption provenance event signing (ML-DSA-65) and immutable SHA-256 hash chaining.
- **3:30 - 4:30:** Live interactive attack on the ledger: tamper with a historical event block and demonstrate instant cryptographic verification failure.
- **4:30 - 5:30:** Leak ingestion and Multi-Channel Bayesian Evidence Fusion (Watermark + Tardos $Z_i$ + Signature + Ledger).
- **5:30 - 6:30:** Adversarial Attack Lab: Print-Scan-Camera perspective homography, JPEG re-encoding, and Tardos collusion resistance.
- **6:30 - 7:00:** Technical evidence report generation, mathematical verification breakdown, and Q&A.

---

## 4. Design Principles for Explainability

1. **Explicit Visual State Transitions:** Color-code all cryptographic states:
   - Green (`#10b981`): `ATTRIBUTED`, `VERIFIED`, `INTACT`
   - Red (`#ef4444`): `TAMPERED`, `INVALID`, `FAILED`
   - Yellow/Amber (`#f59e0b`): `ABSTAIN`, `INSUFFICIENT_EVIDENCE`, `CONFLICT`, `REVIEW_REQUIRED`
   - Blue/Cyan (`#38bdf8`): `ENCRYPTED`, `PQC-WRAPPED`, `SYNCHRONIZED`
   - Purple (`#a855f7`): `TARDOS_CODEWORD`, `BAYESIAN_FUSION`
2. **Instant "Show Me the Math" Tooltips:** Judges who want mathematical rigor can expand details to see exact LLR values, separation margin ($\Delta$), confidence formulas, and SHA-256 digest hex trees.
3. **Interactive "Tamper Me" Controls:** Giving judges an interactive button to deliberately break an event hash provides immediate, unforgettable experiential proof of tamper evidence.
4. **Unambiguous Origin Badges:** Every result explicitly displays whether it was computed live by the backend (`REAL_BACKEND_RESULT`), calculated locally in browser (`REAL_LOCAL_COMPUTATION`), or generated as part of a pre-set test scenario (`SIMULATED_DEMO_SCENARIO`).
