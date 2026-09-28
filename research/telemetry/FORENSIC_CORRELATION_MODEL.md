# AegisTrace Forensic Correlation Model

## 1. Mathematical & Graph Formulation

AegisTrace models external forensic correlation as a directed attributed property graph $\mathcal{G} = (\mathcal{V}, \mathcal{E})$, where vertices $\mathcal{V}$ represent entities and events, and directed edges $\mathcal{E}$ represent causal, cryptographic, or operational transitions.

### 1.1 Node Types ($\mathcal{V}$)
The correlation engine supports 10 strongly-typed node classes:
1. `DOCUMENT`: Canonical original document prior to recipient distribution.
2. `COPY`: Cryptographically bound recipient-specific copy (possessing watermark payload $W_i$ and Tardos codeword $X_i$).
3. `IDENTITY`: Verified enterprise or enrolled human identity.
4. `ACCOUNT`: System or cloud account credential (e.g. `alice@corp.com`, AWS IAM ARN).
5. `DEVICE`: Hardware workstation, server, laptop, external drive, or printer.
6. `SESSION`: Authenticated login window or token session.
7. `EVENT`: Discrete telemetry action (file write, network flow, print job).
8. `NETWORK`: IP address, CIDR subnet, VPN egress node, or Tor exit.
9. `EXTERNAL_ARTIFACT`: Leaked file, dump snippet, or public paste.
10. `LOCATION`: Physical office room, turnstile, or building zone.

### 1.2 Edge Types ($\mathcal{E}$)
Transitions are strictly typed across 10 directional relationships:
1. $\text{RELEASED\_TO} : \text{COPY} \to \text{IDENTITY}$ (Authorized initial distribution)
2. $\text{ACCESSED\_BY} : \text{COPY} \to \text{ACCOUNT}$ (Observed account access)
3. $\text{RENDERED\_ON} : \text{COPY} \to \text{DEVICE}$ (Endpoint in-memory rendering)
4. $\text{EXPORTED\_BY} : \text{COPY} \to \text{EVENT}$ (Export, copy, or print action)
5. $\text{COPIED\_BY} : \text{EVENT} \to \text{DEVICE}$ (Copy to peripheral / USB)
6. $\text{WRITTEN\_TO} : \text{EVENT} \to \text{DEVICE}$ (File write operation)
7. $\text{TRANSMITTED\_TO} : \text{EVENT} \to \text{NETWORK}$ (Outbound network flow)
8. $\text{UPLOADED\_FROM} : \text{EXTERNAL\_ARTIFACT} \to \text{ACCOUNT}$ (Public drop upload)
9. $\text{CORRESPONDS\_TO} : \text{EXTERNAL\_ARTIFACT} \to \text{COPY}$ (Artifact watermark match)
10. $\text{DERIVED\_FROM} : \text{COPY} \to \text{DOCUMENT}$ (Original derivation)

---

## 2. Temporal Correlation & Causal Predecessor Invariants

### 2.1 Causal Ordering & Clock Skew Compensation
In physical systems, an effect cannot precede its cause. If event $e_2$ is causally downstream of $e_1$, the observed timestamps $t(e_1)$ and $t(e_2)$ must satisfy:
$$t(e_2) \ge t(e_1) - \Delta t_{\text{skew}}$$
where $\Delta t_{\text{skew}}$ is the allowable clock skew tolerance across non-NTP-synchronized network endpoints (default: 30.0s to 60.0s).

If $t(e_2) - t(e_1) < -\Delta t_{\text{skew}}$, the engine flags an irrecoverable `CAUSAL_VIOLATION`. This invalidates the hypothesis that $e_1$ caused $e_2$, preventing an adversary from spoofing chronological logs to forge an alibi.

### 2.2 Deduplication Without Score Inflation
A single physical action (e.g. user copying a file to an external USB stick) frequently triggers alerts across multiple sensors simultaneously:
- EDR logs a `FILE_WRITE`
- DLP generates a `POLICY_ALERT`
- Windows Event Log records an `EVENT_ID_4663`
- Hardware bus driver logs a `USB_MASS_STORAGE_MOUNT`

Naively treating these as 4 separate pieces of evidence artificially inflates the Likelihood Ratio (LR) by a factor of $4\times$.
AegisTrace implements sliding-window causal deduplication:
Any events sharing:
$$\text{ArtifactHash} \land (\text{SubjectID} \lor \text{DeviceID}) \land |t(e_i) - t(e_j)| \le \Delta t_{\text{dedup}}$$
are collapsed into a single causal event. Concurrent sources are preserved in `concurrent_telemetry_sources` for forensic provenance, but the evidentiary weight is capped at the maximum single-sensor reliability $\max_i(R_i)$.

---

## 3. Timeline Reconstruction & Custody Gaps

The timeline builder generates three distinct classifications of temporal intervals:
1. `OBSERVED`: Direct sensory evidence recorded by an authenticated sensor with known integrity.
2. `DERIVED`: Inferred continuous state between two proximate, causally linked observed events ($|t_{i+1} - t_i| \le \Delta t_{\text{gap}}$).
3. `UNKNOWN`: Unmonitored temporal gap where artifact custody cannot be accounted for by enterprise telemetry ($|t_{i+1} - t_i| > \Delta t_{\text{gap}}$).

The presence of an `UNKNOWN` gap enforces strict legal boundaries: AegisTrace explicitly certifies where observed custody ceased and downstream unmonitored handling began.
