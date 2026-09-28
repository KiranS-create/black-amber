# AegisTrace Federated Identity Directory Architecture at Scale

## 1. Forensic Decoupling & Security Invariants

In high-consequence forensic investigations, identity resolution must be strictly separated from cryptographic attribution:
1. **Autonomous Attribution**: The cryptographic attribution engine derives the candidate `recipient_id` solely from mathematical evidence (embedded watermark markers, KEM decapsulation receipts, and ML-DSA-65 signed provenance ledger events).
2. **No Operator Bias**: An investigator or operator cannot query or guide the attribution engine by inputting a suspect employee's name or email.
3. **Post-Attribution Directory Resolution**: Human enterprise metadata (full name, department, title, manager, email) is resolved **after** cryptographic attribution has conclusively identified the `recipient_id`.
4. **Availability Decoupling**: If external enterprise directory services (Microsoft Entra ID, Okta, LDAP) are offline, unreachable, or network-partitioned, the cryptographic attribution **does not fail**. It produces attribution with `resolution_status="PENDING"` or `source="CACHE"` rather than aborting.

---

## 2. Four-State Cache Lifecycle State Machine

To guarantee resilience during cloud outages, network air-gaps, or remote field operations, AegisTrace implements a deterministic four-state cache lifecycle:

```
                  +-----------------------------------+
                  |          DIRECTORY QUERY          |
                  +-----------------------------------+
                                    |
                    +---------------+---------------+
                    |                               |
              [Cache Hit]                     [Cache Miss]
                    |                               |
        +-----------+-----------+                   |
        |                       |                   v
  [Age <= TTL]             [Age > TTL]     [Directory Online?]
        |                       |          /                 \
        v                       v        [Yes]               [No]
    +-------+               +--------+     |                  |
    | FRESH |               | CACHED |     v                  v
    +-------+               +--------+  +-------+      +-------------+
        |                       |       | FRESH |      | UNAVAILABLE |
        |                       v       +-------+      +-------------+
        |                 [Age > Stale]                       |
        |                       |                             v
        |                       v                    Status: "PENDING"
        |                   +-------+               (Crypto Attribution
        +------------------>| STALE |                    Preserved)
                            +-------+
```

### State Definitions
- **`FRESH`**: Record retrieved within primary TTL ($\le 1\text{ hour}$). Maximum confidence metadata.
- **`CACHED`**: Record past primary TTL but within stale window ($1\text{ hour} - 24\text{ hours}$). Served during transient network glitches.
- **`STALE`**: Record older than $24\text{ hours}$, directory still unreachable. Served with forensic advisory note indicating historical cache.
- **`UNAVAILABLE`**: No cache entry exists and external IdP is down. Returns `resolution_status="PENDING"`. Cryptographic recipient binding remains 100% valid and verified.

---

## 3. Stable Opaque Identity Surrogate Invariant

Enterprise directory attributes are inherently mutable:
- Employees change legal names (marriage, divorce).
- Employees change email addresses (domain migrations, alias updates).
- Employees transfer between business divisions and departments.
- Employees are suspended, revoked, or deprovisioned.

If forensic systems bind evidence directly to human emails (`alice@corp.com`), subsequent renames or account reassignments break historical chain-of-custody proofs.

### AegisTrace Binding Invariant
- **`identity_id`**: An opaque, globally unique surrogate key (`usr_9a8b7c6d`) generated upon initial enrollment.
- **`recipient_id`**: A cryptographic principal (`rec_1a2b3c4d`) binding post-quantum public keys (ML-KEM-768, ML-DSA-65) to `identity_id`.
- When an employee updates their email or department in Okta / Entra ID, only the directory metadata record is refreshed; the underlying `identity_id` and cryptographic `recipient_id` remain permanently immutable.
- Deprovisioned or revoked identities retain historical auditability in the ledger.
