# SIH26237 — Speaker Delivery Notes & Presenter Guide

**Deck Title:** Post-Quantum Leak Attribution for Documents  
**Target Delivery Window:** 8 to 10 Minutes (Strictly timed for competition panels)  

---

## Slide 1: Title & Value Proposition (0:00 – 0:45)

### **What to Say:**
- *"Good morning, respected judges. Today we are presenting SIH26237: a post-quantum leak attribution framework designed to trace sensitive documents from the moment of encrypted release all the way across the physical leakage boundary."*
- *"Enterprise security today spends billions protecting files in transit and at rest. But the moment an authorized executive or contractor opens that document on their monitor or prints it out on paper, all digital encryption evaporates. If they take a photo with a smartphone, the file is leaked anonymously."*
- *"SIH26237 solves this by binding post-quantum cryptographic trust, collusion-resistant Tardos traitor tracing, and optical physical watermarks into a fail-closed evidence fusion architecture."*

### **Key Emphasis Points:**
- Emphasize that the system **does not rely on one magical watermark**.
- Use the exact phrase: *"From encrypted release to physical-capture traceability."*

### **What NOT to Say:**
- ❌ Do NOT say: *"Our watermark is unbreakable and impossible to remove."*
- ❌ Do NOT say: *"We guarantee 100% identification under any attack."*

---

## Slide 2: The Physical Leakage Boundary Problem (0:45 – 1:30)

### **What to Say:**
- *"Let us examine why conventional Digital Rights Management (DRM) fails."*
- *"When you send an encrypted PDF, all recipients share either the same decrypted plaintext or the server manages symmetric keys. Once Bob opens the document, his display renders raw pixels."*
- *"Bob points a smartphone camera at the screen or paper printout. The resulting photo has perspective tilt, sensor noise, downsampling, and non-uniform room lighting. Furthermore, all EXIF metadata and digital headers are stripped."*
- *"Standard watermarks fail here: high-frequency spatial marks are destroyed by optical blur, while low-frequency watermarks alter the visual aesthetics of sensitive intelligence documents."*

### **Key Emphasis Points:**
- Acknowledge that the "analog hole" is an established physical reality.
- Frame our work as a rigorous **engineering response** combining geometric homography, DSSS modulation, and multi-channel fusion.

---

## Slide 3: Threat Model & Defense Matrix (1:30 – 2:30)

### **What to Say:**
- *"We designed our threat model around six distinct adversarial personas."*
- *"Against the **Malicious Recipient**, we embed an individualized Tardos codebook."*
- *"Against **Colluding Coalitions** who combine multiple legitimate copies to erase marks, we implement Symmetric Tardos codes with a formal false accusation bound of $\epsilon_1 = 10^{-4}$."*
- *"Against **Physical Capture** and camera tilt, we embed four-corner ArUco fiducials for homography rectification alongside Reed-Solomon error correction."*
- *"Against **Artifact Tampering** like aggressive cropping or blurring, our engine dynamically scales down channel reliability."*
- *"And against **Evidence Poisoning or Replay**, our evidence graph strictly deduplicates repeated signals and verifies ML-DSA digital signatures on a Merkle hash-chained ledger."*

---

## Slide 4: System Architecture (2:30 – 3:30)

### **What to Say:**
- *"Here is the complete end-to-end architecture of SIH26237."*
- *"The lifecycle begins at the `ReleaseManager`. For a registered master document, the authority generates an ephemeral symmetric key $K_{\text{doc}}$ and encapsulates it independently for each recipient using NIST `ML-KEM-768`."*
- *"When Bob decapsulates and decrypts his release package, his client signs a sovereign provenance ticket with `ML-DSA-65`, committing the event to our tamper-evident ledger."*
- *"His rendered document contains an individualized physical watermark carrying his Tardos fingerprint."*
- *"When an unauthorized leak occurs, our forensic pipeline rectifies the geometry, extracts multi-channel observations, and feeds them into our Multi-Channel Evidence Fusion Engine."*

---

## Slide 5: Cryptographic Trust Layer (3:30 – 4:30)

### **What to Say:**
- *"Let us highlight the cryptographic foundation. We implement current NIST standardized post-quantum algorithms:"*
- *"`ML-KEM-768` (FIPS 203) for key encapsulation, taking just 11.6 milliseconds in our measured benchmarks."*
- *"`ML-DSA-65` (FIPS 204) for digital signatures, verifying in under 21 milliseconds."*
- *"Authenticated symmetric envelopes using `AES-256-GCM` with strict target binding to `(document_id, release_id, recipient_id, payload_hash)`."*
- *"Crucially, our architecture enforces **Sovereign Recipient Key Custody**. The distribution server never generates or holds private keys, ensuring true non-repudiation."*

