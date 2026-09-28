# AegisTrace: Watermark Forensic Verification & Leak Attribution

## 1. Investigative Workflow Overview

When an unauthorized document leak occurs, the forensic investigator submits the leaked artifact (image capture, scanned printout, screen photo, or exported digital file) into the AegisTrace Forensic Pipeline.

The investigator **does not** specify the suspect's name or pre-select a recipient. The forensic engine derives the candidate autonomously from cryptographic evidence:

```
[ Leaked Document Artifact ]
             |
             v
+-----------------------------------------------------------+
| 1. GEOMETRIC RECTIFICATION & DSSS DEMODULATION            |
| - ArUco marker detection & homography warp                |
| - Matched-filter carrier demodulation                     |
| - Reed-Solomon error correction                           |
| - Recovers 128-symbol dynamic codeword c                  |
+----------------------------+------------------------------+
                             |
                             v
+-----------------------------------------------------------+
| 2. OFFLINE PERMISSIONED DLT CORRELATION                   |
| - Scans finalized blocks across independent nodes         |
| - Matches codeword against derived candidate tokens       |
| - Locates canonical DecryptionReceipt R                   |
+----------------------------+------------------------------+
                             |
                             v
+-----------------------------------------------------------+
| 3. POST-QUANTUM CRYPTOGRAPHIC VERIFICATION                |
| - Verifies Recipient ML-DSA-65 Signature on Receipt R     |
| - Verifies Merkle Inclusion Proof in Block B              |
| - Verifies Multi-Validator BFT Quorum Signatures          |
| - Verifies Block Header Hash Chain Linkage                |
+----------------------------+------------------------------+
                             |
                             v
+-----------------------------------------------------------+
| 4. LINEAGE GRAPH & VISUAL EQUIVALENCE AUDIT               |
| - Traces ancestor tree: DocumentRoot -> Copy_0 -> Copy_1  |
| - Validates derivation depth & device binding             |
| - Computes SSIM & PSNR against pristine master            |
+----------------------------+------------------------------+
                             |
                             v
+-----------------------------------------------------------+
| 5. ENTERPRISE IDENTITY RESOLUTION                         |
| - Resolves opaque RecipientPrincipal to Human Identity    |
| - Queries pluggable IdentityProvider / cached directory   |
| - Emits fail-closed, honest attribution report            |
+-----------------------------------------------------------+
```

---

## 2. Fail-Closed Forensic State Machine

To prevent false accusations, the forensic engine strictly adheres to a fail-closed status model:

| Status | Trigger Condition | Forensic Meaning |
| :--- | :--- | :--- |
| `PROVEN_AUTHENTIC` | Watermark recovered, DLT receipt located, recipient ML-DSA-65 signature verified, DLT quorum verified, Merkle proof valid, lineage valid. | **Cryptographically Proved**: The identified recipient executed this exact decryption event. |
| `ABSENT_OR_DESTROYED` | ArUco markers destroyed, heavy cropping, excessive blur, or unwatermarked document. | **No Signal**: Inconclusive evidence; no recipient attribution possible. Engine abstains. |
| `INVALID_SIGNATURE` | Receipt located on ledger, but recipient ML-DSA-65 signature fails cryptographic verification. | **Forgery / Tampering**: Signature does not match registered recipient public key. Engine abstains. |
| `UNAUTHORIZED_LEDGER`| Watermark recovered, but no matching finalized receipt found on the permissioned DLT, or block lacks validator quorum. | **Rogue / Sub-Quorum**: Decryption not authorized by offline consensus. Engine abstains. |
| `TAMPERED_DERIVATION`| Lineage graph reveals broken parent hash, missing ancestor edge, or cycle. | **Lineage Inconsistency**: History has been tampered with. Engine abstains. |
| `SUSPECT_TRANSPLANT` | Codeword matches recipient, but document root hash in receipt does not match the leaked document content. | **Collusion / Cut-and-Paste**: Watermark was transplanted from another document. Engine flags contradiction. |

---

## 3. The Honesty Invariant

In high-stakes forensic security, an algorithmic claim must never overstate evidentiary certainty:

### What Is Cryptographically Proved:
$$\text{PROVED}: \text{Recipient } R \text{ (holding private key } sk_{\text{dsa}}\text{) executed decryption event } E \text{ on document } D \text{ at timestamp } T.$$

### What Is NOT Automatically Proved:
$$\text{NOT AUTOMATICALLY PROVED}: R \text{ personally emailed, uploaded, or physically handed the leaked copy to an adversary.}$$

Downstream leaks can occur through malware on $R$'s workstation, shoulder surfing, physical theft of a printed page from $R$'s desk, or unauthorized secondary forwarding. 

AegisTrace explicitly outputs this boundary declaration in every forensic attribution report, providing judges, investigators, and incident response teams with unimpeachable, scientifically sound evidence.
