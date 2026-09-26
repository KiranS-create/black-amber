# Security Policy

## Threat Model Overview
SIH26237 provides post-quantum cryptographic envelope encryption, multi-recipient key encapsulation, and tamper-evident decryption provenance.

### Core Security Guarantees
1. **Confidentiality**: Ephemeral 256-bit AES-GCM keys encapsulated per recipient using Post-Quantum KEM (`ML-KEM-768`).
2. **Provenance & Non-Repudiation**: Recipient decryption generates a signed event logged to a hash-chained tamper-evident ledger.
3. **Fail-Closed Attribution**: If evidence is missing, altered, forged, or unauthenticated, the attribution engine returns `ABSTAIN` / `INSUFFICIENT_EVIDENCE` rather than falsely accusing innocent recipients.
4. **Key Isolation**: Recipient private keys are strictly local and never exposed or stored on the distribution server.

## Reporting a Vulnerability
Please report any security findings or vulnerability reports to the project maintainers.