### **What NOT to Say:**
- ❌ Do NOT say: *"Our system is quantum-proof forever."*
- ✅ Say: *"It uses NIST-standardized post-quantum algorithms to guard against 'harvest now, decrypt later' threats."*

---

## Slide 6: Tardos Traitor-Tracing & Physical Carrier (4:30 – 5:30)

### **What to Say:**
- *"It is essential to understand the clean separation of responsibilities in our design:"*
- *"**Tardos is the WHO**: It provides the mathematical proof of identity and collusion resistance."*
- *"**The Watermark Carrier is the HOW**: It ensures that the Tardos symbol bitstream survives the hostile physical and optical channel."*
- *"We implement a dynamic `TardosCapacityPlanner` that calculates the exact code length $m$ based on the document carrier's capacity."*
- *"The bitstream is protected by Reed-Solomon error correction and DSSS spatial modulation, framed by ArUco fiducials that rectify camera perspective distortion up to 30 degrees."*
- *"Note: Our automated test benchmarks currently measure simulated optical channels, and our repository includes a complete physical laboratory ingestion harness ready for hardware validation."*

---

## Slide 7: Adversarial Attack Laboratory (5:30 – 6:30)

### **What to Say:**
- *"To validate robustness, we built an automated Adversarial Attack Laboratory that stress-tests the carrier across digital, geometric, PDF, and simulated physical transformations."*
- *"Under moderate JPEG compression, resizing, and optical tilt, the ArUco homography and Reed-Solomon ECC cleanly recover the signal with 0.0% post-ECC bit error rate."*
- *"When an attacker applies extreme destruction—such as cropping more than 30% of the carrier—the signal is destroyed. But here is the critical engineering feature: **the engine does not guess or frame an innocent person; it strictly abstains**."*

---

## Slide 8: Multi-Channel Evidence Fusion (6:30 – 7:30)

### **What to Say:**
- *"Slide 8 represents our primary algorithmic innovation: the Multi-Channel Evidence Fusion Engine."*
- *"In conventional forensic tools, if you find a watermark and compute a Tardos score from that same watermark, naively adding both scores double-counts the evidence and creates false certainty."*
- *"We solve this by constructing an **Evidence Dependency Graph**. Derived observations are bounded by the **Maximum Evidentiary Bound**: $\max_{n \in \text{Tree}}(\rho_n \cdot \text{LLR}_n(c))$. A child signal cannot artificially amplify its parent."*
- *"Furthermore, if two channels strongly contradict each other, the engine transitions to `CONFLICT`. If evidence is weak, it transitions to `INSUFFICIENT_EVIDENCE`."*

---

## Slide 9: Turnkey Live Demo (7:30 – 8:30)

### **What to Say:**
- *"We will now demonstrate the system live. We have three demo modes: our interactive web dashboard, a deterministic Python runner, and a CLI fallback."*
- *(Proceed through the 3-minute demo script: Register Document $\to$ Create Alice/Bob/Charlie Releases $\to$ Decrypt as Bob $\to$ Submit Bob's Leak $\to$ Show Attribution $\to$ Submit Tampered Leak $\to$ Show Fail-Closed Abstention).*

---

## Slide 10: Measured Benchmarks & Empirical Telemetry (8:30 – 9:15)

### **What to Say:**
- *"Every metric on this slide is directly backed by automated benchmark scripts in our repository."*
- *"Cryptographic encapsulation runs in 11.6 milliseconds; total watermark decode latency is under 67 milliseconds."*
- *"In our 200-scenario synthetic evaluation harness with a 100-scenario held-out evaluation split, the system achieved a 74.0% decision state match rate under extreme adversarial multi-attack corruptions with **zero false accusations** against innocent parties."*
- *"Our deployment starts in under 350 milliseconds with 100% of our 39 automated integration tests passing."*

### **Key Emphasis Points:**
- Explicitly explain the 74% figure: it measures decision state matching across high-noise adversarial stress tests, demonstrating that the engine safely abstains under extreme corruption.

---

## Slide 11: Boundaries, Future Roadmap & Conclusion (9:15 – 10:00)

### **What to Say:**
- *"In conclusion, we maintain strict scientific honesty regarding our current boundaries. Physical printing validation is structured via our ingestion harness, and parameter scaling follows conservative heuristic bounds."*
- *"Our system is designed with one unwavering principle:*
  ***To attribute when evidence is mathematically overwhelming — and fail-closed with complete integrity when it is not.***"
- *"Thank you, and we are ready for your questions."*
