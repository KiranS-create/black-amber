# Traceability Architecture & Marker Binding

## 1. Traceability Provider Interface
The `TraceabilityProvider` interface provides a standardized abstraction for embedding, extracting, and verifying attribution signals across multiple carrier modalities:
- `issue_marker(...)`
- `embed_marker(...)`
- `extract_marker(...)`
- `verify_marker(...)`
- `get_evidence(...)`
- `estimate_confidence(...)`

## 2. Milestone v0.1: PrototypeTraceabilityProvider
- Binds recipient identity $R_i$, document identifier $D$, release identifier $Rel$, and document hash $H_{doc}$ into an HMAC-SHA256 authenticated payload.
- Embedded cleanly into document carrier layers.
- Full verification prevents forgery, tampering, and key-substitution attacks.

## 3. Milestone v0.2+ Roadmap: Tardos & Multi-Channel Fusion
- **Tardos Codes**: Collusion-resistant binary fingerprinting matrix generation with symmetric and asymmetric score functions.
- **Robust Secondary Channels**: Integration with StegaStamp / TrustMark visual watermarking channels.
- **Evidence Fusion Engine**: Multi-channel weighted correlation matrix producing unified evidence vectors.
