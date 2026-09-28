# AegisTrace: Decryption Receipt Format Specification

## 1. Specification Overview

The `DecryptionReceipt` is the non-repudiable cryptographic commitment generated at decryption time. It binds the exact recipient, document root, session, export copy, watermark commitment, and key epoch into a canonical, signed structure committed to the permissioned DLT.

```json
{
  "receipt_id": "rcpt_evt_exp_cpy_b8644f94_df0f8f10",
  "document_root_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "recipient_id": "rec_alice_4a12",
  "identity_reference": "alice@defense.gov",
  "decryption_session_id": "ses_alice_982f1b",
  "decryption_event_id": "evt_exp_cpy_b8644f94_df0f8f10",
  "copy_instance_id": "cpy_b8644f9421a9",
  "watermark_commitment": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "watermark_token": "c565e91f0982bb19302e1a84f3956102847291a0b38192847192837192839182",
  "timestamp": "2026-09-27T10:30:00Z",
  "parent_lineage_reference": "cpy_root_1049281a",
  "recipient_public_key_b64": "MIIB...",
  "recipient_signature_b64": "k9A2...",
  "nonce": "9f82ab749102c48192a0194829103841",
  "metadata": {
    "export_format": "IMAGE",
    "child_copy_id": "cpy_b8644f9421a9"
  }
}
```

---

## 2. Field Definitions

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `receipt_id` | String | Unique receipt ID prefixed with `rcpt_`. |
| `document_root_hash` | String (Hex 64) | SHA-256 canonical hash of the master document root. |
| `recipient_id` | String | Opaque stable RecipientPrincipal identifier (e.g. `rec_alice_4a12`). |
| `identity_reference` | String | Email or external directory handle for post-attribution resolution. |
| `decryption_session_id`| String | Unique access session ID during which decryption occurred. |
| `decryption_event_id` | String | Unique event ID generated for this specific decryption operation. |
| `copy_instance_id` | String | Active lineage copy instance identifier. |
| `watermark_commitment`| String (Hex 64) | Salted SHA-256 commitment of the dynamic watermark token. |
| `watermark_token` | String (Hex 64) | Revealed dynamic watermark token (committed upon verified export). |
| `timestamp` | String (ISO-8601)| UTC timestamp when the receipt was signed. |
| `parent_lineage_reference`| String / Null | Parent copy ID in the derivation DAG (null for root copy). |
| `recipient_public_key_b64`| String (Base64) | Public key of the recipient (NIST FIPS 204 ML-DSA-65). |
| `recipient_signature_b64` | String (Base64) | Digital signature produced by recipient's private key. |
| `nonce` | String (Hex 32) | 128-bit cryptographic anti-replay nonce. |
| `metadata` | Object | Arbitrary contextual telemetry (format, resolution, device key). |

---

## 3. Canonical Payload Bytes Construction

For deterministic signature generation and cross-platform verification, the canonical message string $\mathcal{M}$ is constructed with strict domain separation:

```python
canonical_msg = (
    f"AEGIS-DECRYPTION-RECEIPT:v1:"
    f"receipt={receipt_id}:"
    f"doc_root={document_root_hash}:"
    f"rec={recipient_id}:"
    f"ses={decryption_session_id}:"
    f"evt={decryption_event_id}:"
    f"cpy={copy_instance_id}:"
    f"commit={watermark_commitment}:"
    f"token={watermark_token or ''}:"
    f"ts={timestamp}:"
    f"parent={parent_lineage_reference or 'ROOT'}:"
    f"nonce={nonce}"
).encode('utf-8')
```

### Signature Generation
$$\sigma \gets \text{ML-DSA-65.Sign}(sk_{\text{rec}}, \text{canonical\_msg})$$
$$\text{recipient\_signature\_b64} \gets \text{Base64Encode}(\sigma)$$

### Signature Verification
$$\text{isValid} \gets \text{ML-DSA-65.Verify}(pk_{\text{rec}}, \text{canonical\_msg}, \sigma)$$

Any modification to any field—such as altering the `document_root_hash`, swapping the `recipient_id`, or tampering with the `timestamp`—will immediately cause `ML-DSA-65.Verify` to return `False`.
