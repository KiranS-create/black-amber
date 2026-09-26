# SIH26237 — Master Live Demonstration Scripts

This document contains standardized live demonstration scripts for SIH26237 across four presentation contexts:
1. **30-Second Elevator Pitch**
2. **2-Minute Executive Walkthrough**
3. **5-Minute Competition Judge Live Demonstration**
4. **Technical Deep-Dive Walkthrough**

---

## 1. The 30-Second Elevator Pitch

> *"Traditional cybersecurity protects files until they are opened. The second an authorized recipient renders a sensitive document or prints it out, they can leak it anonymously with a smartphone photo.*
>
> *SIH26237 solves this: we combine NIST post-quantum cryptographic envelopes (`ML-KEM-768`), collusion-resistant Tardos traitor tracing, and optical physical watermarks into a fail-closed evidence fusion engine.*
>
> *When a leak occurs, our engine rectifies the image, extracts the forensic signal, and mathematically proves who leaked it—and if an attacker destroys the watermark, our zero-trust engine refuses to make a false accusation and cleanly abstains."*

---

## 2. The 2-Minute Executive Walkthrough

### **Timing & Flow**

- **0:00 – 0:30 (Problem Framing)**:
  - Open the Web Dashboard (`http://127.0.0.1:5173`).
  - *"We are looking at our air-gapped forensic dashboard. In traditional enterprise DRM, once Bob opens a defense brief and takes a smartphone photo, all digital DRM is gone."*

- **0:30 – 1:00 (Encrypted Release & Sovereign Provenance)**:
  - Click on **Distribution & Releases Tab**.
  - Show the 3 isolated release packages for Alice, Bob, and Charlie.
  - *"Our system encapsulates the document key independently for each recipient using NIST `ML-KEM-768`. When Bob decapsulates his release, his client signs a non-repudiable provenance ticket with `ML-DSA-65`, committing the event to an immutable audit ledger."*

- **1:00 – 1:30 (Leak Submission & Attribution)**:
  - Switch to **Leak Analysis Tab**.
  - Upload `bob_leak.pdf` (simulated smartphone camera capture).
  - Click **Analyze Leak**.
  - Show immediate result: **`ATTRIBUTED` $\to$ Bob** (Confidence: 14.2, Separation $\Delta = 8.4$).
  - *"The engine performs ArUco homography rectification, extracts the DSSS carrier, calculates Bob's Tardos traitor-tracing score, and outputs courtroom-defensible attribution."*

- **1:30 – 2:00 (Fail-Closed Zero-Trust Defense)**:
  - Upload `tampered_leak.pdf` (heavy crop + blur attack).
  - Click **Analyze Leak**.
  - Show result: **`INSUFFICIENT_EVIDENCE` / `CONFLICT`**.
  - *"Notice that under severe attack, the engine does not guess or convict an innocent party. It enforces a strict fail-closed policy and abstains."*

---

## 3. The 5-Minute Competition Judge Live Demonstration

### **Setup Requirements**
- Terminal 1: Backend running on `http://127.0.0.1:8000`.
- Terminal 2: Vite UI running on `http://127.0.0.1:5173`.
- Demo fixtures pre-generated in `data/demo_fixtures/`.

---

### **Step-by-Step Script & Actions**

#### **Step 1: System Readiness & Health (0:00 – 0:45)**
- **Presenter Action**: Open browser to `http://127.0.0.1:5173`. Point to header status indicators.
- **Spoken Script**:
  > *"Judges, before showing the workflow, notice that the entire platform is running 100% locally on this air-gapped machine. In the top bar, you see our NIST post-quantum primitives (`ML-KEM-768`, `ML-DSA-65`), our SQLite control plane, and our zero-cloud verified status. Let us start by examining our registered master document in the vault."*

#### **Step 2: Document Vault & Multi-Recipient Packaging (0:45 – 1:30)**
- **Presenter Action**: Navigate to **Documents Tab**. Show `DOC_DEFENSE_2026` with SHA-256 hash `a3c974c9...`. Click **Create Multi-Recipient Release**.
- **Spoken Script**:
  > *"When headquarters issues a classified whitepaper, our `ReleaseManager` generates an ephemeral 256-bit symmetric key. For each authorized recipient—Alice, Bob, and Charlie—the key is encapsulated using their sovereign `ML-KEM-768` public keys. Notice that each recipient receives a distinct encrypted envelope tied to their identity."*

