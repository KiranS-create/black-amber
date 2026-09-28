# AegisTrace Platform Architecture & Design Specification

> **Platform Designation**: AegisTrace Web Forensic Workstation  
> **Platform Status**: Production Web Application & Standalone Offline Auditor. Standalone desktop applications (Windows `.exe`, macOS `.dmg`) and Android mobile packaging are **DEFERRED TO FUTURE WORKSTREAM**.

---

## 1. System Topology & Layering

AegisTrace decouples deep post-quantum cryptographic primitives from user experience through a progressive disclosure architecture:

```mermaid
flowchart TD
    subgraph UI Layer [User Experience (The Car Controls)]
        A[Operator Workstation] --> B[Overview]
        A --> C[Documents / Import]
        A --> D[Releases / Distribute]
        A --> E[Investigations / Analyze]
        A --> F[AegisTrace Verify]
    end

    subgraph Abstraction Layer [Semantic Services]
        G[ArtifactService]
        H[ProtectionService]
        I[InvestigationService]
        J[VerificationService]
    end

    subgraph Engine Layer [Cryptographic Core]
        K[NIST FIPS 203 ML-KEM-768]
        L[NIST FIPS 204 ML-DSA-65]
        M[AES-256-GCM + HKDF]
        N[Tardos Traitor Tracing]
        O[Bayesian LLR Evidence Fusion]
        P[RFC 6962 DLT Merkle Chain]
    end

    UI Layer --> Abstraction Layer
    Abstraction Layer --> Engine Layer
```

---

## 2. Frontend Layer (React 18 / TypeScript / Vite)

The frontend is engineered as a zero-dependency, high-reliability single-page application:
- **Theme Engine**: Dynamic forensic dark/light workstation palette (`ThemeContext.tsx`) with high-contrast evidentiary typography.
- **Progressive Disclosure**: High-level actions (Import, Protect, Investigate, Verify) are prominently displayed. Technical details (KEM ciphertexts, Merkle paths, LLR equations) remain concealed inside expandable `[Technical details]` accordions.
- **Standalone AegisTrace Verify**: A completely zero-server offline audit workstation allowing examiners to audit evidence packages without network connectivity or backend availability.

---

## 3. Backend & Cryptographic Engine (FastAPI / Python 3.11)

### 3.1 Post-Quantum Cryptography (PQC)
- **Key Encapsulation Mechanism (KEM)**: NIST FIPS 203 ML-KEM-768 generates unique ephemeral symmetric keys for each recipient.
- **Digital Signatures**: NIST FIPS 204 ML-DSA-65 signs all release events, decryption receipts, and forensic manifests.
- **Symmetric Encryption**: AES-256-GCM authenticated encryption ensures confidentiality and tamper detection.

### 3.2 Collusion-Resistant Traitor Tracing (Tardos Code)
- Generates optimal length Tardos fingerprinting codes using symmetric score functions.
- Accommodates up to $c=3$ colluding adversaries who attempt to combine multiple copies to strip watermarks.

### 3.3 Bayesian Evidence Fusion
- Multi-channel log-likelihood ratio (LLR) aggregation across:
  1. Spatial DSSS watermark carrier
  2. Tardos traitor tracing matrix
  3. ML-DSA-65 post-quantum signature verification
  4. Immutable audit ledger tamper state
- **Directed Acyclic Graph (DAG)** prevents statistical double-counting.
- **Fail-Closed Decision Guard**: If the separation margin between the top suspect and second suspect $\Delta < 2.50$, the system explicitly outputs `ABSTAINED` rather than accusing an innocent party.

---

## 4. Storage Architecture

- **`data/` (SQLite WAL)**: High-speed relational storage for identities, recipient keys, and append-only hash chains.
- **`artifacts/` (Content-Addressed)**: Document payloads and evidence packages addressed by their SHA-256 digests.
- **Zero Fake Data Invariant**: Clean initial state on fresh deployment; demo records strictly quarantined within `demo_tenant`.
