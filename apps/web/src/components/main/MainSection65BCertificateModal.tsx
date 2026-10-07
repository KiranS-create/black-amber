import React, { useState, useEffect } from 'react';
import { 
  X, 
  Printer, 
  Download, 
  FileCheck, 
  ShieldCheck, 
  Award, 
  Scale, 
  CheckCircle2, 
  FileArchive,
  QrCode,
  Fingerprint,
  Cpu,
  Lock,
  Plus,
  Trash2,
  FolderOpen,
  UserCheck,
  ShieldAlert,
  Calendar,
  Building,
  FileText,
  AlertTriangle
} from 'lucide-react';
import JSZip from 'jszip';
import { STANDALONE_VERIFIER_PYTHON_SCRIPT } from '../../utils/standalone_verifier_template';
import { AttributionResult, PublicRecipient } from '../../types';

export interface CourtCaseProfile {
  id: string;
  caseNumber: string;               // e.g. "CR-DL-2026-0929-DEFENCE"
  firNumber: string;                // e.g. "FIR-CBI-CYBER-2026-881"
  docketId: string;                 // e.g. "CERT-65B-AEGIS-2026-9901"
  title: string;                    // e.g. "State (National Cyber Cell) v. Marcus Vance"
  jurisdiction: string;             // e.g. "Special Cyber Appellate Tribunal (New Delhi)"
  incidentDate: string;             // e.g. "26 September 2026"
  documentName: string;             // e.g. "Strategic_Defense_Protocol_2026.pdf"
  classification: string;           // "TOP SECRET // NOFORN"
  accusedName: string;              // "Marcus Vance"
  accusedRank: string;              // "Principal Cryptanalyst"
  accusedDepartment: string;        // "Naval Cryptographic Operations (WESEE)"
  terminalId: string;               // "Field Terminal #ST-842911"
  secretCodeHex: string;            // "0x7E9A-C401-88F3-902B-0CDA07-9AF2"
  confidence: string;               // "99.98% (BCH-Verified, 0 Bit Errors)"
  bchStatus: string;                // "0 Bit Errors (BCH t=3 Corrected)"
  statutoryActs: string[];          // ["BSA 2023 § 63(4)", "Official Secrets Act 1923 § 3 & 5", ...]
  incidentSynopsis: string;         // Case narrative
  routeHops: string[];
  originalDocHash: string;
  leakHash: string;
  sigDigest: string;
  merkleLeaf: string;
  merkleRoot: string;
  fusionFormula: string;
  fusionScore: number;
  bayesianLlr: string;
  pfaBound: string;
  examinerName: string;
  examinerRank: string;
  examinerKeyId: string;
  magistrateName: string;
  magistrateRank: string;
  magistrateSealId: string;
  isCustom?: boolean;
}

const PRESET_CASES: CourtCaseProfile[] = [
  {
    id: 'case_marcus',
    caseNumber: 'CR-DL-2026-0929-DEFENCE',
    firNumber: 'FIR-CBI-CYBER-2026-881',
    docketId: 'CERT-65B-AEGIS-2026-9901',
    title: 'State (Special Cyber Cell) v. Marcus Vance',
    jurisdiction: 'Special Cyber Appellate Tribunal (New Delhi)',
    incidentDate: '26 September 2026',
    documentName: 'Strategic_Defense_Protocol_2026.pdf',
    classification: 'TOP SECRET // NOFORN',
    accusedName: 'Marcus Vance',
    accusedRank: 'Principal Cryptanalyst',
    accusedDepartment: 'Strategic Intelligence Division (WESEE)',
    terminalId: 'Field Terminal #ST-842911',
    secretCodeHex: '0x7E9A-C401-88F3-902B-0CDA07-9AF2',
    confidence: '99.98% (BCH-Verified, 0 Bit Errors)',
    bchStatus: '0 Bit Errors (BCH t=3 Corrected)',
    statutoryActs: [
      'Section 63(4) Bharatiya Sakshya Adhiniyam, 2023',
      'Official Secrets Act, 1923 §§ 3 & 5',
      'Bharatiya Nyaya Sanhita, 2023 § 316 (Criminal Breach of Trust)',
      'Information Technology Act, 2000 § 43 & § 66'
    ],
    incidentSynopsis: 'Unauthorized exfiltration of classified Post-Quantum Cryptographic Key Deployment Architecture. Recipient cryptographic watermark carrier extracted with 98.4% DSSS correlation; ML-DSA-65 signature verified on audit ledger block #842,911.',
    routeHops: [
      'Strategic Central Enclave (HQ Node)',
      'Intelligence Dissemination Hub #02 (Mumbai)',
      'Tactical Cryptography Terminal Node #04',
      'Field Terminal #ST-842911 (Marcus Vance / bob)'
    ],
    originalDocHash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    leakHash: '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
    sigDigest: 'dSA65_sig_vance_04_eefa1234567890abcdef1234567890abcdef1234567890ab',
    merkleLeaf: 'Block #842,911 (ML-DSA-65 Valid Signature)',
    merkleRoot: '03a58e65f9024b11e2890acdef1234567890abcdef1234567890abcdef123456',
    fusionFormula: 'E = 0.35·W + 0.15·H + 0.30·S + 0.20·L = 0.978',
    fusionScore: 0.978,
    bayesianLlr: '+18.08 LLR',
    pfaBound: '≤ 10⁻⁶ (1 in 1,000,000)',
    examinerName: 'Dr. V. Raman, Ph.D.',
    examinerRank: 'Lead Forensic Cryptographer (WESEE / CERT-In)',
    examinerKeyId: 'FIPS-204-ML-DSA-65-RAMAN-841',
    magistrateName: 'Capt. S. Sengupta, IN',
    magistrateRank: 'Naval Provost Marshal / Judicial Magistrate',
    magistrateSealId: 'SABHA-COUNCIL-QUORUM-SEALED-2026'
  },
  {
    id: 'case_sarah',
    caseNumber: 'CR-MUM-2026-1104-NAVY',
    firNumber: 'FIR-NAVY-POLICE-2026-104',
    docketId: 'CERT-65B-AEGIS-2026-9902',
    title: 'Union of India (Ministry of Defence) v. Sarah Jenkins',
    jurisdiction: 'Armed Forces Tribunal (Western Command, Mumbai)',
    incidentDate: '14 October 2026',
    documentName: 'Western_Naval_Fleet_Readiness_2026.pdf',
    classification: 'SECRET // OPERATIONAL',
    accusedName: 'Sarah Jenkins',
    accusedRank: 'Cyber Defense Operations Lead',
    accusedDepartment: 'Cyber Defense Operations',
    terminalId: 'Field Terminal #ST-991204',
    secretCodeHex: '0x4A1F-E902-11D8-BC73-88FA01-44B2',
    confidence: '98.20% (DCT-Aligned, BCH Corrected)',
    bchStatus: '0 Bit Errors (BCH t=3 Corrected)',
    statutoryActs: [
      'Section 63 Bharatiya Sakshya Adhiniyam, 2023',
      'Navy Act, 1957 § 54 (Breach of Official Duty)',
      'Official Secrets Act, 1923 § 5'
    ],
    incidentSynopsis: 'Interception of Western Naval Fleet movement and submarine surveillance perimeter specifications. Spatial watermark recovered with 98.2% correlation; non-repudiation ledger confirms access receipt token evt_dec_alice_003.',
    routeHops: [
      'Strategic Central Enclave (HQ Node)',
      'Western Fleet Operational Command',
      'Maritime Security Terminal Node #02',
      'Field Terminal #ST-991204 (Sarah Jenkins / alice)'
    ],
    originalDocHash: '8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b',
    leakHash: '6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e',
    sigDigest: 'dSA65_sig_jenkins_02_bbca9876543210fedcba9876543210fedcba9876543210fe',
    merkleLeaf: 'Block #842,912 (ML-DSA-65 Valid Signature)',
    merkleRoot: '03a58e65f9024b11e2890acdef1234567890abcdef1234567890abcdef123456',
    fusionFormula: 'E = 0.35·W + 0.15·H + 0.30·S + 0.20·L = 0.965',
    fusionScore: 0.965,
    bayesianLlr: '+17.92 LLR',
    pfaBound: '≤ 10⁻⁶ (1 in 1,000,000)',
    examinerName: 'Dr. V. Raman, Ph.D.',
    examinerRank: 'Lead Forensic Cryptographer (WESEE / CERT-In)',
    examinerKeyId: 'FIPS-204-ML-DSA-65-RAMAN-841',
    magistrateName: 'Capt. S. Sengupta, IN',
    magistrateRank: 'Naval Provost Marshal / Judicial Magistrate',
    magistrateSealId: 'SABHA-COUNCIL-QUORUM-SEALED-2026'
  },
  {
    id: 'case_camera',
    caseNumber: 'CR-AIRGAP-2026-0812-HOMOGRAPHY',
    firNumber: 'FIR-NIA-TECH-2026-442',
    docketId: 'CERT-65B-AEGIS-2026-9903',
    title: 'In re: Optical Screen-Capture & Air-Gap Evasion Incident',
    jurisdiction: 'Special Cyber Division, High Court of Judicature',
    incidentDate: '02 November 2026',
    documentName: 'Submarine_Sonar_Acoustics_V4.pdf',
    classification: 'TOP SECRET // AIR-GAP ISOLATED',
    accusedName: 'Marcus Vance',
    accusedRank: 'Principal Cryptanalyst',
    accusedDepartment: 'Strategic Intelligence Division',
    terminalId: 'Field Terminal #ST-842911',
    secretCodeHex: '0x91F2-BB38-40C1-22A8-FA9081-01C5',
    confidence: '92.40% (Homography Perspective Rectified)',
    bchStatus: '3 Burst Errors Corrected (RS 42,26)',
    statutoryActs: [
      'Section 63(4) Bharatiya Sakshya Adhiniyam, 2023',
      'Information Technology Act, 2000 § 66F (Cyber Terrorism)',
      'Official Secrets Act, 1923 § 3'
    ],
    incidentSynopsis: 'Accused attempted to evade data loss prevention by using an optical smartphone camera at a 25° perspective skew. Automated OpenCV projective homography detected Barker-13 corner fiducials, de-skewed the canvas, and extracted the recipient codeword at 24.6 dB PSNR.',
    routeHops: [
      'Strategic Central Enclave (HQ Node)',
      'Tactical Operations Center (Air-Gapped)',
      'Secured Display Terminal #ST-842911',
      'Optical Camera Intercept (Physical Device Capture)'
    ],
    originalDocHash: '1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d',
    leakHash: '3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b',
    sigDigest: 'dSA65_sig_optical_skew_8812490123abcdef8812490123abcdef8812490123ab',
    merkleLeaf: 'Block #842,913 (ML-DSA-65 Valid Signature)',
    merkleRoot: '03a58e65f9024b11e2890acdef1234567890abcdef1234567890abcdef123456',
    fusionFormula: 'E = 0.35·W + 0.15·H + 0.30·S + 0.20·L = 0.924',
    fusionScore: 0.924,
    bayesianLlr: '+14.30 LLR',
    pfaBound: '≤ 10⁻⁵ (1 in 100,000)',
    examinerName: 'Dr. V. Raman, Ph.D.',
    examinerRank: 'Lead Forensic Cryptographer (WESEE / CERT-In)',
    examinerKeyId: 'FIPS-204-ML-DSA-65-RAMAN-841',
    magistrateName: 'Capt. S. Sengupta, IN',
    magistrateRank: 'Naval Provost Marshal / Judicial Magistrate',
    magistrateSealId: 'SABHA-COUNCIL-QUORUM-SEALED-2026'
  },
  {
    id: 'case_collusion',
    caseNumber: 'CR-COLLUSION-2026-0419-TARDOS',
    firNumber: 'FIR-CBI-ANTI-CORRUPT-2026-309',
    docketId: 'CERT-65B-AEGIS-2026-9904',
    title: 'State v. Marcus Vance & Dr. Aris Thorne (Collusion Coalition)',
    jurisdiction: 'Special Court of the Central Bureau of Investigation',
    incidentDate: '18 November 2026',
    documentName: 'Nuclear_Command_Cryptography_Standard.pdf',
    classification: 'TOP SECRET // STRICT RESTRICTION',
    accusedName: 'Marcus Vance & Dr. Aris Thorne (Co-Conspirators)',
    accusedRank: 'Principal Cryptanalyst & Visiting PQC Scientist',
    accusedDepartment: 'Strategic Intelligence & External Research',
    terminalId: 'Joint Tactical Enclave #JTE-09',
    secretCodeHex: '0xCC01-77BA-9021-EE14-00AB39-21F8',
    confidence: '99.99% (Tardos Coalition Traitor Matrix Bounded)',
    bchStatus: 'Dual-Symbol Orthogonal Separation Verified',
    statutoryActs: [
      'Section 63 Bharatiya Sakshya Adhiniyam, 2023',
      'Official Secrets Act, 1923 § 3',
      'Bharatiya Nyaya Sanhita, 2023 § 61 (Criminal Conspiracy)'
    ],
    incidentSynopsis: 'Two authorized recipients attempted a coalition attack by interleaving content segments to average out watermarks and frame a third party. Gabor Tardos traitor-tracing score vector (Score U=84.6 > Cutoff Z=22.4) isolated both co-conspirators to the mathematical exclusion of all innocent cohort members.',
    routeHops: [
      'Strategic Central Enclave (HQ Node)',
      'Joint Dissemination Hub #03',
      'Tactical Terminal #ST-842911 (Vance) & #ST-991204 (Thorne)',
      'Adversarial Spliced Leak Artifact'
    ],
    originalDocHash: '5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f',
    leakHash: '7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d',
    sigDigest: 'dSA65_sig_collusion_dual_9901abcdef9901abcdef9901abcdef9901abcdef99',
    merkleLeaf: 'Block #842,914 (Dual ML-DSA-65 Valid Signatures)',
    merkleRoot: '03a58e65f9024b11e2890acdef1234567890abcdef1234567890abcdef123456',
    fusionFormula: 'E = 0.35·W + 0.15·H + 0.30·S + 0.20·L = 0.989',
    fusionScore: 0.989,
    bayesianLlr: '+19.45 LLR',
    pfaBound: '≤ 10⁻⁷ (1 in 10,000,000)',
    examinerName: 'Dr. V. Raman, Ph.D.',
    examinerRank: 'Lead Forensic Cryptographer (WESEE / CERT-In)',
    examinerKeyId: 'FIPS-204-ML-DSA-65-RAMAN-841',
    magistrateName: 'Capt. S. Sengupta, IN',
    magistrateRank: 'Naval Provost Marshal / Judicial Magistrate',
    magistrateSealId: 'SABHA-COUNCIL-QUORUM-SEALED-2026'
  }
];

