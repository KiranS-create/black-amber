# SIH26237 Presentation Storyboard & Pitch Narrative

## Slide Structure
1. **Title & Problem Statement**:
   - The insider threat & confidential multi-recipient distribution dilemma.
2. **Threat Model & Real-World Attack Scenarios**:
   - Screenshot leaks, print-and-scan, collusive reconstruction, and repudiation.
3. **Official Requirements & Gap Analysis**:
   - Why traditional DRM and basic watermarks fail post-breach attribution.
4. **End-to-End System Architecture**:
   - Hybrid post-quantum envelope encryption (ML-KEM-768 + AES-256-GCM).
5. **Decryption Provenance & Tamper-Evident Ledger**:
   - Cryptographically signed decryption events anchored in a hash-chained ledger.
6. **Traceability & Evidence Fusion Engine**:
   - Multi-source correlation: Tardos codes + visual channel + provenance chain.
7. **Fail-Closed Attribution & Adversarial Defenses**:
   - Zero false accusations: why forged/altered evidence produces ABSTAIN.
8. **Attack Laboratory & Quantitative Benchmarks**:
   - Robustness under compression, filtering, cropping, and noise.
9. **Live System Demonstration**:
   - Alice, Bob, Charlie distribution $\rightarrow$ Bob decrypts $\rightarrow$ Leak analyzed $\rightarrow$ Bob attributed.
10. **Deployment, Air-Gap Readiness & National Security Impact**:
    - High-throughput defense, government, and enterprise document security.
