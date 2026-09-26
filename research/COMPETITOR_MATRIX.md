# Competitor & Prior Art Comparison Matrix

| Feature / Dimension | Traditional DRM / Watermarking | Competitor SIH Teams | SIH26237 (Our Architecture) |
| :--- | :--- | :--- | :--- |
| **Post-Quantum Security** | None (RSA/ECC) | Rare / Incomplete | **ML-KEM-768 + ML-DSA-65 Standardized** |
| **Document Key Encapsulation** | Re-encrypt entire file per recipient | Inefficient full encryption | **Single AES-256-GCM + Per-Recipient KEM Wrap** |
| **Decryption Provenance** | Centralized server logs | Unsigned client reports | **Hash-Chained Tamper-Evident Ledger + Recipient Signatures** |
| **Attribution Logic** | Heuristic / Forced matching | Single-channel fragile tag | **Multi-Source Evidence Fusion (Fail-Closed ABSTAIN)** |
| **Collusion Resistance** | None | Absent | **Planned Tardos Fingerprinting (v0.2)** |
| **Adversarial Robustness** | Fails on metadata strip | Overclaims robustness | **Validated Fail-Closed & Attack Benchmark Suite** |
