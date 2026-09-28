# AegisTrace Human Attribution Boundaries & Epistemological Limits

## 1. The Core Scientific Premise

Digital forensic evidence records state transitions in computers, network equipment, and storage devices. **A digital log does not directly observe the human consciousness directing an action.**

AegisTrace establishes rigorous mathematical and epistemological boundaries that separate technical observations from human accusations. Under no circumstances will AegisTrace convert an account ID, IP address, or device serial into an uncorroborated accusation against a human individual.

---

## 2. Six-Tier Attribution Entity Taxonomy

To prevent category errors and legal over-reach, AegisTrace categorizes every entity in an attribution report into one of six mutually exclusive tiers:

1. **`OBSERVED ACCOUNT`** (e.g. `alice@corp.com`, `arn:aws:iam::...`)
   - Proves: That a specific credential was authenticated and used to request an action.
   - Does NOT prove: Who typed the password, who held the phone receiving an SMS OTP, or whether the credential was stolen.
2. **`OBSERVED DEVICE`** (e.g. `WS-FINANCE-04`, `PRINTER-HP-SERIAL-991`)
   - Proves: That an artifact was processed, stored, or rendered on a specific hardware platform.
   - Does NOT prove: Who was sitting in front of the screen.
3. **`OBSERVED NETWORK SOURCE`** (e.g. `198.51.100.24`, `VPN-US-EAST`)
   - Proves: The ingress or egress IP route used to transmit packets.
   - Does NOT prove: The physical location of the actor if proxies, VPNs, or Tor circuits are present.
4. **`OBSERVED FORWARDING EVENT`** (e.g. Email from Alice to Bob, Slack file attachment)
   - Proves: That entity $A$ initiated a transmission of an artifact to entity $B$.
   - Does NOT prove: That entity $B$ subsequently leaked the document.
5. **`INFERRED HUMAN`**
   - Proves: A probabilistic hypothesis associating an account or device with an individual employee.
   - Standard: Uncorroborated, insufficient for legal or disciplinary culpability.
6. **`CORROBORATED HUMAN`**
   - Requires: Multi-source independent physical corroboration:
     - Enrolled identity matching cryptographic release binding
     - Concurrent physical badge swipe / turnstile access into secure room
     - Active console session on endpoint (EDR keyboard/mouse interaction)
     - Multi-factor authentication (FIDO2 / WebAuthn hardware token)
     - Explicit absence of account takeover or shared kiosk flags

---

## 3. The Exact-Copy Downstream Transfer Theorem

### 3.1 Theorem Formulation
Consider an initial document release $D_A$ issued to recipient Alice. Suppose Alice forwards an exact bitwise copy of $D_A$ to Bob:
$$\text{Alice} \xrightarrow{\text{Forward}} \text{Bob} \xrightarrow{\text{Unobserved}} \text{Adversary } X \xrightarrow{\text{Publish}} \text{Public Drop}$$

If an investigation recovers the leaked file from the Public Drop and extracts the cryptographic watermark of $D_A$:
1. The watermark proves that the leaked artifact was derived from the copy initially released to Alice.
2. The enterprise email log proves that Alice forwarded the copy to Bob.
3. **Crucial Limitation**: The evidence **terminates** at Bob's inbox or desktop. Once Bob receives an exact copy, Bob could have:
   - Personally leaked the document.
   - Had his laptop stolen.
   - Been infected by malware.
   - Forwarded it to a colleague Charlie.
   - Left a printed copy in a conference room.

### 3.2 Required Decision State
In this scenario, AegisTrace outputs:
- `primary_state = LAST_KNOWN_CONTROLLED_HOLDER`
- `original_recipient_id = "Alice"`
- `last_known_controlled_holder = "Bob"`
- `publication_source = "Public Drop"`
- `all_states` includes `UNKNOWN_DOWNSTREAM_ACTOR`

**The system explicitly certifies that the downstream uploader is UNKNOWN.** Accusing Bob of leaking the file is mathematically and forensically unsupported.

---

## 4. Physical Device Forensics (PRNU & Printer MIC)

### 4.1 Photo Response Non-Uniformity (PRNU)
PRNU measures microscopic variations in silicon pixel response across digital camera sensors.
- If an observed smartphone photo yields PRNU fingerprint $\mathbf{K}$, and $\mathbf{K}$ matches an enrolled reference camera in the organization's database:
  $$\text{State} \to \text{DOWNSTREAM\_DEVICE\_IDENTIFIED}$$
- **The Zero-Knowledge Fallback**: If $\mathbf{K}$ does not match any enrolled camera, the provider outputs:
  $$\text{reference\_status} = \text{NO\_REFERENCE}, \quad \text{reference\_corpus\_matched} = \text{False}$$
  The engine **never** invents an imaginary camera serial number or guesses an owner.

### 4.2 Machine Identification Codes (MIC)
Color laser printers embed minute yellow dot patterns encoding printer serial numbers and timestamps.
- If decoded serial matches an enrolled corporate printer: $\text{DOWNSTREAM\_DEVICE\_IDENTIFIED}$.
- If printer is black-and-white, ink-jet, or unenrolled: $\text{NO\_REFERENCE}$.

---

## 5. Fail-Closed Abstention Policy

AegisTrace automatically aborts human attribution (emitting `ABSTAINED`) under the following conditions:
1. **Impossible Travel**: Authentication events from geographically incompatible locations within a sub-flight time interval (e.g. London turnstile and Vladivostok IP within 15 minutes).
2. **Shared Kiosk / Workstation**: More than one person's badge recorded at the terminal during an active session.
3. **Untrusted Telemetry**: Any imported log bundle that fails cryptographic signature verification or exhibits internal hash mismatches.
