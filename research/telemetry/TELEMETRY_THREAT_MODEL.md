# AegisTrace Telemetry Threat Model & Adversarial Analysis

## 1. Threat Environment & Adversary Capabilities

In enterprise leak scenarios and targeted insider threat investigations, adversaries possess substantial technical capabilities to manipulate, forge, or suppress telemetry signals:
- **Malicious Insiders**: Privileged access to local endpoints, ability to alter system clocks, disable local security agents, or route traffic through commercial VPNs.
- **Compromised Accounts**: Attackers using stolen session cookies, MFA bypass techniques, or remote access Trojans (RATs).
- **Log Tampering**: Attempts to modify exported SIEM/EDR log dumps prior to forensic handoff.
- **Collusive Deflection**: Intentionally framing another employee by forwarding documents or copying them to shared workstations.

---

## 2. Adversarial Vectors & AegisTrace Defenses

| Adversarial Attack Vector | Attack Description | AegisTrace Countermeasure & Invariant |
|:---|:---|:---|
| **Vector 1: Clock Skew Spoofing** | Attacker backdates local machine clock to make an exfiltration event appear prior to document release. | **Causal Predecessor Validation**: Enforces $t_B \ge t_A - \Delta t_{\text{skew}}$. Predecessor violations flag `CAUSAL_VIOLATION` and invalidate candidate hypotheses. |
| **Vector 2: Synthetic EDR Injection** | Attacker injects fabricated JSON log entries into an exported telemetry file to frame a target. | **Cryptographic Bundle Manifests**: Requires HMAC-SHA256 or ML-DSA digital signatures over canonical event digests. Unsigned/tampered logs are marked `UNTRUSTED` and engine aborts (`ABSTAINED`). |
| **Vector 3: Multi-Sensor Duplication Flooding** | Attacker orchestrates duplicate alerts across EDR, DLP, Syslog, and NetFlow to artificially inflate attribution confidence. | **Causal Deduplication Window**: Collapses concurrent alerts for the same artifact and actor into a single logical event, capping evidentiary weight at single-sensor maximum. |
| **Vector 4: Account Takeover & Pivoting** | Attacker compromises Alice's account from a remote VPN/Tor node and downloads sensitive files. | **Impossible Travel & Anomaly Detection**: Cross-correlates IdP/Network geolocations against physical badge telemetry. Rejects human attribution, marking `account_compromised_or_shared = True`. |
| **Vector 5: Shared Workstation Masking** | Attacker uses a common lab terminal or kiosk workstation to download and exfiltrate documents. | **Multi-Badge Ambiguity Detection**: Correlates multiple physical badge swipes during active kiosk windows. Restricts candidate to `OBSERVED_DEVICE` / `OBSERVED_ACCOUNT` and abstains from naming an individual. |
| **Vector 6: Egress Masking via VPN / Tor** | Attacker uploads leaked document through an anonymizing VPN or Tor exit gateway. | **Network Ambiguity Preservation**: Tags network node as `is_vpn_or_proxy = True`, preserving boundary and preventing false IP attribution to innocuous residential networks. |
| **Vector 7: PRNU Sensor Noise Hallucination** | Investigator attempts to assert that an unverified camera photo originated from a suspect's phone. | **Enrolled Reference Corpus Requirement**: Sensor noise that does not match an enrolled corporate reference database strictly returns `NO_REFERENCE`. Guessing or probabilistic matching is prohibited. |
| **Vector 8: Custody Gap Exploitation** | Insider forwards document to an external contractor; leak appears 3 weeks later on Pastebin. | **Downstream Custody Boundary Enforcement**: Engine identifies contractor as `LAST_KNOWN_CONTROLLED_HOLDER` and records Pastebin uploader as `UNKNOWN_DOWNSTREAM_ACTOR`. |

---

## 3. Fail-Closed Security Guarantee

The central guarantee of the AegisTrace Telemetry Architecture is **fail-closed security**:
When external telemetry is compromised, conflicting, or absent, the platform degrades gracefully to its verified cryptographic core (watermarking and Tardos codebook verification). It never fabricates operational certainty to satisfy an investigative bias.