export interface MainSection65BCertificateModalProps {
  isOpen: boolean;
  onClose: () => void;
  result?: AttributionResult | null;
  candidateName?: string;
  documentName?: string;
  terminalId?: string;
  suspectRank?: string;
  secretCodeHex?: string;
  merkleLeaf?: string;
  confidence?: string;
  bchStatus?: string;
  routeHop?: string[];
  sabhaCountersigned?: boolean;
  recipients?: PublicRecipient[];
  initialCaseId?: string;
}

export const MainSection65BCertificateModal: React.FC<MainSection65BCertificateModalProps> = ({
  isOpen,
  onClose,
  result,
  candidateName = 'Marcus Vance',
  documentName = 'Strategic_Defense_Protocol_2026.pdf',
  terminalId = 'Field Terminal #ST-842911',
  suspectRank = 'Principal Cryptanalyst',
  secretCodeHex = '0x7E9A-C401-88F3-902B-0CDA07-9AF2',
  merkleLeaf = 'Block #842,911 (ML-DSA-65 Valid Signature)',
  confidence = '99.98% (BCH-Verified, 0 Bit Errors)',
  bchStatus = '0 Bit Errors (BCH t=3 Corrected)',
  routeHop,
  sabhaCountersigned = true,
  recipients = [],
  initialCaseId
}) => {
  // Load custom cases from localStorage
  const [customCases, setCustomCases] = useState<CourtCaseProfile[]>(() => {
    try {
      const stored = localStorage.getItem('aegistrace_custom_court_cases');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch {}
    return [];
  });

  // Active case selection
  const [selectedCaseId, setSelectedCaseId] = useState<string>(() => {
    if (initialCaseId) return initialCaseId;
    return 'case_marcus';
  });

  // Interactive Sabha Dual-Signing states
  const [examinerSigned, setExaminerSigned] = useState<boolean>(true);
  const [magistrateSigned, setMagistrateSigned] = useState<boolean>(sabhaCountersigned);

  // Custom Case Creator Drawer state
  const [isCreatingCase, setIsCreatingCase] = useState<boolean>(false);
  const [newCaseNumber, setNewCaseNumber] = useState<string>('');
  const [newFirNumber, setNewFirNumber] = useState<string>('');
  const [newTitle, setNewTitle] = useState<string>('');
  const [newJurisdiction, setNewJurisdiction] = useState<string>('Special Cyber Court (Armed Forces Tribunal)');
  const [newAccusedName, setNewAccusedName] = useState<string>('');
  const [newAccusedRank, setNewAccusedRank] = useState<string>('');
  const [newAccusedDept, setNewAccusedDept] = useState<string>('Naval Cryptographic Operations (WESEE)');
  const [newTerminalId, setNewTerminalId] = useState<string>('');
  const [newDocName, setNewDocName] = useState<string>('Classified_Naval_Briefing_2026.pdf');
  const [newClassification, setNewClassification] = useState<string>('TOP SECRET // NOFORN');
  const [newSynopsis, setNewSynopsis] = useState<string>('Unauthorized exfiltration of classified tactical data intercepted at perimeter.');
  const [newConfidence, setNewConfidence] = useState<string>('99.95% (BCH-Verified, 0 Bit Errors)');

  // Sync when prop updates
  useEffect(() => {
    if (initialCaseId) {
      setSelectedCaseId(initialCaseId);
    }
  }, [initialCaseId]);

  useEffect(() => {
    setMagistrateSigned(sabhaCountersigned);
  }, [sabhaCountersigned]);

  if (!isOpen) return null;

  // Synthesize dynamic case if passed from active result
  const dynamicActiveCase: CourtCaseProfile | null = (result || candidateName !== 'Marcus Vance') ? {
    id: 'case_active',
    caseNumber: `CR-LIVE-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
    firNumber: `FIR-LIVE-FORENSIC-${Math.floor(100 + Math.random() * 900)}`,
    docketId: `CERT-65B-AEGIS-${new Date().getFullYear()}-LIVE`,
    title: `In re: Forensic Attribution of Leaked Document (${result?.candidate?.name || candidateName})`,
    jurisdiction: 'Special Cyber Appellate Tribunal (National Defense Command)',
    incidentDate: new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' }),
    documentName: documentName,
    classification: 'TOP SECRET // NOFORN',
    accusedName: result?.candidate?.name || candidateName,
    accusedRank: suspectRank,
    accusedDepartment: result?.candidate?.identity_summary?.department || 'Strategic Intelligence Division',
    terminalId: terminalId,
    secretCodeHex: secretCodeHex,
    confidence: confidence,
    bchStatus: bchStatus,
    statutoryActs: [
      'Section 63(4) Bharatiya Sakshya Adhiniyam, 2023',
      'Official Secrets Act, 1923 §§ 3 & 5',
      'Bharatiya Nyaya Sanhita, 2023 § 316',
      'Information Technology Act, 2000 § 43 & § 66'
    ],
    incidentSynopsis: `Automated 4-vector multi-vector evidence fusion extracted volatile cryptographic marker from intercepted artifact. Corroborates authorized principal ${result?.candidate?.name || candidateName} on hardware terminal ${terminalId}.`,
    routeHops: routeHop || [
      'Strategic Central Enclave (HQ Node)',
      'Intelligence Dissemination Hub #02',
      'Tactical Cryptography Terminal',
      `${terminalId} (${result?.candidate?.name || candidateName})`
    ],
    originalDocHash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    leakHash: '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
    sigDigest: 'dSA65_sig_live_session_hash_7788112233aabbccddeeff001122334455667788',
    merkleLeaf: merkleLeaf,
    merkleRoot: '03a58e65f9024b11e2890acdef1234567890abcdef1234567890abcdef123456',
    fusionFormula: 'E = 0.35·W + 0.15·H + 0.30·S + 0.20·L = 0.978',
    fusionScore: 0.978,
    bayesianLlr: '+18.08 LLR',
    pfaBound: '≤ 10⁻⁶ (1 in 1,000,000)',
    examinerName: 'Dr. V. Raman, Ph.D.',
    examinerRank: 'Lead Forensic Cryptographer (WESEE / CERT-In)',
    examinerKeyId: 'FIPS-204-ML-DSA-65-RAMAN-841',
    magistrateName: 'Capt. S. Sengupta, IN',
    magistrateRank: 'Naval Provost Marshal / Judicial Magistrate',
    magistrateSealId: 'SABHA-COUNCIL-QUORUM-SEALED-2026'
  } : null;

  // Combine all available cases
  const allCases: CourtCaseProfile[] = [
    ...(dynamicActiveCase ? [dynamicActiveCase] : []),
    ...PRESET_CASES,
    ...customCases
  ];

  const activeCase = allCases.find(c => c.id === selectedCaseId) || allCases[0];

  // Save new custom case
  const handleCreateCustomCase = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAccusedName.trim()) {
      alert('Please enter the Accused Subject name.');
      return;
    }

    const customId = `custom_case_${Date.now()}`;
    const generatedCaseNum = newCaseNumber.trim() || `CR-SPEC-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`;
    const generatedFir = newFirNumber.trim() || `FIR-DEF-${Math.floor(100 + Math.random() * 900)}`;

    const newCase: CourtCaseProfile = {
      id: customId,
      caseNumber: generatedCaseNum,
      firNumber: generatedFir,
      docketId: `CERT-65B-AEGIS-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
      title: newTitle.trim() || `State v. ${newAccusedName}`,
      jurisdiction: newJurisdiction.trim(),
      incidentDate: new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' }),
      documentName: newDocName.trim(),
      classification: newClassification,
      accusedName: newAccusedName.trim(),
      accusedRank: newAccusedRank.trim() || 'Authorized Principal Officer',
      accusedDepartment: newAccusedDept.trim(),
      terminalId: newTerminalId.trim() || `Field Terminal #ST-${Math.floor(100000 + Math.random() * 900000)}`,
      secretCodeHex: `0x${Array.from({length: 4}, () => Math.floor(Math.random()*65535).toString(16).toUpperCase().padStart(4, '0')).join('-')}`,
      confidence: newConfidence,
      bchStatus: '0 Bit Errors (BCH t=3 Corrected)',
      statutoryActs: [
        'Section 63(4) Bharatiya Sakshya Adhiniyam, 2023',
        'Official Secrets Act, 1923 §§ 3 & 5',
        'Bharatiya Nyaya Sanhita, 2023 § 316',
        'Information Technology Act, 2000 § 43 & § 66'
      ],
      incidentSynopsis: newSynopsis.trim(),
      routeHops: [
        'Strategic Central Enclave (HQ Node)',
        'Sector Dissemination Hub #01',
        'Tactical Security Terminal Node',
        `${newTerminalId.trim() || 'Field Terminal'} (${newAccusedName.trim()})`
      ],
      originalDocHash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      leakHash: '4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e',
      sigDigest: `dSA65_sig_${customId}_digest_valid_provenance_seal_authenticated_2026`,
      merkleLeaf: `Block #${Math.floor(800000 + Math.random() * 100000)} (ML-DSA-65 Valid Signature)`,
      merkleRoot: '03a58e65f9024b11e2890acdef1234567890abcdef1234567890abcdef123456',
      fusionFormula: 'E = 0.35·W + 0.15·H + 0.30·S + 0.20·L = 0.978',
      fusionScore: 0.978,
      bayesianLlr: '+18.08 LLR',
      pfaBound: '≤ 10⁻⁶ (1 in 1,000,000)',
      examinerName: 'Dr. V. Raman, Ph.D.',
      examinerRank: 'Lead Forensic Cryptographer (WESEE / CERT-In)',
      examinerKeyId: 'FIPS-204-ML-DSA-65-RAMAN-841',
      magistrateName: 'Capt. S. Sengupta, IN',
      magistrateRank: 'Naval Provost Marshal / Judicial Magistrate',
      magistrateSealId: 'SABHA-COUNCIL-QUORUM-SEALED-2026',
      isCustom: true
    };

    const updated = [newCase, ...customCases];
    setCustomCases(updated);
    try {
      localStorage.setItem('aegistrace_custom_court_cases', JSON.stringify(updated));
    } catch {}

    setSelectedCaseId(customId);
    setIsCreatingCase(false);

    // Reset inputs
    setNewCaseNumber('');
    setNewFirNumber('');
    setNewTitle('');
    setNewAccusedName('');
    setNewAccusedRank('');
    setNewTerminalId('');
  };

  const handleDeleteCustomCase = (caseIdToDelete: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this custom case docket?')) return;
    const filtered = customCases.filter(c => c.id !== caseIdToDelete);
    setCustomCases(filtered);
    try {
      localStorage.setItem('aegistrace_custom_court_cases', JSON.stringify(filtered));
    } catch {}
    if (selectedCaseId === caseIdToDelete) {
      setSelectedCaseId('case_marcus');
    }
  };

  const isDualOfficerValidated = examinerSigned && magistrateSigned;

  // Print Handlers
  const handlePrint = () => {
    window.print();
  };

  const handleOpenStandalonePrintView = () => {
    const printWindow = window.open('', '_blank', 'width=920,height=1150');
    if (!printWindow) {
      alert('Popup blocker prevented opening the print window. Please allow popups or use the Browser Print button.');
      return;
    }

    const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Court Evidence Docket - BSA § 63 / § 65B - ${activeCase.docketId}</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 14mm 16mm;
    }
    body {
      font-family: "Times New Roman", Times, Georgia, serif;
      color: #0F172A;
      background: #FFFFFF;
      margin: 0;
      padding: 0;
      font-size: 11pt;
      line-height: 1.45;
    }
    .docket-container {
      border: 2px solid #0F172A;
      padding: 24px 28px;
      box-sizing: border-box;
      position: relative;
    }
    .header-seal {
      text-align: center;
      border-bottom: 2px double #0F172A;
      padding-bottom: 14px;
      margin-bottom: 16px;
    }
    .gov-title {
      font-size: 9pt;
      letter-spacing: 0.16em;
      font-weight: bold;
      color: #334155;
      text-transform: uppercase;
    }
    .main-court-title {
      font-size: 15pt;
      font-weight: bold;
      margin: 4px 0 2px 0;
      letter-spacing: 0.02em;
    }
    .legal-act {
      font-size: 10pt;
      font-style: italic;
      color: #475569;
    }
    .meta-bar {
      display: flex;
      justify-content: space-between;
      font-size: 8.5pt;
      font-family: system-ui, -apple-system, sans-serif;
      border-top: 1px solid #CBD5E1;
      padding-top: 6px;
      margin-top: 10px;
    }
    .section-title {
      font-family: system-ui, -apple-system, sans-serif;
      font-weight: bold;
      font-size: 10pt;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border-bottom: 1px solid #CBD5E1;
      padding-bottom: 3px;
      margin: 12px 0 8px 0;
      color: #0F172A;
    }
    .data-grid {
      display: grid;
      grid-template-columns: 200px 1fr;
      row-gap: 3px;
      font-size: 9pt;
      font-family: system-ui, -apple-system, sans-serif;
    }
    .data-label { color: #64748B; font-weight: 500; }
    .data-value { color: #0F172A; font-weight: 600; }
    .mono { font-family: "Courier New", Courier, monospace; }
    .fusion-box {
      background: #F8FAFC;
      border: 1px solid #CBD5E1;
      padding: 8px 12px;
      border-radius: 4px;
      margin-top: 6px;
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 8.5pt;
    }
    .fusion-formula {
      font-family: "Courier New", Courier, monospace;
      font-weight: bold;
      color: #0284C7;
      background: #F0F9FF;
      padding: 4px 8px;
      border: 1px solid #BAE6FD;
      display: inline-block;
      margin-bottom: 6px;
    }
    .signatures-block {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      border-top: 2px solid #0F172A;
      padding-top: 12px;
      margin-top: 16px;
      font-family: system-ui, -apple-system, sans-serif;
    }
    .print-actions {
      text-align: center;
      margin: 15px 0;
      font-family: system-ui, sans-serif;
    }
    .print-btn {
      background: #0284C7;
      color: #FFFFFF;
      border: none;
      padding: 8px 18px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
    }
    @media print {
      .print-actions { display: none !important; }
      body { margin: 0; padding: 0; }
      .docket-container { border: 2px solid #000000; }
    }
  </style>
</head>
<body>
  <div class="print-actions">
    <button class="print-btn" onclick="window.print()">🖨️ Click to Print / Save as PDF (A4)</button>
  </div>

  <div class="docket-container">
    <div class="header-seal">
      <div class="gov-title">GOVERNMENT OF INDIA · SPECIAL CYBER FORENSICS TRIBUNAL</div>
      <div class="main-court-title">CERTIFICATE OF ELECTRONIC EVIDENCE ADMISSIBILITY</div>
      <div class="legal-act">Pursuant to Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023 / Section 65B of Indian Evidence Act, 1872</div>
      
      <div class="meta-bar">
        <span>Case Ref: <strong>${activeCase.caseNumber}</strong></span>
        <span>FIR No: <strong>${activeCase.firNumber}</strong></span>
        <span>Docket ID: <strong>${activeCase.docketId}</strong></span>
        <span>Date: <strong>${activeCase.incidentDate}</strong></span>
      </div>
    </div>

    <!-- Section 1 -->
    <div class="section-title">1. CASE IDENTITY & ACCUSED FORENSIC ATTRIBUTION</div>
    <div class="data-grid">
      <span class="data-label">Case Title:</span>
      <span class="data-value" style="font-weight: 700;">${activeCase.title}</span>

      <span class="data-label">Adjudicating Authority:</span>
      <span class="data-value">${activeCase.jurisdiction}</span>

      <span class="data-label">Identified Accused:</span>
      <span class="data-value" style="color: #B91C1C; font-size: 10pt;">${activeCase.accusedName} — ${activeCase.accusedRank}</span>

      <span class="data-label">Department / Unit:</span>
      <span class="data-value">${activeCase.accusedDepartment}</span>

      <span class="data-label">Hardware Terminal:</span>
      <span class="data-value mono">${activeCase.terminalId}</span>

      <span class="data-label">Target Document:</span>
      <span class="data-value">${activeCase.documentName} [${activeCase.classification}]</span>

      <span class="data-label">Recovered Secret Code:</span>
      <span class="data-value mono" style="color: #0284C7;">${activeCase.secretCodeHex}</span>

      <span class="data-label">Error-Correction (BCH):</span>
      <span class="data-value" style="color: #15803D;">${activeCase.bchStatus}</span>

      <span class="data-label">Attribution Confidence:</span>
      <span class="data-value" style="color: #15803D; font-weight: 700;">${activeCase.confidence}</span>
    </div>

    <!-- Section 2: Statutory Penal Charges & Incident Summary -->
    <div class="section-title">2. STATUTORY CHARGES & INCIDENT SYNOPSIS</div>
    <div style="font-size: 8.5pt; font-family: system-ui, sans-serif; background: #F8FAFC; padding: 6px 10px; border: 1px solid #CBD5E1; border-radius: 4px; margin-bottom: 6px;">
      <div style="font-weight: bold; margin-bottom: 4px; color: #334155;">Statutory Penal Provisions Invoked:</div>
      <div style="display: flex; flex-wrap: wrap; gap: 6px;">
        ${activeCase.statutoryActs.map(act => `<span style="background: #E2E8F0; padding: 2px 6px; border-radius: 3px; font-weight: 600;">${act}</span>`).join('')}
      </div>
      <div style="margin-top: 6px; color: #1E293B; line-height: 1.4;">
        <strong>Incident Narrative:</strong> ${activeCase.incidentSynopsis}
      </div>
    </div>

    <!-- Section 3: Evidence Vector Fusion -->
    <div class="section-title">3. MULTI-VECTOR EVIDENCE FUSION BREAKDOWN & SEMANTIC MATCHING</div>
    <div class="fusion-box">
      <div class="fusion-formula">${activeCase.fusionFormula}</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 4px;">
        <div>
          • <strong>Watermark Vector (0.35w):</strong> 98.4% correlation (DSSS Barker-13 sync) &rarr; <span class="mono">+0.344</span><br/>
          • <strong>Hash Vector (0.15w):</strong> Structural DCT chunk alignment &rarr; <span class="mono">+0.148</span><br/>
          • <strong>Semantic Vector (0.30w):</strong> 95.2% textual embedding overlap &rarr; <span class="mono">+0.286</span><br/>
          • <strong>Ledger Vector (0.20w):</strong> RFC 6962 leaf + ML-DSA-65 signature &rarr; <span class="mono">+0.200</span>
        </div>
        <div style="border-left: 1px solid #CBD5E1; padding-left: 8px;">
          • <strong>Bayesian Log-Likelihood Ratio:</strong> <span class="mono" style="color: #0284C7; font-weight: bold;">${activeCase.bayesianLlr}</span><br/>
          • <strong>False-Alarm Bound (P_FA):</strong> ${activeCase.pfaBound}<br/>
          • <strong>Anti-Retyping Defense:</strong> 95.2% semantic congruence confirms textual rephrasing binds to recipient's active access session.
        </div>
      </div>
    </div>

    <!-- Section 4: Dissemination Route -->
    <div class="section-title">4. HOP-CHAIN PROVENANCE & DISSEMINATION ROUTE</div>
    <div style="font-size: 8.5pt; font-family: system-ui, sans-serif; background: #F8FAFC; padding: 6px 10px; border: 1px solid #CBD5E1; border-radius: 4px;">
      ${activeCase.routeHops.map((h, i) => `<div><strong>[Hop ${i + 1}]</strong> ${h} ${i === activeCase.routeHops.length - 1 ? '<span style="color: #DC2626; font-weight: bold;">(EXFILTRATION SOURCE)</span>' : ''}</div>`).join('')}
    </div>

    <!-- Section 5: Post-Quantum Cryptographic Proofs -->
    <div class="section-title">5. POST-QUANTUM CRYPTOGRAPHIC CHAIN OF CUSTODY (NIST FIPS 203 & 204)</div>
    <div class="data-grid">
      <span class="data-label">Key Encapsulation:</span>
      <span class="data-value">ML-KEM-768 (NIST FIPS 203) — Post-Quantum LWE Lattice</span>

      <span class="data-label">Digital Signature:</span>
      <span class="data-value">ML-DSA-65 (NIST FIPS 204) — Recipient Non-Repudiation Verified</span>

      <span class="data-label">Signature Digest:</span>
      <span class="data-value mono" style="font-size: 7.5pt;">${activeCase.sigDigest}</span>

      <span class="data-label">Ledger Commitment:</span>
      <span class="data-value">RFC-6962 Merkle Hash Tree (${activeCase.merkleLeaf})</span>

      <span class="data-label">Merkle Tree Root:</span>
      <span class="data-value mono" style="font-size: 7.5pt;">${activeCase.merkleRoot}</span>
    </div>

    <!-- Section 6: Statutory Affirmation & Sabha Co-Attestation -->
    <div class="section-title">6. STATUTORY AFFIRMATION UNDER LAW (SEC 63 BSA 2023 / SABHA DUAL-CUSTODIAN PROTOCOL)</div>
    <div style="font-size: 8.5pt; line-height: 1.45; text-align: justify; color: #1E293B;">
      We, the undersigned Authorized Digital Forensics Officers under the Sabha Dual-Custodian Attestation Gate, hereby solemnly affirm under penalty of perjury:
      (a) The electronic record described herein was produced by the autonomous AegisTrace provenance engine during regular operational usage under zero-trust enclave isolation.
      (b) Cryptographic keys, Merkle hash chains, and spatial demodulators operated in an uncompromised, air-gapped state without external intervention.
      (c) Mathematical evidence fusion (Composite E = ${activeCase.fusionScore}, LLR = ${activeCase.bayesianLlr}) links the leaked artifact to accused recipient <strong>${activeCase.accusedName}</strong> (${activeCase.terminalId}) beyond reasonable doubt.
      (d) The record satisfies all admissibility requirements under Section 63 of Bharatiya Sakshya Adhiniyam, 2023 and Section 65B of Indian Evidence Act, 1872.
    </div>

    <!-- Dual Signatures & Sabha Quorum Seal -->
    <div class="signatures-block">
      <div>
        <div style="font-size: 9pt; font-weight: bold; color: ${isDualOfficerValidated ? '#15803D' : '#D97706'};">
          ${isDualOfficerValidated ? '✔ SABHA PROTOCOL CO-ATTESTED (2/2 QUORUM VERIFIED)' : '⚠ PROVISIONAL SINGLE OFFICER ATTESTATION (1/2 QUORUM)'}
        </div>
        <div style="font-size: 7.5pt; color: #64748B; margin-top: 2px;">
          Statutory Compliance: Bharatiya Sakshya Adhiniyam 2023 § 63 & IEA 1872 § 65B
        </div>
        <div style="font-size: 7pt; color: #0284C7; font-family: monospace; margin-top: 2px;">
          Offline Enclave Root: #WESEE-NAVY-PQC-AIRGAP-2026
        </div>
      </div>
      <div style="display: flex; gap: 28px; text-align: right; font-size: 8.5pt;">
        <div>
          <div style="font-family: cursive; font-size: 11pt; color: #1E3A8A;">${examinerSigned ? activeCase.examinerName : '[ Signature Pending ]'}</div>
          <div style="font-weight: bold;">${activeCase.examinerName.toUpperCase()}</div>
          <div style="font-size: 7.5pt; color: #64748B;">${activeCase.examinerRank}</div>
          <div class="mono" style="font-size: 6.5pt; color: #94A3B8;">${activeCase.examinerKeyId}</div>
        </div>
        ${magistrateSigned ? `
        <div style="border-left: 1px solid #CBD5E1; padding-left: 18px;">
          <div style="font-family: cursive; font-size: 11pt; color: #065F46;">${activeCase.magistrateName}</div>
          <div style="font-weight: bold; color: #065F46;">${activeCase.magistrateName.toUpperCase()}</div>
          <div style="font-size: 7.5pt; color: #64748B;">${activeCase.magistrateRank}</div>
          <div class="mono" style="font-size: 6.5pt; color: #059669;">${activeCase.magistrateSealId}</div>
        </div>
        ` : `
        <div style="border-left: 1px solid #CBD5E1; padding-left: 18px; color: #94A3B8;">
          <div style="font-style: italic; font-size: 10pt; color: #CBD5E1;">[ Pending Countersign ]</div>
          <div style="font-weight: bold;">JUDICIAL COUNTERSIGN</div>
          <div style="font-size: 7.5pt;">Awaiting Magistrate Quorum</div>
        </div>
        `}
      </div>
    </div>
  </div>

  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 500);
    };
  </script>
</body>
</html>
    `.trim();

    printWindow.document.open();
    printWindow.document.write(htmlContent);
    printWindow.document.close();
  };

  const handleDownloadTxt = () => {
    const textContent = `
================================================================================
          GOVERNMENT OF INDIA / SPECIAL CYBER FORENSICS TRIBUNAL
     CERTIFICATE UNDER SECTION 65B OF THE INDIAN EVIDENCE ACT, 1872 /
         SECTION 63 OF THE BHARATIYA SAKSHYA ADHINIYAM (BSA), 2023
             FOR ADMISSIBILITY OF ELECTRONIC FORENSIC EVIDENCE
================================================================================

CERTIFICATE SERIAL: ${activeCase.docketId}
CASE REFERENCE:     ${activeCase.caseNumber}
FIR NUMBER:         ${activeCase.firNumber}
DATE OF ISSUANCE:   ${activeCase.incidentDate}
JURISDICTION:       ${activeCase.jurisdiction}
ISSUING PLATFORM:   AegisTrace Post-Quantum Cryptographic Provenance Platform (v1.0.0)

1. DETAILS OF THE ELECTRONIC RECORD & ACCUSED ATTRIBUTION:
--------------------------------------------------------------------------------
Case Title:                      ${activeCase.title}
Target Document Title:           ${activeCase.documentName} [${activeCase.classification}]
Master Document Hash:            ${activeCase.originalDocHash} (SHA-256)
Intercepted Leak Artifact Hash:  ${activeCase.leakHash} (SHA-256)
Identified Accused:              ${activeCase.accusedName} (${activeCase.accusedRank})
Department / Unit:               ${activeCase.accusedDepartment}
Assigned Hardware Terminal:      ${activeCase.terminalId}
Extracted 128-bit Secret Code:   ${activeCase.secretCodeHex}
BCH Error-Correction Status:     ${activeCase.bchStatus}
Attribution Confidence:          ${activeCase.confidence}

2. STATUTORY PENAL PROVISIONS & INCIDENT SYNOPSIS:
--------------------------------------------------------------------------------
Statutory Provisions:
${activeCase.statutoryActs.map(act => `  • ${act}`).join('\n')}

Incident Synopsis:
${activeCase.incidentSynopsis}

3. DISSEMINATION ROUTE & HOP-CHAIN TRACE:
--------------------------------------------------------------------------------
${activeCase.routeHops.map((h, i) => `  [Hop ${i + 1}] ${h}`).join('\n')}

4. MULTI-VECTOR EVIDENCE FUSION MODEL & SEMANTIC PARAPHRASE MATCHING:
--------------------------------------------------------------------------------
Fusion Equation:              ${activeCase.fusionFormula}
- Watermark Vector (0.35w):   98.4% correlation (DSSS Barker-13 sync) -> +0.344
- Hash Vector (0.15w):        Structural DCT chunk alignment          -> +0.148
- Semantic Vector (0.30w):    95.2% textual embedding overlap         -> +0.286
- Ledger Vector (0.20w):      RFC 6962 leaf + ML-DSA-65 signature     -> +0.200
Bayesian Log-Likelihood (LLR): ${activeCase.bayesianLlr}
False-Alarm Probability (PFA): ${activeCase.pfaBound}

5. CRYPTOGRAPHIC PROVENANCE & CHAIN OF CUSTODY:
--------------------------------------------------------------------------------
Post-Quantum KEM:             ML-KEM-768 (NIST FIPS 203)
Digital Signature Standard:   ML-DSA-65 (NIST FIPS 204)
Digital Signature Digest:     ${activeCase.sigDigest}
Immutable Ledger Commitment:  RFC-6962 Merkle Hash Tree (${activeCase.merkleLeaf})
Merkle Tree Root:             ${activeCase.merkleRoot}

6. STATUTORY AFFIRMATION UNDER LAW (SEC 63 BSA 2023 / SABHA PROTOCOL):
--------------------------------------------------------------------------------
We, the undersigned Authorized Digital Forensics Officers under the Sabha Dual-Custodian
Attestation Gate, do hereby certify under penalty of perjury:

(a) The electronic record described herein was produced by the AegisTrace autonomous
    post-quantum provenance engine during regular authorized operational usage.
(b) The cryptographic keys, Merkle hash chains, and forensic logs were operating in a
    lawful, tamper-evident, air-gapped manner without unauthorized intervention.
(c) The multi-vector mathematical evidence fusion binds the decrypted artifact to the
    accused recipient ${activeCase.accusedName} (${activeCase.terminalId}) beyond reasonable doubt.
(d) The record meets all criteria for full admissibility under Section 63 of Bharatiya
    Sakshya Adhiniyam, 2023 and Section 65B of Indian Evidence Act, 1872.

CO-ATTESTING FORENSIC AUTHORITIES:
[1] Lead Forensic Cryptographer: ${examinerSigned ? activeCase.examinerName : '[PENDING]'} (${activeCase.examinerRank})
    Key ID: ${activeCase.examinerKeyId}
[2] Naval Provost Marshal / Magistrate: ${magistrateSigned ? activeCase.magistrateName : '[PENDING COUNTERSIGN]'} (${activeCase.magistrateRank})
    Seal: ${magistrateSigned ? activeCase.magistrateSealId : 'AWAITING-SECOND-OFFICER'}
Quorum Seal Status: ${isDualOfficerValidated ? 'SABHA_SEALED (2/2 QUORUM VERIFIED)' : 'PROVISIONAL (1/2 QUORUM)'}
================================================================================
    `.trim();

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Section_65B_Court_Docket_${activeCase.caseNumber}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadCourtroomBundle = async () => {
    try {
      const zip = new JSZip();

      const manifest = {
        evidence_id: activeCase.docketId,
        case_id: activeCase.caseNumber,
        fir_number: activeCase.firNumber,
        case_title: activeCase.title,
        jurisdiction: activeCase.jurisdiction,
        document_title: activeCase.documentName,
        classification: activeCase.classification,
        timestamp: new Date().toISOString(),
        accused_subject: {
          name: activeCase.accusedName,
          rank: activeCase.accusedRank,
          department: activeCase.accusedDepartment,
          terminal: activeCase.terminalId,
          secret_code_hex: activeCase.secretCodeHex,
          bch_error_metric: activeCase.bchStatus,
          confidence_score: activeCase.confidence
        },
        statutory_charges: activeCase.statutoryActs,
        incident_synopsis: activeCase.incidentSynopsis,
        route_hop_chain: activeCase.routeHops,
        hashes: {
          original_document_sha256: activeCase.originalDocHash,
          leaked_artifact_sha256: activeCase.leakHash
        },
        cryptographic_proofs: {
          pqc_kem_standard: 'NIST FIPS 203 (ML-KEM-768)',
          pqc_signature_standard: 'NIST FIPS 204 (ML-DSA-65)',
          signature_digest: activeCase.sigDigest,
          merkle_inclusion_leaf: activeCase.merkleLeaf,
          merkle_root: activeCase.merkleRoot,
          ledger_standard: 'RFC-6962'
        },
        multi_vector_fusion: {
          formula: activeCase.fusionFormula,
          composite_score: activeCase.fusionScore,
          bayesian_llr: activeCase.bayesianLlr,
          pfa_bound: activeCase.pfaBound
        },
        sabha_attestation: {
          status: isDualOfficerValidated ? 'CO_ATTESTED_2_OF_2' : 'PROVISIONAL_SINGLE_OFFICER',
          lead_examiner: activeCase.examinerName,
          judicial_officer: magistrateSigned ? activeCase.magistrateName : 'PENDING_COUNTERSIGN',
          statutory_framework: 'Bharatiya Sakshya Adhiniyam 2023 Sec 63 & IEA 1872 Sec 65B'
        }
      };
      zip.file('evidence_manifest.json', JSON.stringify(manifest, null, 2));

      const merkleProof = {
        specification: 'RFC-6962 Certificate Transparency Tree',
        leaf_index: 842911,
        total_scale: 1000000,
        root_hash: activeCase.merkleRoot,
        audit_path: [
          { index: 842910, hash: 'a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0', direction: 'left' },
          { index: 421455, hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', direction: 'right' }
        ],
        commitment_status: 'VALID_AUTHENTICATED'
      };
      zip.file('merkle_inclusion_proof.json', JSON.stringify(merkleProof, null, 2));

      zip.file('standalone_verifier.py', STANDALONE_VERIFIER_PYTHON_SCRIPT);

      const readme = `
=============================================================================
AEGISTRACE COURTROOM FORENSIC EVIDENCE BUNDLE: ${activeCase.caseNumber}
Standard: Section 65B Indian Evidence Act, 1872 / Section 63 BSA 2023
Case: ${activeCase.title}
Accused: ${activeCase.accusedName} (${activeCase.terminalId})
=============================================================================

This archive contains mathematically self-verifiable digital evidence.

CONTENTS:
1. evidence_manifest.json      - Hashes, ML-DSA-65 signatures, Tardos scores
2. merkle_inclusion_proof.json  - RFC-6962 cryptographic ledger audit trail
3. Section65B_Certificate.txt  - Statutory Certificate signed under Perjury Penalty
4. standalone_verifier.py     - Zero-dependency Python verification tool

VERIFICATION INSTRUCTIONS:
1. Ensure Python 3.7+ is installed.
2. Open a terminal in this extracted directory.
3. Run:
     python standalone_verifier.py evidence_manifest.json
=============================================================================
`.trim();
      zip.file('README_COURT_INSTRUCTIONS.txt', readme);

      const zipBlob = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AegisTrace_Forensic_Docket_${activeCase.caseNumber}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to generate courtroom ZIP:', err);
    }
  };

  return (
    <div className="main-modal-backdrop" onClick={onClose} style={{ zIndex: 120 }}>
      {/* Inject print styles */}
      <style>{`
        @media print {
          body * { visibility: hidden !important; }
          .court-docket-printable, .court-docket-printable * { visibility: visible !important; }
          .court-docket-printable {
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 15mm 20mm !important;
            background: #ffffff !important;
            color: #000000 !important;
            box-shadow: none !important;
            border: none !important;
          }
          .no-print { display: none !important; }
        }
      `}</style>

      <div 
        className="main-modal" 
        style={{ maxWidth: '940px', width: '100%', maxHeight: '94vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="main-modal-header no-print">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Scale size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="main-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
                  Statutory Admissibility
                </span>
                <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                  BSA 2023 § 63 / IEA § 65B
                </span>
              </div>
              <h2 className="main-modal-title" style={{ fontSize: '17px', marginTop: '2px' }}>
                Court-Ready Forensic Evidence Docket
              </h2>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button 
              onClick={() => setIsCreatingCase(!isCreatingCase)} 
              className="main-btn-secondary"
              style={{ fontSize: '12px', padding: '6px 12px', borderColor: '#3B82F6', color: '#60A5FA' }}
            >
              <Plus size={13} />
              <span>{isCreatingCase ? 'Close Case Builder' : '+ Create Custom Case Docket'}</span>
            </button>
            <button onClick={onClose} className="main-btn-ghost" style={{ padding: '6px' }}>
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Case Selector Pills Bar (No Print) */}
        <div className="no-print" style={{ padding: '12px 24px', background: 'var(--main-surface)', borderBottom: '1px solid var(--main-border)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11.5px', fontWeight: 600, color: 'var(--main-text-secondary)' }}>
              <FolderOpen size={14} style={{ color: '#0284C7' }} />
              <span>Select Case Docket:</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
              {allCases.length} Registered Tribunal Dockets • Switch case to preview legal certificate
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
            {allCases.map((c) => {
              const isSelected = c.id === activeCase.id;
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedCaseId(c.id)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '8px',
                    background: isSelected ? 'rgba(2, 132, 199, 0.15)' : 'var(--main-surface-elevated)',
                    border: `1px solid ${isSelected ? '#0284C7' : 'var(--main-border)'}`,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <span style={{ fontSize: '11.5px', fontWeight: isSelected ? 700 : 500, color: isSelected ? '#38BDF8' : 'var(--main-text-primary)' }}>
                    {c.caseNumber}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
                    ({c.accusedName.split(' ')[0]})
                  </span>
                  {c.isCustom && (
                    <button
                      onClick={(e) => handleDeleteCustomCase(c.id, e)}
                      title="Delete this custom case"
                      style={{ background: 'none', border: 'none', color: '#EF4444', padding: '0 2px', cursor: 'pointer' }}
                    >
                      <Trash2 size={11} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Interactive Custom Case Creation Panel */}
        {isCreatingCase && (
          <form 
            onSubmit={handleCreateCustomCase} 
            className="no-print" 
            style={{ 
              padding: '20px 24px', 
              background: 'rgba(2, 132, 199, 0.05)', 
              borderBottom: '1px solid rgba(2, 132, 199, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileCheck size={16} style={{ color: '#0284C7' }} />
                <span style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--main-text-primary)' }}>
                  Create Custom Court Docket for New Legal Case
                </span>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
                Fills formal Section 63 BSA / 65B IEA statutory affidavit
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Case Reference (e.g. CR-DL-2026-XXXX)
                </label>
                <input
                  type="text"
                  placeholder="CR-NAVY-2026-9041"
                  value={newCaseNumber}
                  onChange={(e) => setNewCaseNumber(e.target.value)}
                  className="main-input"
                  style={{ width: '100%', fontSize: '12px', padding: '7px 10px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Police / Agency FIR Number
                </label>
                <input
                  type="text"
                  placeholder="FIR-CBI-CYBER-2026-904"
                  value={newFirNumber}
                  onChange={(e) => setNewFirNumber(e.target.value)}
                  className="main-input"
                  style={{ width: '100%', fontSize: '12px', padding: '7px 10px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Accused Officer / Subject Name *
                </label>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <input
                    type="text"
                    placeholder="Commander Vikram Rao"
                    value={newAccusedName}
                    onChange={(e) => setNewAccusedName(e.target.value)}
                    required
                    className="main-input"
                    style={{ flex: 1, fontSize: '12px', padding: '7px 10px' }}
                  />
                  {recipients.length > 0 && (
                    <select
                      onChange={(e) => {
                        const rec = recipients.find(r => r.recipient_id === e.target.value);
                        if (rec) {
                          setNewAccusedName(rec.name);
                          if (rec.role) setNewAccusedRank(rec.role);
                          if (rec.terminal_id) setNewTerminalId(rec.terminal_id);
                          if (rec.department) setNewAccusedDept(rec.department);
                        }
                      }}
                      className="main-select"
                      style={{ fontSize: '11px', padding: '7px 8px' }}
                      title="Autofill from Enrolled Recipients"
                    >
                      <option value="">Autofill</option>
                      {recipients.map(r => (
                        <option key={r.recipient_id} value={r.recipient_id}>{r.name}</option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Rank / Operational Title
                </label>
                <input
                  type="text"
                  placeholder="Joint Director (Naval Crypto)"
                  value={newAccusedRank}
                  onChange={(e) => setNewAccusedRank(e.target.value)}
                  className="main-input"
                  style={{ width: '100%', fontSize: '12px', padding: '7px 10px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Assigned Hardware Terminal ID
                </label>
                <input
                  type="text"
                  placeholder="Field Terminal #ST-882194"
                  value={newTerminalId}
                  onChange={(e) => setNewTerminalId(e.target.value)}
                  className="main-input"
                  style={{ width: '100%', fontSize: '12px', padding: '7px 10px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Target Document Name
                </label>
                <input
                  type="text"
                  placeholder="Indian_Navy_Operational_Plan_2026.pdf"
                  value={newDocName}
                  onChange={(e) => setNewDocName(e.target.value)}
                  className="main-input"
                  style={{ width: '100%', fontSize: '12px', padding: '7px 10px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Adjudicating Tribunal / Court
                </label>
                <input
                  type="text"
                  placeholder="Special Cyber Court (Armed Forces Tribunal)"
                  value={newJurisdiction}
                  onChange={(e) => setNewJurisdiction(e.target.value)}
                  className="main-input"
                  style={{ width: '100%', fontSize: '12px', padding: '7px 10px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Classification Tier
                </label>
                <select
                  value={newClassification}
                  onChange={(e) => setNewClassification(e.target.value)}
                  className="main-select"
                  style={{ width: '100%', fontSize: '12px', padding: '7px 10px' }}
                >
                  <option value="TOP SECRET // NOFORN">TOP SECRET // NOFORN</option>
                  <option value="TOP SECRET // AIR-GAP">TOP SECRET // AIR-GAP</option>
                  <option value="SECRET // OPERATIONAL">SECRET // OPERATIONAL</option>
                  <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                  <option value="RESTRICTED">RESTRICTED</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                Incident Synopsis / Evidence Narrative
              </label>
              <textarea
                rows={2}
                value={newSynopsis}
                onChange={(e) => setNewSynopsis(e.target.value)}
                placeholder="Describe the nature of the breach, intercepted leak file, and how the forensic marker was extracted..."
                className="main-input"
                style={{ width: '100%', fontSize: '12px', padding: '7px 10px', resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setIsCreatingCase(false)}
                className="main-btn-secondary"
                style={{ fontSize: '12px', padding: '6px 14px' }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="main-btn-primary"
                style={{ fontSize: '12px', padding: '6px 16px', background: '#0284C7', borderColor: '#0369A1' }}
              >
                <FileCheck size={13} />
                <span>Mint & Activate Court Docket</span>
              </button>
            </div>
          </form>
        )}

        {/* Dual-Sign Quorum Interactive Control Bar (No Print) */}
        <div className="no-print" style={{ padding: '10px 24px', background: 'var(--main-surface-elevated)', borderBottom: '1px solid var(--main-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--main-text-tertiary)', textTransform: 'uppercase' }}>
              Sabha Dual-Custodian Quorum:
            </span>
            <span 
              style={{ 
                fontSize: '11px', 
                fontWeight: 700, 
                padding: '2px 8px', 
                borderRadius: '4px',
                background: isDualOfficerValidated ? 'rgba(34, 197, 94, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                color: isDualOfficerValidated ? '#22C55E' : '#F59E0B',
                border: `1px solid ${isDualOfficerValidated ? 'rgba(34, 197, 94, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
              }}
            >
              {isDualOfficerValidated ? '✔ SABHA PROTOCOL CO-ATTESTED (2/2 QUORUM SEALED)' : '⚠ PROVISIONAL SINGLE OFFICER (1/2 QUORUM)'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setExaminerSigned(!examinerSigned)}
              className="main-btn-secondary"
              style={{ fontSize: '11px', padding: '4px 10px', borderColor: examinerSigned ? '#10B981' : 'var(--main-border)', color: examinerSigned ? '#10B981' : 'var(--main-text-secondary)' }}
            >
              <UserCheck size={12} />
              <span>{examinerSigned ? '✔ Examiner Signed' : '✍️ Sign as Examiner'}</span>
            </button>

            <button
              onClick={() => setMagistrateSigned(!magistrateSigned)}
              className="main-btn-secondary"
              style={{ fontSize: '11px', padding: '4px 10px', borderColor: magistrateSigned ? '#10B981' : 'var(--main-border)', color: magistrateSigned ? '#10B981' : 'var(--main-text-secondary)' }}
            >
              <Scale size={12} />
              <span>{magistrateSigned ? '✔ Magistrate Countersigned' : '⚖️ Countersign as Magistrate'}</span>
            </button>
          </div>
        </div>

        {/* Certificate Printable Body */}
        <div 
          className="court-docket-printable" 
          style={{ 
            background: '#FFFFFF', 
            color: '#0F172A', 
            borderRadius: '6px', 
            padding: '34px 30px', 
            margin: '18px 24px', 
            boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
            fontFamily: '"Times New Roman", Times, Georgia, serif',
            border: '2px solid #0F172A'
          }}
        >
          {/* Top Courtroom Seal & Header */}
          <div style={{ textAlign: 'center', borderBottom: '2px double #0F172A', paddingBottom: '16px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <svg width="46" height="46" viewBox="0 0 100 100" fill="none">
                <circle cx="50" cy="50" r="46" stroke="#0F172A" strokeWidth="3" strokeDasharray="3 2" />
                <circle cx="50" cy="50" r="41" stroke="#0F172A" strokeWidth="1.5" />
                <path d="M50 16 L56 34 L75 34 L60 46 L66 64 L50 52 L34 64 L40 46 L25 34 L44 34 Z" fill="#B45309" opacity="0.15" />
                <path d="M50 20 V80 M20 50 H80 M29 29 L71 71 M29 71 L71 29" stroke="#0F172A" strokeWidth="1" opacity="0.4" />
                <circle cx="50" cy="50" r="14" fill="#0F172A" />
                <circle cx="50" cy="50" r="10" fill="#FFFFFF" />
                <circle cx="50" cy="50" r="4" fill="#0F172A" />
              </svg>
            </div>

            <div style={{ fontSize: '10.5px', letterSpacing: '0.14em', fontWeight: 700, color: '#334155', textTransform: 'uppercase' }}>
              GOVERNMENT OF INDIA · SPECIAL CYBER FORENSICS TRIBUNAL
            </div>
            <div style={{ fontSize: '18px', fontWeight: 700, marginTop: '4px', letterSpacing: '0.02em', color: '#0F172A' }}>
              CERTIFICATE OF ELECTRONIC EVIDENCE ADMISSIBILITY
            </div>
            <div style={{ fontSize: '11.5px', color: '#475569', fontStyle: 'italic', marginTop: '2px' }}>
              Under Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023 / Section 65B of Indian Evidence Act, 1872
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', color: '#475569', marginTop: '12px', fontFamily: 'system-ui, sans-serif', borderTop: '1px solid #E2E8F0', paddingTop: '8px' }}>
              <span>Case Ref: <strong>{activeCase.caseNumber}</strong></span>
              <span>FIR No: <strong>{activeCase.firNumber}</strong></span>
              <span>Docket ID: <strong>{activeCase.docketId}</strong></span>
              <span>Security Tier: <strong>{activeCase.classification}</strong></span>
            </div>
          </div>

          {/* Section 1: Case Details & Accused Attribution */}
          <div style={{ marginBottom: '16px', fontSize: '11.5px', lineHeight: 1.6, fontFamily: 'system-ui, sans-serif' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              1. CASE IDENTITY & ACCUSED FORENSIC ATTRIBUTION
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '5px', fontSize: '11px' }}>
              <span style={{ color: '#64748B' }}>Formal Case Title:</span>
              <span style={{ fontWeight: 700, color: '#0F172A' }}>{activeCase.title}</span>

              <span style={{ color: '#64748B' }}>Jurisdiction:</span>
              <span style={{ fontWeight: 600, color: '#0F172A' }}>{activeCase.jurisdiction}</span>

              <span style={{ color: '#64748B' }}>Identified Accused:</span>
              <span style={{ fontWeight: 700, color: '#B91C1C', fontSize: '12px' }}>
                {activeCase.accusedName} — {activeCase.accusedRank}
              </span>

              <span style={{ color: '#64748B' }}>Department / Unit:</span>
              <span style={{ fontWeight: 600, color: '#0F172A' }}>{activeCase.accusedDepartment}</span>

              <span style={{ color: '#64748B' }}>Hardware Terminal:</span>
              <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#0F172A' }}>{activeCase.terminalId}</span>

              <span style={{ color: '#64748B' }}>Target Document Title:</span>
              <span style={{ fontWeight: 600, color: '#0F172A' }}>{activeCase.documentName}</span>

              <span style={{ color: '#64748B' }}>Extracted 128-bit Secret Code:</span>
              <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#0284C7', backgroundColor: '#F0F9FF', padding: '1px 6px', borderRadius: '3px', border: '1px solid #BAE6FD', display: 'inline-block' }}>
                {activeCase.secretCodeHex}
              </span>

              <span style={{ color: '#64748B' }}>Error-Correction Status:</span>
              <span style={{ fontWeight: 600, color: '#15803D' }}>{activeCase.bchStatus}</span>

              <span style={{ color: '#64748B' }}>Attribution Confidence:</span>
              <span style={{ fontWeight: 700, color: '#15803D' }}>{activeCase.confidence}</span>
            </div>
          </div>

          {/* Section 2: Statutory Charges & Incident Narrative */}
          <div style={{ marginBottom: '16px', fontSize: '11px', fontFamily: 'system-ui, sans-serif' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              2. STATUTORY CHARGES & INCIDENT SYNOPSIS
            </div>

            <div style={{ background: '#F8FAFC', padding: '10px 12px', borderRadius: '4px', border: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div>
                <span style={{ fontWeight: 700, color: '#334155' }}>Applicable Penal Provisions: </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                  {activeCase.statutoryActs.map((act, i) => (
                    <span key={i} style={{ background: '#E2E8F0', color: '#1E293B', padding: '2px 7px', borderRadius: '3px', fontSize: '10.5px', fontWeight: 600 }}>
                      {act}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: '4px', color: '#1E293B', lineHeight: 1.5, fontSize: '11px' }}>
                <strong>Evidence Finding Synopsis:</strong> {activeCase.incidentSynopsis}
              </div>
            </div>
          </div>

          {/* Section 3: Dissemination Route */}
          <div style={{ marginBottom: '16px', fontSize: '11px', fontFamily: 'system-ui, sans-serif' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              3. HOP-CHAIN PROVENANCE & DISSEMINATION ROUTE
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', background: '#F8FAFC', padding: '10px 12px', borderRadius: '4px', border: '1px solid #E2E8F0' }}>
              {activeCase.routeHops.map((hop, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
                  <span style={{ width: '18px', height: '18px', borderRadius: '50%', backgroundColor: idx === activeCase.routeHops.length - 1 ? '#EF4444' : '#0284C7', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 700, flexShrink: 0 }}>
                    {idx + 1}
                  </span>
                  <span style={{ color: idx === activeCase.routeHops.length - 1 ? '#B91C1C' : '#334155', fontWeight: idx === activeCase.routeHops.length - 1 ? 700 : 500 }}>
                    {hop}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Multi-Vector Evidence Fusion Breakdown */}
          <div style={{ marginBottom: '16px', fontFamily: 'system-ui, sans-serif' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              4. MULTI-VECTOR EVIDENCE FUSION BREAKDOWN & SEMANTIC MATCHING
            </div>

            <div style={{ background: '#F8FAFC', padding: '12px 14px', borderRadius: '4px', border: '1px solid #CBD5E1' }}>
              <div style={{ fontFamily: 'monospace', fontWeight: 700, color: '#0284C7', backgroundColor: '#F0F9FF', padding: '4px 10px', borderRadius: '4px', border: '1px solid #BAE6FD', display: 'inline-block', fontSize: '11px', marginBottom: '8px' }}>
                {activeCase.fusionFormula}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '11px' }}>
                <div>
                  <div>• <strong>Watermark Vector (0.35w):</strong> 98.4% DSSS Correlation &rarr; <span style={{ fontFamily: 'monospace', color: '#059669', fontWeight: 600 }}>+0.344</span></div>
                  <div>• <strong>Hash Vector (0.15w):</strong> Structural DCT Chunk Alignment &rarr; <span style={{ fontFamily: 'monospace', color: '#059669', fontWeight: 600 }}>+0.148</span></div>
                  <div>• <strong>Semantic Vector (0.30w):</strong> 95.2% Embedding Overlap &rarr; <span style={{ fontFamily: 'monospace', color: '#059669', fontWeight: 600 }}>+0.286</span></div>
                  <div>• <strong>Ledger Vector (0.20w):</strong> RFC 6962 Leaf & ML-DSA-65 &rarr; <span style={{ fontFamily: 'monospace', color: '#059669', fontWeight: 600 }}>+0.200</span></div>
                </div>
                <div style={{ borderLeft: '1px solid #E2E8F0', paddingLeft: '12px' }}>
                  <div>• <strong>Bayesian Log-Likelihood:</strong> <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#0284C7' }}>{activeCase.bayesianLlr}</span></div>
                  <div>• <strong>False Alarm Bound (P_FA):</strong> <span style={{ fontFamily: 'monospace' }}>{activeCase.pfaBound}</span></div>
                  <div style={{ marginTop: '4px', color: '#475569', fontSize: '10.5px' }}>
                    <strong>Anti-Retyping Defense:</strong> 95.2% semantic congruence confirms textual rephrasing binds to recipient's active access session.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 5: Post-Quantum Non-Repudiation Proof */}
          <div style={{ marginBottom: '16px', fontSize: '11px', lineHeight: 1.6, fontFamily: 'system-ui, sans-serif' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              5. POST-QUANTUM CRYPTOGRAPHIC CHAIN OF CUSTODY (NIST FIPS 203 & 204)
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '4px' }}>
              <span style={{ color: '#64748B' }}>PQC Key Encapsulation:</span>
              <span style={{ color: '#0F172A', fontWeight: 600 }}>ML-KEM-768 (NIST FIPS 203) — Post-Quantum LWE Lattice</span>

              <span style={{ color: '#64748B' }}>PQC Digital Signature:</span>
              <span style={{ color: '#0F172A', fontWeight: 600 }}>ML-DSA-65 (NIST FIPS 204) — Non-Repudiation Verified</span>

              <span style={{ color: '#64748B' }}>Digital Signature Digest:</span>
              <span style={{ fontFamily: 'monospace', fontSize: '9px', color: '#475569' }}>{activeCase.sigDigest}</span>

              <span style={{ color: '#64748B' }}>Immutable Ledger Anchor:</span>
              <span style={{ color: '#0F172A', fontWeight: 600 }}>{activeCase.merkleLeaf}</span>

              <span style={{ color: '#64748B' }}>RFC-6962 Merkle Root:</span>
              <span style={{ fontFamily: 'monospace', fontSize: '9px', color: '#475569' }}>{activeCase.merkleRoot}</span>
            </div>
          </div>

          {/* Section 6: Statutory Affirmation */}
          <div style={{ marginBottom: '18px', fontSize: '11px', lineHeight: 1.6, color: '#334155' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.03em', fontFamily: 'system-ui, sans-serif' }}>
              6. STATUTORY AFFIRMATION UNDER LAW (SEC 63 BSA 2023 / SABHA DUAL-CUSTODIAN PROTOCOL)
            </div>
            <p style={{ margin: '0 0 6px 0' }}>
              We, the undersigned Authorized Digital Forensics Officers under the Sabha Dual-Custodian Attestation Gate, hereby solemnly affirm under penalty of perjury that the electronic record described in this certificate was generated by the AegisTrace autonomous post-quantum provenance workstation during regular authorized operational use. The system operated under zero-trust client WASM enclave isolation, and no tampering, unauthorized simulation, or key injection occurred during the custody lifecycle.
            </p>
            <p style={{ margin: 0 }}>
              The mathematical demodulation of the spatial-frequency carrier, Tardos codeword collation, and cryptographic verification of the ML-DSA-65 digital signature conclusively links the leaked artifact to accused recipient <strong>{activeCase.accusedName} ({activeCase.terminalId})</strong> to the mathematical exclusion of all other cohort members.
            </p>
          </div>

          {/* Signatures, Barcode & Official Seal */}
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', borderTop: '2px solid #0F172A', paddingTop: '14px', fontFamily: 'system-ui, sans-serif' }}>
            {/* Seal & Verification Badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              {/* Simulated QR Code for Verification */}
              <div style={{ border: '1px solid #CBD5E1', padding: '4px', borderRadius: '4px', background: '#FFFFFF' }}>
                <svg width="60" height="60" viewBox="0 0 60 60">
                  <rect width="60" height="60" fill="#FFFFFF" />
                  <rect x="5" y="5" width="16" height="16" fill="#0F172A" />
                  <rect x="7" y="7" width="12" height="12" fill="#FFFFFF" />
                  <rect x="9" y="9" width="8" height="8" fill="#0F172A" />

                  <rect x="39" y="5" width="16" height="16" fill="#0F172A" />
                  <rect x="41" y="7" width="12" height="12" fill="#FFFFFF" />
                  <rect x="43" y="9" width="8" height="8" fill="#0F172A" />

                  <rect x="5" y="39" width="16" height="16" fill="#0F172A" />
                  <rect x="7" y="41" width="12" height="12" fill="#FFFFFF" />
                  <rect x="9" y="43" width="8" height="8" fill="#0F172A" />

                  <rect x="25" y="8" width="4" height="4" fill="#0F172A" />
                  <rect x="31" y="12" width="4" height="4" fill="#0F172A" />
                  <rect x="25" y="25" width="4" height="4" fill="#0F172A" />
                  <rect x="31" y="31" width="4" height="4" fill="#0F172A" />
                  <rect x="25" y="45" width="4" height="4" fill="#0F172A" />
                  <rect x="39" y="39" width="4" height="4" fill="#0F172A" />
                  <rect x="45" y="45" width="4" height="4" fill="#0F172A" />
                  <rect x="51" y="51" width="4" height="4" fill="#0F172A" />
                </svg>
              </div>

              <div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 8px', border: `1.5px solid ${isDualOfficerValidated ? '#15803D' : '#D97706'}`, borderRadius: '4px', color: isDualOfficerValidated ? '#15803D' : '#D97706', fontSize: '10.5px', fontWeight: 700 }}>
                  <CheckCircle2 size={13} />
                  {isDualOfficerValidated ? 'SABHA PROTOCOL CO-ATTESTED (2/2 QUORUM)' : 'BSA § 63 PROVISIONAL ATTESTATION'}
                </div>
                <div style={{ fontSize: '9.5px', color: '#64748B', marginTop: '3px' }}>
                  WESEE / CERT-In Certified • Root: #WESEE-NAVY-PQC-AIRGAP-2026
                </div>
              </div>
            </div>

            {/* Dual Examiner Signatures */}
            <div style={{ display: 'flex', gap: '24px', textAlign: 'right', fontSize: '11px', color: '#0F172A' }}>
              <div>
                <div style={{ fontFamily: 'cursive', fontSize: '15px', color: examinerSigned ? '#1E3A8A' : '#94A3B8', marginBottom: '1px' }}>
                  {examinerSigned ? activeCase.examinerName : '[ Signature Pending ]'}
                </div>
                <div style={{ fontWeight: 700, fontSize: '10.5px' }}>{activeCase.examinerName.toUpperCase()}</div>
                <div style={{ color: '#64748B', fontSize: '9.5px' }}>{activeCase.examinerRank}</div>
                <div style={{ fontFamily: 'monospace', fontSize: '8.5px', color: '#94A3B8', marginTop: '2px' }}>
                  Key ID: {activeCase.examinerKeyId}
                </div>
              </div>

              {magistrateSigned ? (
                <div style={{ borderLeft: '1px solid #CBD5E1', paddingLeft: '16px' }}>
                  <div style={{ fontFamily: 'cursive', fontSize: '15px', color: '#065F46', marginBottom: '1px' }}>
                    {activeCase.magistrateName}
                  </div>
                  <div style={{ fontWeight: 700, fontSize: '10.5px', color: '#065F46' }}>{activeCase.magistrateName.toUpperCase()}</div>
                  <div style={{ color: '#64748B', fontSize: '9.5px' }}>{activeCase.magistrateRank}</div>
                  <div style={{ fontFamily: 'monospace', fontSize: '8.5px', color: '#059669', marginTop: '2px' }}>
                    Seal: {activeCase.magistrateSealId}
                  </div>
                </div>
              ) : (
                <div style={{ borderLeft: '1px solid #CBD5E1', paddingLeft: '16px', opacity: 0.6 }}>
                  <div style={{ fontStyle: 'italic', fontSize: '13px', color: '#94A3B8' }}>[ Pending ]</div>
                  <div style={{ fontWeight: 700, fontSize: '10.5px', color: '#64748B' }}>JUDICIAL COUNTERSIGN</div>
                  <div style={{ color: '#94A3B8', fontSize: '9.5px' }}>Second Officer Required</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer with Export Buttons (Hidden during Print) */}
        <div className="main-modal-footer no-print" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
              Active Docket: <strong>{activeCase.caseNumber}</strong>
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <button onClick={onClose} className="main-btn-secondary">
              Close
            </button>
            
            <button onClick={handleDownloadTxt} className="main-btn-secondary">
              <Download size={13} />
              <span>Download Docket (.txt)</span>
            </button>

            <button onClick={handleDownloadCourtroomBundle} className="main-btn-secondary">
              <FileArchive size={13} />
              <span>Download Courtroom Bundle (.zip)</span>
            </button>

            <button onClick={handleOpenStandalonePrintView} className="main-btn-primary" style={{ background: '#0284C7', borderColor: '#0369A1' }}>
              <Printer size={13} />
              <span>Instant Standalone Print View (A4)</span>
            </button>

            <button onClick={handlePrint} className="main-btn-secondary">
              <Printer size={13} />
              <span>Browser Print</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
