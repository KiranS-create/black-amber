# AegisTrace Device Identity Architecture

## 1. Executive Summary

AegisTrace establishes a cryptographically verifiable relationship between human identity, recipient authorization, interactive viewer sessions, device identity, platform hardware attestation, and downstream forensic evidence.

Crucially, AegisTrace rejects the flawed assumption that an IP address, hostname, MAC address, user-agent string, or browser fingerprint constitutes a device identity. In modern virtualized, mobile, and hostile enterprise environments, network indicators and client-reported strings are trivially spoofed, shared, or mutated. 

Instead, AegisTrace models **Device Identity** as an asymmetric cryptographic keypair rooted in hardware isolation (TPM 2.0, Apple Secure Enclave, Android StrongBox, or FIDO2 Security Keys), bound to a strict multi-tenant organizational perimeter and independent of human identity credentials.

---

## 2. Seven-Tier Principal Separation

AegisTrace rigorously maintains separation across seven distinct conceptual tiers:

```
Human Operator (Identity Provider / Enterprise Directory)
       ↓
Recipient Principal (Cryptographic Recipient: ML-KEM-768 + ML-DSA-65)
       ↓
Controlled Viewer Session (Time-Bounded Interaction: Nonce + Document Hash)
       ↓
Device Principal (Cryptographic Device Key Reference)
       ↓
Device Attestation State (Hardware Root of Trust Verification)
       ↓
Decryption / Export Event (Composite Receipt: Recipient Sig + Device Attestation)
       ↓
Forensic Attribution Evidence (Calibrated Multi-Channel Fusion)
```

| Security Concept | Definition | Cryptographic Primitive | Failure Impact |
| :--- | :--- | :--- | :--- |
| **AUTHENTICATED USER** | Enterprise human actor (e.g. employee, military officer). | OIDC / SAML / Kerberos identity assertion. | Directory outage; does NOT invalidate cryptographic evidence. |
| **RECIPIENT PRINCIPAL** | Opaque recipient holding post-quantum decryption keys. | ML-KEM-768 (KEM) + ML-DSA-65 (DSA). | Master decryption key compromise. |
| **DEVICE IDENTITY** | Stable, opaque device identifier bound to an asymmetric key. | NIST P-256 / RSA-2048 / ML-DSA-65. | Unregistered device access rejection. |
| **ATTESTED DEVICE** | Device whose key possession and platform state are hardware-verified. | TPM 2.0 Quote / Apple App Attest / StrongBox / FIDO2. | Fails closed on untrusted or tampered firmware. |
| **UNATTESTED DEVICE** | Enrolled device with software-only key storage. | OS Keystore / Software fallback keypair. | Permitted in STANDARD mode; blocked in HIGH_ASSURANCE mode. |
| **COMPROMISED DEVICE** | Device flagged for key mismatch, impossible travel, or revocation. | Administrative revocation / Tamper detection. | Immediate global block on all operations. |
| **UNKNOWN DEVICE** | Unenrolled device presenting unauthorized requests. | No registered public key. | Hard rejection at boundary. |

---

## 3. Separation of Powers: Recipient vs. Device

A central architectural invariant of AegisTrace is the **Separation of Powers**:

1. **Recipient Authorization** is proven **only** by the recipient's post-quantum signature (ML-DSA-65) over the document decryption/export receipt. A device cannot sign on behalf of the recipient.
2. **Device Platform Trust** is proven **only** by hardware attestation (TPM quote, Secure Enclave receipt) proving platform integrity, secure boot, and non-extractable key storage. An attested device cannot claim recipient intent without the recipient's signature.
3. Conflating the two would create severe forensic vulnerabilities:
   - A compromised software emulator could forge user actions.
   - An attested hardware kiosk used by multiple employees could frame an innocent user if device presence were treated as human authorization.

---

## 4. Multi-Tenant Isolation Architecture

Every `DevicePrincipal` and `AttestationChallenge` is strictly partitioned by `organization_id`:

- **Namespace Isolation**: Device lookups and challenge evaluations use composite keys `(organization_id, device_id)`.
- **Cross-Tenant Rejection**: A challenge nonce created for `org_energy` presented by a device in `org_defense` is rejected immediately (`ORGANIZATION_MISMATCH`).
- **No Shared Device Assumptions**: If two organizations register a device with the same identifier, their cryptographic public keys, key epochs, and attestation states remain completely independent.

---

## 5. Key Rotation & Lifecycle State Machine

Each device maintains an administrative lifecycle status and a cryptographic `key_epoch`:

```
                 [ REGISTER ]
                      ↓
                  [ ACTIVE ] <----------------+
                   │      │                   │
     Admin Suspend │      │ Rotate Key        │ Reactivate
                   ↓      ↓                   │
              [ SUSPENDED ] (epoch++)         │
                   │                          │
                   +--------------------------+
                   │
                   │ Security Compromise / Decommission
                   ↓
              [ REVOKED ] (Permanent Tombstone)
```

- **Revocation Immutability**: Once a device enters `REVOKED`, it can never be reactivated, re-enrolled, or assigned new sessions.
- **Historical Non-Repudiation**: Revoking a device today does **not** invalidate historical decryption receipts or DLT ledger commitments made while the device was active.