#### **Step 3: Sovereign Decryption & Audit Ledger (1:30 – 2:15)**
- **Presenter Action**: Navigate to **Audit Ledger Tab**. Show the latest entry for Bob's decryption event.
- **Spoken Script**:
  > *"When Bob opens his release, his client decapsulates the key and signs a decryption provenance event with `ML-DSA-65`. This is committed into our SHA-256 Merkle hash-chained ledger. If Bob claims he never opened the document, the cryptographic signature and ledger entry refute that claim."*

#### **Step 4: The Physical Leak & Forensic Extraction (2:15 – 3:15)**
- **Presenter Action**: Switch to **Leak Analysis Tab**. Upload `data/demo_fixtures/bob_leak.pdf`. Click **Analyze Leak**.
- **Spoken Script**:
  > *"Now, Bob takes a smartphone photo of his printed document and leaks it anonymously online. All digital EXIF headers and PDF tags are stripped. We submit this raw, optically degraded file to our forensic pipeline.*
  >
  > *In 38 milliseconds, the engine executes four steps:*
  > *1. ArUco fiducial synchronization rectifies the 15-degree camera perspective tilt.*
  > *2. DSSS spatial demodulation recovers the raw symbol bitstream.*
  > *3. Reed-Solomon error correction eliminates optical sensor bit errors.*
  > *4. The Tardos engine computes the traitor-tracing likelihood across all enrolled candidates."*

#### **Step 5: Reviewing the Fused Evidence Graph (3:15 – 4:00)**
- **Presenter Action**: Scroll to the **Evidence Fusion Breakdown** card. Highlight the candidate separation score.
- **Spoken Script**:
  > *"Look at the evidence fusion breakdown. The engine does not simply add numbers together. It constructs an Evidence Dependency Graph. Because the Tardos score is derived from the spatial watermark, the engine applies our Transitive Derivation Lineage Bound:*
  > $$\text{Score}_{\text{cluster}} = \max(\text{Score}_{\text{WM}}, \text{Score}_{\text{Tardos}})$$
  > *This prevents artificial confidence inflation. Bob's fused score is 14.2 with a candidate separation margin $\Delta = 8.4$, far exceeding our minimum margin of 2.5. The engine safely issues an `ATTRIBUTED` verdict for Bob."*

#### **Step 6: Hostile Attack & Fail-Closed Abstention (4:00 – 4:45)**
- **Presenter Action**: Click **New Analysis**. Upload `data/demo_fixtures/tampered_leak.pdf` (heavily cropped + blurred). Click **Analyze Leak**.
- **Spoken Script**:
  > *"Now, what happens if an adversary attempts to defeat attribution by cropping the document and applying heavy Gaussian filtering?*
  >
  > *Look at the result: **`INSUFFICIENT_EVIDENCE`**. Our Attack-Aware Reliability module detected that the carrier was degraded beyond statistical confidence. Rather than framing an innocent recipient or guessing, the system strictly abstains. This is our zero-trust guarantee."*

#### **Step 7: Conclusion & Summary (4:45 – 5:00)**
- **Presenter Action**: Show the **Ledger Verification** badge (`100% Hash-Chain Valid`).
- **Spoken Script**:
  > *"In summary: SIH26237 bridges the physical leakage boundary with post-quantum cryptography, mathematical traitor tracing, and fail-closed evidence fusion. Thank you."*

---

## 4. Technical Deep-Dive Walkthrough (For Technical Judges)

### **Key Technical Questions to Address During Deep-Dive**

1. **How does Tardos scoring function on continuous bits?**
   - Point to `core/traceability/tardos.py`.
   - Explain the symmetric accumulator:
     $$U_{ic} = \sum_{j=1}^m \left[ y_j \cdot g_1(p_j) + (1 - y_j) \cdot g_0(p_j) \right]$$
   - Explain cutoff threshold $t = 1 / (300 c)$.

2. **How is double-counting prevented mathematically?**
   - Point to `core/attribution/fusion.py` $\to$ `EvidenceDependencyGraph`.
   - Walk through the traversal logic where parent-child lineages are clustered and bounded by $\max_{n \in \text{Tree}}(\rho_n \cdot \text{LLR}_n)$.

3. **How does ArUco homography rectification work?**
   - Point to `core/watermark/` $\to$ `cv2.findHomography` and `cv2.warpPerspective`.
   - Explain how 4 corner fiducials map any arbitrary quadrilateral capture back to a canonical $2480 \times 3508$ A4 pixel canvas.
