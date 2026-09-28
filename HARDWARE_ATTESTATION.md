# AegisTrace: Cryptographic Hardware Attestation & Device Profile

**Document ID:** `AEGIS-HW-ATTEST-2026`  
**Classification:** RESTRICTED / FORENSIC ATTESTATION RECORD  
**Standards Compliance:** NIST FIPS 203 (ML-KEM-768), NIST FIPS 204 (ML-DSA-65), RFC 6962  
**Validation Timestamp:** 2026-09-27T23:13:22Z  
**Host Machine:** `MSI` (Windows 11 Enterprise x64)  

---

## 1. Hardware Inventory & Attestation Profile

AegisTrace anchors cryptographic sessions, decryption authorizations, and evidence packages directly to verifiable hardware descriptors.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                      AEGISTRACE HARDWARE ATTESTATION GRAPH                    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  [HOST WORKSTATION]                                                           │
│   • Identifier: MSI (Windows 11 x64, Build 22631)                            │
│   • Display: AMD Radeon(TM) Graphics (1920x1080 @ 144Hz)                      │
│   • Host IP: 10.114.31.4 (Wi-Fi 802.11ax Interface Index 10)                  │
│                                                                               │
│            │                                           │                      │
│   Mutual TLS / Zero-Trust Channel             Mutual TLS / Zero-Trust Channel │
│            │                                           │                      │
│            ▼                                           ▼                      │
│  [PHONE A: RECIPIENT ENDPOINT]               [PHONE B: ISOLATED ENDPOINT]     │
│   • Model: Galaxy Note10 Lite (SM-N770F)      • Model: Galaxy A55 5G          │
│   • Hardware Serial: RF8N927PM9N              • Hardware Serial: RZCY9396AGX  │
│   • OS: Android 12 (API Level 31)             • OS: Android 14 (API Level 34) │
│   • USB State: Composite MTP / ADB            • USB State: Composite MTP      │
│   • Cryptographic Identity:                   • Cryptographic Identity:       │
│     ML-KEM-768 Public Key                      ML-KEM-768 Public Key          │
│     ML-DSA-65 Attestation Key                  ML-DSA-65 Attestation Key      │
│   • Assigned Role: PHONE_A_RECIPIENT          • Assigned Role: PHONE_B_ISO    │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Cryptographic Attestation Mechanisms

### 2.1 Post-Quantum Key Agreement & Identity Binding
1. **NIST FIPS 203 ML-KEM-768:**
   - Every enrolled device generates an ephemeral or hardware-bound ML-KEM-768 keypair.
   - Decryption keys are encapsulated by the server using the device's public key ($\text{pk}_{\text{dev}}$).
   - Only the specific physical device with the matching private key ($\text{sk}_{\text{dev}}$) can decapsulate the shared secret.
2. **NIST FIPS 204 ML-DSA-65 Attestation Signatures:**
   - Device attestation reports and evidence package manifests are signed with ML-DSA-65.
   - Guarantees non-repudiation and prevents public key substitution attacks.

### 2.2 Replay-Resistant Challenge-Response Protocol
To prevent session replay attacks or cloning of device tokens:
1. Server issues a cryptographically secure random 256-bit challenge nonce $N_c$.
2. The device signs $(N_c \parallel \text{timestamp} \parallel \text{device\_serial})$ using its hardware-bound private key.
3. The server validates the signature, checks that $N_c$ has not been previously consumed, and enforces a strict 30-second freshness window.

---

## 3. Discovered Hardware Specification & Identity Details

### 3.1 Smartphone A: Primary Authorized Recipient
- **Device ID:** `phone_rf8n927pm9n`
- **Device Role:** `PHONE_A_RECIPIENT`
- **Manufacturer / Model:** Samsung Galaxy Note10 Lite (`SM-N770F`)
- **Hardware Serial Number:** `RF8N927PM9N`
- **Operating System:** Android 12 (SDK 31)
- **USB PnP Identity:** `USB\VID_04E8&PID_6860\RF8N927PM9N`
- **Connection Modality:** Real USB-ADB / MTP Composite Bus
- **Epistemic State:** **`DEVICE_IN_LOOP`**

### 3.2 Smartphone B: Independent Secondary Endpoint
- **Device ID:** `phone_rzcy9396agx`
- **Device Role:** `PHONE_B_INDEPENDENT`
- **Manufacturer / Model:** Samsung Galaxy A55 5G (`SM-A556B`)
- **Hardware Serial Number:** `RZCY9396AGX`
- **Operating System:** Android 14 (OneUI 6.1)
- **USB PnP Identity:** `USB\VID_04E8&PID_6860\RZCY9396AGX` (`Galaxy A55 Endpoint B`)
- **Connection Modality:** Real USB MTP Bus
- **Epistemic State:** **`DEVICE_IN_LOOP`**

### 3.3 Host Workstation & Physical Display
- **Host System:** `MSI` (Windows 11 Pro 64-bit)
- **Primary GPU & Display Controller:** AMD Radeon(TM) Graphics
- **Physical Display Resolution:** $1920 \times 1080$ pixels @ 144.0 Hz
- **Display Driver:** `Advanced Micro Devices, Inc.`
- **Physical Presentation Verification:** Carrier rendered directly to physical framebuffer.
- **Epistemic State:** **`DEVICE_IN_LOOP`**

### 3.4 Network Infrastructure
- **Active Physical Interface:** Wi-Fi (`Wi-Fi`, Interface Index 10)
- **Local Host IP Address:** `10.114.31.4`
- **Subnet:** `255.255.255.0`
- **Secondary Local Virtual Interface:** WSL Hyper-V (`172.20.128.1`)
- **Epistemic State:** **`DEVICE_IN_LOOP`**

---

## 4. Hardware Absence Audit & Epistemic Boundaries

In accordance with strict anti-fabrication standards, physical hardware absence is permanently audited:

| Modality | Probed Interface | Discovered State | Epistemic Classification |
| :--- | :--- | :--- | :--- |
| **Document Camera** | DirectShow / MediaFoundation indices 0–3 | 0 devices detected | **`NOT_VERIFIED`** |
| **Physical Printer** | Windows Print Spooler (Physical Queues) | 0 devices detected | **`UNAVAILABLE`** |
| **Document Scanner** | Windows Image Acquisition (WIA) | 0 devices detected | **`UNAVAILABLE`** |

> [!IMPORTANT]
> **Epistemic Boundary:** Connecting a smartphone via USB does NOT provide a document camera feed. AegisTrace explicitly refuses to mark optical capture as verified unless a physical optical sensor stream is authenticated.
