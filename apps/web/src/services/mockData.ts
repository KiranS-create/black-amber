import { 
  PublicRecipient, 
  DocumentRelease, 
  EvidenceEvent, 
  AttributionResult, 
  AttackTestScenario, 
  DocumentMetadata,
  DirectoryIdentity,
  DirectoryGroup,
  InvestigationRecord,
  IntegrationProviderStatus,
  EvidenceRecord
} from '../types';

export const DIRECTORY_IDENTITIES: DirectoryIdentity[] = [
  {
    identity_id: 'usr_8f7a9c2b01',
    display_name: 'Sarah Jenkins',
    email: 'sarah.jenkins@defense.enterprise.org',
    organization_id: 'org_defense_gov',
    provider: 'local_enterprise_directory',
    status: 'ACTIVE',
    department: 'Cyber Defense Operations',
    title: 'Security Operations Lead',
    tags: ['clearance_top_secret', 'incident_responder']
  },
  {
    identity_id: 'usr_3d4e5f6a02',
    display_name: 'Marcus Vance',
    email: 'marcus.vance@defense.enterprise.org',
    organization_id: 'org_defense_gov',
    provider: 'local_enterprise_directory',
    status: 'ACTIVE',
    department: 'Strategic Intelligence Division',
    title: 'Principal Cryptanalyst',
    tags: ['clearance_top_secret', 'crypto_specialist']
  },
  {
    identity_id: 'usr_1a2b3c4d03',
    display_name: 'Dr. Aris Thorne',
    email: 'aris.thorne@partner.defense.org',
    organization_id: 'org_defense_gov',
    provider: 'local_enterprise_directory',
    status: 'ACTIVE',
    department: 'Advanced Research Projects (External Partner)',
    title: 'Visiting PQC Scientist',
    tags: ['clearance_secret', 'external_partner']
  },
  {
    identity_id: 'usr_9e8d7c6b04',
    display_name: 'Elena Rostova',
    email: 'elena.rostova@contractor.defense.org',
    organization_id: 'org_defense_gov',
    provider: 'local_enterprise_directory',
    status: 'ACTIVE',
    department: 'Tactical Cryptography Contractor (Contractor)',
    title: 'Senior Hardware Security Auditor',
    tags: ['contractor', 'hardware_specialist']
  },
  {
    identity_id: 'usr_5f6e7d8c05',
    display_name: 'Jordan Lee',
    email: 'jordan.lee@defense.enterprise.org',
    organization_id: 'org_defense_gov',
    provider: 'local_enterprise_directory',
    status: 'ACTIVE',
    department: 'Legal & Compliance Office',
    title: 'Chief Compliance Counsel',
    tags: ['compliance', 'legal']
  },
  {
    identity_id: 'usr_0a1b2c3d06',
    display_name: 'David Kim',
    email: 'david.kim@defense.enterprise.org',
    organization_id: 'org_defense_gov',
    provider: 'local_enterprise_directory',
    status: 'ACTIVE',
    department: 'Executive Leadership',
    title: 'Deputy Chief of Staff',
    tags: ['executive', 'clearance_top_secret']
  }
];

export const DIRECTORY_GROUPS: DirectoryGroup[] = [
  {
    group_id: 'grp_cyber_secops',
    name: 'Cyber Incident Response Team',
    organization_id: 'org_defense_gov',
    member_count: 2,
    description: 'Active CIRT engineers authorized for high-consequence incident investigation.'
  },
  {
    group_id: 'grp_strategic_intel',
    name: 'Strategic Intelligence & Cryptanalysis',
    organization_id: 'org_defense_gov',
    member_count: 2,
    description: 'Cryptographic policy and intelligence analysis branch.'
  },
  {
    group_id: 'grp_contractors',
    name: 'External Cleared Contractors',
    organization_id: 'org_defense_gov',
    member_count: 2,
    description: 'External research and hardware auditor personnel under non-disclosure.'
  },
  {
    group_id: 'grp_exec_leadership',
    name: 'Executive Leadership & Oversight',
    organization_id: 'org_defense_gov',
    member_count: 2,
    description: 'Executive committee and general counsel for distribution authorization.'
  }
];

export const INITIAL_DOCUMENTS: DocumentMetadata[] = [
  {
    document_id: 'doc_sec_shield_99',
    document_name: 'National_Defense_Protocol_2026.pdf',
    original_document_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    size_bytes: 524288,
    mime_type: 'application/pdf',
    created_at: '2026-09-26T10:30:00Z',
    artifact_id: 'art_doc_9f86d081884c',
    classification: 'TOP_SECRET',
    owner_department: 'Cyber Defense Operations',
    owner_name: 'Sarah Jenkins',
    active_releases_count: 2,
    origin: 'REAL_BACKEND_RESULT'
  },
  {
    document_id: 'doc_qkd_spec_04',
    document_name: 'PQC_Migration_Architecture_Briefing.pdf',
    original_document_hash: '4a6b2c89f012e3456789abcdef0123456789abcdef0123456789abcdef012345',
    size_bytes: 1048576,
    mime_type: 'application/pdf',
    created_at: '2026-09-25T14:15:00Z',
    artifact_id: 'art_doc_4a6b2c89f012',
    classification: 'SECRET',
    owner_department: 'Strategic Intelligence Division',
    owner_name: 'Marcus Vance',
    active_releases_count: 1,
    origin: 'REAL_BACKEND_RESULT'
  },
  {
    document_id: 'doc_tactical_key_07',
    document_name: 'Hardware_Root_of_Trust_Audit_Report.pdf',
    original_document_hash: '7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d',
    size_bytes: 786432,
    mime_type: 'application/pdf',
    created_at: '2026-09-24T09:00:00Z',
    artifact_id: 'art_doc_7c8d9e0f1a2b',
    classification: 'CONFIDENTIAL',
    owner_department: 'Tactical Cryptography Contractor',
    owner_name: 'Elena Rostova',
    active_releases_count: 1,
    origin: 'REAL_BACKEND_RESULT'
  }
];

export const HISTORICAL_INVESTIGATIONS: InvestigationRecord[] = [
  {
    investigation_id: 'inv_20260927_001',
    artifact_id: 'art_leak_9921',
    artifact_name: 'leaked_defense_protocol_page4.png',
    suspected_document_id: 'doc_sec_shield_99',
    suspected_release_id: 'rel_20260926_001',
    state: 'ATTRIBUTED',
    candidate_id: 'bob',
    candidate_name: 'Marcus Vance',
    identity_summary: {
      identity_id: 'usr_3d4e5f6a02',
      display_name: 'Marcus Vance',
      email: 'marcus.vance@defense.enterprise.org',
      organization_id: 'org_defense_gov',
      provider: 'Microsoft Entra ID',
      status: 'ACTIVE',
      department: 'Strategic Intelligence Division',
      title: 'Principal Cryptanalyst',
      source: 'DIRECTORY'
    },
    confidence_level: 'HIGH',
    fused_score: 18.08,
    created_at: '2026-09-27T11:42:00Z',
    status: 'COMPLETED'
  },
  {
    investigation_id: 'inv_20260927_002',
    artifact_id: 'art_leak_8842',
    artifact_name: 'mobile_photograph_recapture_leak.jpg',
    suspected_document_id: 'doc_sec_shield_99',
    suspected_release_id: 'rel_20260926_001',
    state: 'ATTRIBUTED',
    candidate_id: 'bob',
    candidate_name: 'Marcus Vance',
    identity_summary: {
      identity_id: 'usr_3d4e5f6a02',
      display_name: 'Marcus Vance',
      email: 'marcus.vance@defense.enterprise.org',
      organization_id: 'org_defense_gov',
      provider: 'Microsoft Entra ID',
      status: 'ACTIVE',
      department: 'Strategic Intelligence Division',
      title: 'Principal Cryptanalyst',
      source: 'DIRECTORY'
    },
    confidence_level: 'HIGH',
    fused_score: 15.62,
    created_at: '2026-09-27T08:15:00Z',
    status: 'COMPLETED'
  },
  {
    investigation_id: 'inv_20260926_003',
    artifact_id: 'art_leak_7719',
    artifact_name: 'counterfeit_signature_payload.pdf',
    suspected_document_id: 'doc_sec_shield_99',
    state: 'ABSTAINED',
    confidence_level: 'NONE',
    fused_score: 0.0,
    created_at: '2026-09-26T16:20:00Z',
    status: 'COMPLETED'
  },
  {
    investigation_id: 'inv_20260925_004',
    artifact_id: 'art_leak_6604',
    artifact_name: 'collusion_mixed_signal_document.pdf',
    suspected_document_id: 'doc_sec_shield_99',
    state: 'CONFLICT',
    confidence_level: 'NONE',
    fused_score: 0.0,
    created_at: '2026-09-25T13:45:00Z',
    status: 'COMPLETED'
  }
];

export const EVIDENCE_RECORDS: EvidenceRecord[] = [
  {
    evidence_id: 'ev_wm_9011',
    source_channel: 'SPATIAL_DSSS',
    channel_name: 'Spatial Watermark Carrier (DSSS + ArUco 4x4)',
    suspected_candidate_id: 'bob',
    suspected_candidate_name: 'Marcus Vance',
    binding_type: 'HOMOMORPHIC_WATERMARK',
    measurement: 0.98,
    llr: 6.84,
    reliability: 0.95,
    status: 'VERIFIED',
    timestamp: '2026-09-27T11:42:01Z',
    document_id: 'doc_sec_shield_99',
    release_id: 'rel_20260926_001',
    raw_proof: 'DSSS spatial carrier matched orthogonal pseudo-random sequence seed_bob_02 (BER: 0.00%, Peak Corr: 0.98, ArUco skew corrected 2.4 deg).'
  },
  {
    evidence_id: 'ev_tar_9012',
    source_channel: 'TARDOS_MATRIX',
    channel_name: 'Tardos Traitor Tracing Matrix (m=128, c<=5)',
    suspected_candidate_id: 'bob',
    suspected_candidate_name: 'Marcus Vance',
    binding_type: 'CODEBOOK_CORRELATION',
    measurement: 16.42,
    llr: 6.44,
    reliability: 0.90,
    status: 'VERIFIED',
    timestamp: '2026-09-27T11:42:02Z',
    document_id: 'doc_sec_shield_99',
    release_id: 'rel_20260926_001',
    raw_proof: 'Score U_j = 16.42 exceeds cutoff Z = 11.40. Chebyshev false alarm probability eps <= 10^-5 under c-collusion.'
  },
  {
    evidence_id: 'ev_pqc_9013',
    source_channel: 'ML_DSA_SIGNATURE',
    channel_name: 'Decryption Event Provenance Signature (ML-DSA-65)',
    suspected_candidate_id: 'bob',
    suspected_candidate_name: 'Marcus Vance',
    binding_type: 'CRYPTOGRAPHIC_SIGNATURE',
    measurement: 1.0,
    llr: 4.80,
    reliability: 1.0,
    status: 'VERIFIED',
    timestamp: '2026-09-27T11:42:03Z',
    document_id: 'doc_sec_shield_99',
    release_id: 'rel_20260926_001',
    raw_proof: 'NIST FIPS 204 ML-DSA-65 digital signature verified against public key dSA65_pub_9a871234... on ledger event evt_dec_bob_002.'
  },
  {
    evidence_id: 'ev_led_9014',
    source_channel: 'AUDIT_LEDGER',
    channel_name: 'Cryptographic Ledger Block Linkage (SHA-256)',
    suspected_candidate_id: 'bob',
    suspected_candidate_name: 'Marcus Vance',
    binding_type: 'HASH_CHAIN',
    measurement: 1.0,
    llr: 0.0,
    reliability: 1.0,
    status: 'VERIFIED',
    timestamp: '2026-09-27T11:42:04Z',
    document_id: 'doc_sec_shield_99',
    release_id: 'rel_20260926_001',
    raw_proof: 'Block #2 verified: Parent Hash == Block #1 Tip (03a58e65...), Event Hash verified (e3b0c442...). Chain unbroken.'
  }
];

export const INTEGRATION_PROVIDERS: IntegrationProviderStatus[] = [
  {
    id: 'int_entra_id',
    name: 'Microsoft Entra ID (Azure AD)',
    type: 'IDENTITY_DIRECTORY',
    provider: 'entra_id_oauth2_scim',
    status: 'CONNECTED',
    last_sync: '2026-09-27T14:00:00Z',
    details: 'Tenant ID: 8f9b2c3d-org-gov. SCIM v2.0 bidirectional directory sync active. 6 user objects, 4 group objects synced.',
    synced_entities_count: 10
  },
  {
    id: 'int_okta',
    name: 'Okta Identity Cloud',
    type: 'IDENTITY_DIRECTORY',
    provider: 'okta_rest_api_v1',
    status: 'CONNECTED',
    last_sync: '2026-09-27T13:45:00Z',
    details: 'Okta Domain: defense-gov.okta.com. SAML 2.0 / OIDC Post-Quantum Authentication Broker connected.',
    synced_entities_count: 6
  },
  {
    id: 'int_ldap_local',
    name: 'Enterprise Active Directory / LDAP',
    type: 'IDENTITY_DIRECTORY',
    provider: 'ldaps_kerberos',
    status: 'CONNECTED',
    last_sync: '2026-09-27T14:10:00Z',
    details: 'LDAPS :636 secured with TLS 1.3. Local high-availability directory failover active with cached TTL.',
    synced_entities_count: 12
  },
  {
    id: 'int_vault_kms',
    name: 'HashiCorp Vault Transit Engine',
    type: 'KMS',
    provider: 'vault_transit_pqc',
    status: 'CONNECTED',
    last_sync: '2026-09-27T14:15:00Z',
    details: 'Vault Cluster: vault.internal.defense.gov:8200. Transit engine handles master wrapping keys & PQC root certificates.',
    synced_entities_count: 4
  },
  {
    id: 'int_siem_sentinel',
    name: 'Microsoft Sentinel / Splunk HEC',
    type: 'SIEM_AUDIT',
    provider: 'webhook_syslog_tls',
    status: 'CONNECTED',
    last_sync: '2026-09-27T14:14:00Z',
    details: 'Continuous immutable audit ledger streaming active. SHA-256 block receipts forward every 500ms.',
    synced_entities_count: 48
  }
];


export const INITIAL_RECIPIENTS: PublicRecipient[] = [
  {
    recipient_id: 'alice',
    name: 'Sarah Jenkins',
    identity_id: 'usr_8f7a9c2b01',
    identity_status: 'ACTIVE',
    role: 'Cyber Defense Operations Lead',
    kem_public_key_b64: 'kEM768_pub_8f29e01a89c43b879a92fbc7891234ea567890bcde1234567890abcdef123456',
    dsa_public_key_b64: 'dSA65_pub_4179bc892a0e41235678bcda09871234eefa1234567890abcdef1234567890ab',
    algorithm_kem: 'ML-KEM-768 (Kyber-768 standard)',
    algorithm_dsa: 'ML-DSA-65 (Dilithium3 standard)',
    created_at: '2026-09-26T10:00:00Z',
    status: 'ACTIVE',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    recipient_id: 'bob',
    name: 'Marcus Vance',
    identity_id: 'usr_3d4e5f6a02',
    identity_status: 'ACTIVE',
    role: 'Principal Cryptanalyst',
    kem_public_key_b64: 'kEM768_pub_3b7890acdef1234567890abcdef1234567890abcdef1234567890abcdef123456',
    dsa_public_key_b64: 'dSA65_pub_9a871234bcda09871234eefa1234567890abcdef1234567890abcdef12345678',
    algorithm_kem: 'ML-KEM-768 (Kyber-768 standard)',
    algorithm_dsa: 'ML-DSA-65 (Dilithium3 standard)',
    created_at: '2026-09-26T10:05:00Z',
    status: 'ACTIVE',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    recipient_id: 'charlie',
    name: 'Dr. Aris Thorne',
    identity_id: 'usr_1a2b3c4d03',
    identity_status: 'ACTIVE',
    role: 'Visiting PQC Scientist',
    kem_public_key_b64: 'kEM768_pub_cda09871234eefa1234567890abcdef1234567890abcdef1234567890abcdef12',
    dsa_public_key_b64: 'dSA65_pub_ef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    algorithm_kem: 'ML-KEM-768 (Kyber-768 standard)',
    algorithm_dsa: 'ML-DSA-65 (Dilithium3 standard)',
    created_at: '2026-09-26T10:10:00Z',
    status: 'ACTIVE',
    origin: 'SIMULATED_DEMO_SCENARIO'
  }
];

export const INITIAL_RELEASES: DocumentRelease[] = [
  {
    release_id: 'rel_20260926_001',
    document_id: 'doc_sec_shield_99',
    document_name: 'National_Defense_Protocol_2026.pdf',
    original_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    original_document_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    issuer_id: 'HQ_DISTRIBUTION_AUTHORITY',
    recipient_ids: ['alice', 'bob', 'charlie'],
    created_at: '2026-09-26T11:00:00Z',
    origin: 'SIMULATED_DEMO_SCENARIO',
    packages: {
      alice: {
        release_id: 'rel_20260926_001',
        document_id: 'doc_sec_shield_99',
        recipient_id: 'alice',
        kem_ciphertext_b64: 'kEM_CAPSULE_ALICE_398a87b6c5d4e3f210...',
        wrapped_doc_key_b64: 'WRAPPED_KEY_ALICE_88f9a2b1...',
        encrypted_doc_nonce_b64: 'NONCE_96BIT_a1b2c3d4e5f6',
        encrypted_doc_tag_b64: 'TAG_128BIT_f1e2d3c4b5a6',
        encrypted_doc_ciphertext_b64: 'AES_GCM_CIPHERTEXT_BASE64_98a76d54c3b2...',
        algorithm_kem: 'ML-KEM-768',
        algorithm_sym: 'AES-256-GCM',
        document_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        timestamp: '2026-09-26T11:00:00Z'
      },
      bob: {
        release_id: 'rel_20260926_001',
        document_id: 'doc_sec_shield_99',
        recipient_id: 'bob',
        kem_ciphertext_b64: 'kEM_CAPSULE_BOB_712a3b4c5d6e7f809a...',
        wrapped_doc_key_b64: 'WRAPPED_KEY_BOB_55a4e3f2...',
        encrypted_doc_nonce_b64: 'NONCE_96BIT_b2c3d4e5f6a1',
        encrypted_doc_tag_b64: 'TAG_128BIT_e2d3c4b5a6f1',
        encrypted_doc_ciphertext_b64: 'AES_GCM_CIPHERTEXT_BASE64_98a76d54c3b2...',
        algorithm_kem: 'ML-KEM-768',
        algorithm_sym: 'AES-256-GCM',
        document_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        timestamp: '2026-09-26T11:00:00Z'
      },
      charlie: {
        release_id: 'rel_20260926_001',
        document_id: 'doc_sec_shield_99',
        recipient_id: 'charlie',
        kem_ciphertext_b64: 'kEM_CAPSULE_CHARLIE_55e4d3c2b1a0987f...',
        wrapped_doc_key_b64: 'WRAPPED_KEY_CHARLIE_11b2c3d4...',
        encrypted_doc_nonce_b64: 'NONCE_96BIT_c3d4e5f6a1b2',
        encrypted_doc_tag_b64: 'TAG_128BIT_d3c4b5a6f1e2',
        encrypted_doc_ciphertext_b64: 'AES_GCM_CIPHERTEXT_BASE64_98a76d54c3b2...',
        algorithm_kem: 'ML-KEM-768',
        algorithm_sym: 'AES-256-GCM',
        document_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        timestamp: '2026-09-26T11:00:00Z'
      }
    }
  }
];

export const INITIAL_LEDGER_EVENTS: EvidenceEvent[] = [
  {
    event_id: 'evt_genesis_000',
    event_type: 'SYSTEM_INITIALIZATION',
    timestamp: '2026-09-26T10:00:00Z',
    document_id: 'system_root',
    release_id: 'system_root',
    recipient_id: 'HQ_AUTHORITY',
    algorithm: 'ML-DSA-65',
    artifact_hash: '0000000000000000000000000000000000000000000000000000000000000000',
    evidence_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    previous_event_hash: '0000000000000000000000000000000000000000000000000000000000000000',
    signature: 'GENESIS_SIGNATURE_PQC_ML_DSA_65_INIT_ROOT_000',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    event_id: 'evt_rel_001',
    event_type: 'DOCUMENT_RELEASE',
    timestamp: '2026-09-26T11:00:00Z',
    document_id: 'doc_sec_shield_99',
    release_id: 'rel_20260926_001',
    recipient_id: 'HQ_AUTHORITY',
    algorithm: 'ML-DSA-65',
    artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    evidence_hash: '5a41b5a289b4f4c2810c9e0129a0bcde1234567890abcdef1234567890abcdef',
    previous_event_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    signature: 'HQ_AUTH_SIG_ML_DSA_65_RELEASE_001_KEY_VALIDATED',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    event_id: 'evt_dec_bob_002',
    event_type: 'DECRYPTION_EVENT',
    timestamp: '2026-09-26T11:15:30Z',
    document_id: 'doc_sec_shield_99',
    release_id: 'rel_20260926_001',
    recipient_id: 'bob',
    algorithm: 'ML-DSA-65',
    artifact_hash: '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
    evidence_hash: '3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d',
    previous_event_hash: '5a41b5a289b4f4c2810c9e0129a0bcde1234567890abcdef1234567890abcdef',
    signature: 'BOB_SIG_ML_DSA_65_NON_REPUDIATION_PROVENANCE_LOGGED',
    origin: 'SIMULATED_DEMO_SCENARIO'
  }
];

export const ATTACK_SCENARIOS: AttackTestScenario[] = [
  {
    id: 'clean_bob',
    name: 'Clean Digital Leak (Bob Martinez)',
    category: 'CLEAN',
    description: "Pristine recipient copy from Bob's decrypted PDF session. Contains verified spatial marker and signed ML-DSA-65 provenance event.",
    expected_state: 'ATTRIBUTED',
    expected_candidate_name: 'Bob Martinez',
    attack_params: { distortion_type: 'None (Digital Original)', intensity: '0%', psnr: 99.9, ssim: 1.0, ber: 0.0, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
    simulated_payload_b64: 'CLEAN_LEAK_BOB_AUTHENTIC_MARKER',
    watermark_status: 'RECOVERED',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'clean_alice',
    name: 'Clean Digital Leak (Alice Vance)',
    category: 'CLEAN',
    description: "Pristine recipient copy extracted from Alice's decrypted package.",
    expected_state: 'ATTRIBUTED',
    expected_candidate_name: 'Alice Vance',
    attack_params: { distortion_type: 'None (Digital Original)', intensity: '0%', psnr: 99.9, ssim: 1.0, ber: 0.0, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
    simulated_payload_b64: 'CLEAN_LEAK_ALICE_AUTHENTIC_MARKER',
    watermark_status: 'RECOVERED',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'clean_charlie',
    name: 'Clean Digital Leak (Charlie Zhang)',
    category: 'CLEAN',
    description: "Pristine recipient copy extracted from Charlie's decrypted package.",
    expected_state: 'ATTRIBUTED',
    expected_candidate_name: 'Charlie Zhang',
    attack_params: { distortion_type: 'None (Digital Original)', intensity: '0%', psnr: 99.9, ssim: 1.0, ber: 0.0, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: '3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d',
    simulated_payload_b64: 'CLEAN_LEAK_CHARLIE_AUTHENTIC_MARKER',
    watermark_status: 'RECOVERED',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'print_scan_camera',
    name: 'Physical Print-Camera Smartphone Photograph (Bob)',
    category: 'PRINT_SCAN',
    description: 'Document printed to paper and captured via smartphone camera at 25-degree perspective skew. OpenCV homography synchronizes Barker-13 fiducials.',
    expected_state: 'ATTRIBUTED',
    expected_candidate_name: 'Bob Martinez',
    attack_params: { distortion_type: 'Perspective Skew + Defocus Blur', intensity: 'Moderate', psnr: 24.6, ssim: 0.74, ber: 0.08, execution_mode: 'PHYSICAL' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: 'photo_leak_hash_778899aabbccddeeff00112233445566778899aabbccddeeff',
    simulated_payload_b64: 'PRINT_SCAN_CAMERA_BOB_WARPED_ARTIFACT',
    watermark_status: 'RECOVERED',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'raw_unwatermarked',
    name: 'Unwatermarked Pre-Release Master Document',
    category: 'FORGERY',
    description: 'Pre-release original master PDF before distribution. Zero attribution markers or provenance signatures exist. Engine strictly returns NO_SIGNAL and ABSTAINS.',
    expected_state: 'NO_SIGNAL',
    expected_candidate_name: 'ABSTAIN',
    attack_params: { distortion_type: 'Pre-Release Master (No Marker)', intensity: '100%', psnr: 99.9, ssim: 1.0, ber: 1.0, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    simulated_payload_b64: 'RAW_UNWATERMARKED_ORIGINAL_DOCUMENT',
    watermark_status: 'NO_SIGNAL',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'forged_hmac',
    name: 'Counterfeit Marker / Forged Token Injection',
    category: 'FORGERY',
    description: 'Adversary injects a fake marker syntax into an arbitrary PDF with a fabricated signature token. Cryptographic token verification fails -> ABSTAIN.',
    expected_state: 'INSUFFICIENT_EVIDENCE',
    expected_candidate_name: 'ABSTAIN',
    attack_params: { distortion_type: 'Fabricated Signature Token', intensity: 'Adversarial', psnr: 45.2, ssim: 0.92, ber: 0.85, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: 'forged_token_hash_deadbeef00112233445566778899aabbccddeeff001122',
    simulated_payload_b64: 'FORGED_HMAC_FAKE_SIGNATURE_PAYLOAD',
    watermark_status: 'INVALID',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'framed_identity',
    name: 'Tampered Recipient Frame (Framing Alice)',
    category: 'FORGERY',
    description: "Attacker takes Bob's legitimate marker and manually alters recipient_id to 'alice'. Cryptographic signature fails verification -> ABSTAIN.",
    expected_state: 'INSUFFICIENT_EVIDENCE',
    expected_candidate_name: 'ABSTAIN',
    attack_params: { distortion_type: 'Identity Injection Framing', intensity: 'Targeted', psnr: 44.8, ssim: 0.91, ber: 0.72, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: 'framed_alice_payload_hash_112233445566778899aabbccddeeff00112233',
    simulated_payload_b64: 'TAMPERED_RECIPIENT_FRAME_ALICE_PAYLOAD',
    watermark_status: 'INVALID',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'heavy_jpeg',
    name: 'Severe JPEG Re-Compression (Quality Q=10)',
    category: 'DIGITAL_COMPRESSION',
    description: 'Document subjected to aggressive 8x8 DCT quantization. High bit error rate causes watermark degradation below detection threshold -> ABSTAIN.',
    expected_state: 'INSUFFICIENT_EVIDENCE',
    expected_candidate_name: 'ABSTAIN',
    attack_params: { distortion_type: 'JPEG Quantization Q=10', intensity: 'Severe', psnr: 19.4, ssim: 0.58, ber: 0.38, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: 'jpeg_q10_artifact_hash_aabbccddeeff00112233445566778899aabbccdd',
    simulated_payload_b64: 'HEAVY_JPEG_COMPRESSED_PAYLOAD_Q10',
    watermark_status: 'PARTIAL',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'cross_doc_scope',
    name: 'Cross-Document Marker Scope Mismatch',
    category: 'COLLUSION',
    description: 'Marker transplanted from an external release into this document. Document-release digest mismatch triggers CONFLICT -> ABSTAIN.',
    expected_state: 'CONFLICT',
    expected_candidate_name: 'ABSTAIN',
    attack_params: { distortion_type: 'Release Scope Digest Mismatch', intensity: 'Severe', psnr: 38.0, ssim: 0.89, ber: 0.50, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: 'scope_mismatch_hash_eeff00112233445566778899aabbccddeeff001122',
    simulated_payload_b64: 'CROSS_DOCUMENT_SCOPE_MISMATCH_PAYLOAD',
    watermark_status: 'UNAVAILABLE',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'evidence_conflict_bob_charlie',
    name: 'Multi-Channel Contradiction (Tardos: Bob, Watermark: Charlie)',
    category: 'COLLUSION',
    description: 'Tardos codebook and ledger provenance indicate Bob, but spatial watermark payload decodes to Charlie. Engine flags CONFLICT and strictly ABSTAINS.',
    expected_state: 'CONFLICT',
    expected_candidate_name: 'ABSTAIN',
    attack_params: { distortion_type: 'Multi-Party Contradictory Ingestion', intensity: 'Adversarial Splicing', psnr: 32.5, ssim: 0.82, ber: 0.22, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: 'conflict_bob_charlie_hash_445566778899aabbccddeeff0011223344556677',
    simulated_payload_b64: 'EVIDENCE_CONFLICT_BOB_CHARLIE_PAYLOAD',
    watermark_status: 'RECOVERED',
    origin: 'SIMULATED_DEMO_SCENARIO'
  },
  {
    id: 'review_required_anomaly',
    name: 'Marginal Separation Anomaly (Delta < 3.0)',
    category: 'DIGITAL_COMPRESSION',
    description: 'Multiple candidates exhibit overlapping correlation scores with separation margin Delta = 1.45 < 3.0 threshold. Engine flags REVIEW_REQUIRED.',
    expected_state: 'REVIEW_REQUIRED',
    expected_candidate_name: 'ABSTAIN',
    attack_params: { distortion_type: 'High Ambiguity Noise', intensity: 'Moderate', psnr: 22.1, ssim: 0.65, ber: 0.28, execution_mode: 'SIMULATED' },
    input_artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    output_artifact_hash: 'review_req_hash_11223344556677889900aabbccddeeff00112233',
    simulated_payload_b64: 'REVIEW_REQUIRED_ANOMALY_PAYLOAD',
    watermark_status: 'PARTIAL',
    origin: 'SIMULATED_DEMO_SCENARIO'
  }
];

export function computeMockAttribution(scenarioIdOrPayload: string): AttributionResult {
  const scenario = ATTACK_SCENARIOS.find(s => s.id === scenarioIdOrPayload || s.simulated_payload_b64 === scenarioIdOrPayload);
  
  if (!scenario || scenario.id === 'clean_bob') {
    return {
      state: 'ATTRIBUTED',
      candidate: {
        recipient_id: 'bob',
        name: 'Marcus Vance',
        confidence: 0.985,
        verified_events: ['evt_dec_bob_002', 'evt_rel_001'],
        identity_id: 'usr_3d4e5f6a02',
        resolution_status: 'RESOLVED',
        identity_status: 'ACTIVE',
        identity_summary: {
          identity_id: 'usr_3d4e5f6a02',
          display_name: 'Marcus Vance',
          email: 'marcus.vance@defense.enterprise.org',
          organization_id: 'org_defense_gov',
          provider: 'local_enterprise_directory',
          status: 'ACTIVE',
          department: 'Strategic Intelligence Division',
          title: 'Principal Cryptanalyst',
          source: 'DIRECTORY'
        }
      },
      confidence: 0.985,
      confidence_level: 'HIGH',
      watermark_status: 'RECOVERED',
      summary: "Attribution verified for recipient 'Marcus Vance' (bob) with HIGH confidence (Fused LLR: 18.08 >= threshold 8.0, separation margin Delta: 18.08 >= threshold 3.0).",
      should_abstain: false,
      fused_score: 18.08,
      margin: 18.08,
      metrics: { psnr: 99.9, ssim: 1.0, ber: 0.0, crop_ratio: 0.0, perspective_skew: 0.0, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark (DSSS/Barker-13)', raw_measurement: 0.99, llr: 6.20, reliability: 1.0, effective_llr: 6.20, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'tardos_fp', channel_name: 'Tardos Traitor Tracing (m=128 codebook)', raw_measurement: 8.42, llr: 5.48, reliability: 1.0, effective_llr: 5.48, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'pqc_sig', channel_name: 'ML-DSA-65 Provenance Signature', raw_measurement: 1.0, llr: 4.80, reliability: 1.0, effective_llr: 4.80, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'ledger_chain', channel_name: 'Tamper-Evident Ledger Hash Chain', raw_measurement: 1.0, llr: 1.60, reliability: 1.0, effective_llr: 1.60, status: 'VALID', type: 'DERIVED' }
      ],
      explanation: [
        'Valid recipient cryptographic marker extracted from carrier artifact',
        'ML-DSA-65 provenance signature verified against Marcus Vance public key',
        'Decryption provenance event evt_dec_bob_002 confirmed in audit ledger hash chain',
        'Document-release binding digest matches release context rel_20260926_001',
        'Bayesian fused score 18.08 exceeds threshold 8.0 with separation margin 18.08'
      ],
      assumptions: {
        tardos_coalition_max: 3,
        false_accusation_bound: '1e-4 (Blayer-Tassa Bound)',
        fusion_model: 'Bayesian Log-Likelihood Ratio with Anti-Double-Counting'
      },
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'clean_alice') {
    return {
      state: 'ATTRIBUTED',
      candidate: {
        recipient_id: 'alice',
        name: 'Sarah Jenkins',
        confidence: 0.982,
        verified_events: ['evt_dec_alice_003', 'evt_rel_001'],
        identity_id: 'usr_8f7a9c2b01',
        resolution_status: 'RESOLVED',
        identity_status: 'ACTIVE',
        identity_summary: {
          identity_id: 'usr_8f7a9c2b01',
          display_name: 'Sarah Jenkins',
          email: 'sarah.jenkins@defense.enterprise.org',
          organization_id: 'org_defense_gov',
          provider: 'local_enterprise_directory',
          status: 'ACTIVE',
          department: 'Cyber Defense Operations',
          title: 'Security Operations Lead',
          source: 'DIRECTORY'
        }
      },
      confidence: 0.982,
      confidence_level: 'HIGH',
      watermark_status: 'RECOVERED',
      summary: "Attribution verified for recipient 'Sarah Jenkins' (alice) with HIGH confidence (Fused LLR: 17.92).",
      should_abstain: false,
      fused_score: 17.92,
      margin: 17.92,
      metrics: { psnr: 99.9, ssim: 1.0, ber: 0.0, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark', raw_measurement: 0.98, llr: 6.10, reliability: 1.0, effective_llr: 6.10, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'tardos_fp', channel_name: 'Tardos Traitor Tracing', raw_measurement: 8.35, llr: 5.42, reliability: 1.0, effective_llr: 5.42, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'pqc_sig', channel_name: 'ML-DSA-65 Provenance Signature', raw_measurement: 1.0, llr: 4.80, reliability: 1.0, effective_llr: 4.80, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'ledger_chain', channel_name: 'Tamper-Evident Ledger', raw_measurement: 1.0, llr: 1.60, reliability: 1.0, effective_llr: 1.60, status: 'VALID', type: 'DERIVED' }
      ],
      explanation: ['All cryptographic, watermark, and ledger channels corroborate Sarah Jenkins.'],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'clean_charlie') {
    return {
      state: 'ATTRIBUTED',
      candidate: {
        recipient_id: 'charlie',
        name: 'Dr. Aris Thorne',
        confidence: 0.988,
        verified_events: ['evt_dec_charlie_004', 'evt_rel_001'],
        identity_id: 'usr_1a2b3c4d03',
        resolution_status: 'RESOLVED',
        identity_status: 'ACTIVE',
        identity_summary: {
          identity_id: 'usr_1a2b3c4d03',
          display_name: 'Dr. Aris Thorne',
          email: 'aris.thorne@partner.defense.org',
          organization_id: 'org_defense_gov',
          provider: 'local_enterprise_directory',
          status: 'ACTIVE',
          department: 'Advanced Research Projects (External Partner)',
          title: 'Visiting PQC Scientist',
          source: 'DIRECTORY'
        }
      },
      confidence: 0.988,
      confidence_level: 'HIGH',
      watermark_status: 'RECOVERED',
      summary: "Attribution verified for recipient 'Dr. Aris Thorne' (charlie) with HIGH confidence (Fused LLR: 18.15).",
      should_abstain: false,
      fused_score: 18.15,
      margin: 18.15,
      metrics: { psnr: 99.9, ssim: 1.0, ber: 0.0, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark', raw_measurement: 0.99, llr: 6.25, reliability: 1.0, effective_llr: 6.25, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'tardos_fp', channel_name: 'Tardos Traitor Tracing', raw_measurement: 8.50, llr: 5.50, reliability: 1.0, effective_llr: 5.50, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'pqc_sig', channel_name: 'ML-DSA-65 Provenance Signature', raw_measurement: 1.0, llr: 4.80, reliability: 1.0, effective_llr: 4.80, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'ledger_chain', channel_name: 'Tamper-Evident Ledger', raw_measurement: 1.0, llr: 1.60, reliability: 1.0, effective_llr: 1.60, status: 'VALID', type: 'DERIVED' }
      ],
      explanation: ['All cryptographic, watermark, and ledger channels corroborate Dr. Aris Thorne.'],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'print_scan_camera') {
    return {
      state: 'ATTRIBUTED',
      candidate: {
        recipient_id: 'bob',
        name: 'Marcus Vance',
        confidence: 0.92,
        verified_events: ['evt_dec_bob_002'],
        identity_id: 'usr_3d4e5f6a02',
        resolution_status: 'RESOLVED',
        identity_status: 'ACTIVE',
        identity_summary: {
          identity_id: 'usr_3d4e5f6a02',
          display_name: 'Marcus Vance',
          email: 'marcus.vance@defense.enterprise.org',
          organization_id: 'org_defense_gov',
          provider: 'local_enterprise_directory',
          status: 'ACTIVE',
          department: 'Strategic Intelligence Division',
          title: 'Principal Cryptanalyst',
          source: 'DIRECTORY'
        }
      },
      confidence: 0.92,
      confidence_level: 'HIGH',
      watermark_status: 'RECOVERED',
      summary: 'Attribution verified for Marcus Vance despite 3D camera warp. OpenCV projective homography rectified Barker-13 fiducials with RS(42,26) error correction.',
      should_abstain: false,
      fused_score: 14.30,
      margin: 14.30,
      metrics: { psnr: 24.6, ssim: 0.74, ber: 0.08, perspective_skew: 25.0, execution_mode: 'PHYSICAL' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark (Homography Rectified)', raw_measurement: 0.84, llr: 4.70, reliability: 0.85, effective_llr: 4.00, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'tardos_fp', channel_name: 'Tardos Traitor Tracing', raw_measurement: 6.80, llr: 4.30, reliability: 0.90, effective_llr: 3.90, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'pqc_sig', channel_name: 'ML-DSA-65 Provenance Signature', raw_measurement: 1.0, llr: 4.80, reliability: 1.0, effective_llr: 4.80, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'ledger_chain', channel_name: 'Tamper-Evident Ledger', raw_measurement: 1.0, llr: 1.60, reliability: 1.0, effective_llr: 1.60, status: 'VALID', type: 'DERIVED' }
      ],
      explanation: [
        'Homography matrix calculated from 4 fiducial corners',
        'Reed-Solomon RS(42,26) corrected 3 burst symbol errors',
        'PQC provenance event corroborated in hash-chained audit log'
      ],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'raw_unwatermarked') {
    return {
      state: 'NO_SIGNAL',
      candidate: null,
      confidence: 0.0,
      confidence_level: 'NONE',
      watermark_status: 'NO_SIGNAL',
      summary: 'Abstain: No extractable forensic watermark, cryptographic marker, or provenance signature found in carrier artifact. Fail-closed policy abstains from accusation.',
      should_abstain: true,
      fused_score: 0.0,
      margin: 0.0,
      metrics: { psnr: 99.9, ssim: 1.0, ber: 1.0, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark', raw_measurement: 0.0, llr: 0.0, reliability: 0.0, effective_llr: 0.0, status: 'NO_SIGNAL', type: 'INDEPENDENT' },
        { channel_id: 'tardos_fp', channel_name: 'Tardos Traitor Tracing', raw_measurement: 0.0, llr: 0.0, reliability: 0.0, effective_llr: 0.0, status: 'NO_SIGNAL', type: 'INDEPENDENT' },
        { channel_id: 'pqc_sig', channel_name: 'ML-DSA-65 Provenance Signature', raw_measurement: 0.0, llr: 0.0, reliability: 0.0, effective_llr: 0.0, status: 'NO_SIGNAL', type: 'INDEPENDENT' }
      ],
      explanation: [
        'Zero fiducial anchors detected in document canvas',
        'No cryptographic marker envelope present in trailer/metadata',
        'Fail-closed decision: ABSTAIN (NO_SIGNAL)'
      ],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'forged_hmac') {
    return {
      state: 'INSUFFICIENT_EVIDENCE',
      candidate: null,
      confidence: 0.08,
      confidence_level: 'LOW',
      watermark_status: 'INVALID',
      summary: 'Abstain: Adversarial marker structure detected but signature token validation failed. Engine flags counterfeit forgery and strictly ABSTAINS.',
      should_abstain: true,
      fused_score: 0.42,
      margin: 0.42,
      metrics: { psnr: 45.2, ssim: 0.92, ber: 0.85, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark', raw_measurement: 0.1, llr: 0.42, reliability: 0.1, effective_llr: 0.04, status: 'FORGED', type: 'INDEPENDENT' },
        { channel_id: 'pqc_sig', channel_name: 'Cryptographic Signature', raw_measurement: 0.0, llr: -5.0, reliability: 1.0, effective_llr: -5.0, status: 'FORGED', type: 'INDEPENDENT' }
      ],
      explanation: [
        'Marker syntax was manually fabricated by an adversary',
        'Cryptographic HMAC signature token fails verification with system master key',
        'Fail-closed decision: ABSTAIN (INSUFFICIENT_EVIDENCE)'
      ],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'framed_identity') {
    return {
      state: 'INSUFFICIENT_EVIDENCE',
      candidate: null,
      confidence: 0.12,
      confidence_level: 'LOW',
      watermark_status: 'INVALID',
      summary: "Abstain: Adversary modified recipient payload field to frame Alice using Bob's signature token. Cryptographic recipient binding verification failed -> ABSTAIN.",
      should_abstain: true,
      fused_score: 0.85,
      margin: 0.85,
      metrics: { psnr: 44.8, ssim: 0.91, ber: 0.72, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark', raw_measurement: 0.2, llr: 0.85, reliability: 0.1, effective_llr: 0.09, status: 'FORGED', type: 'INDEPENDENT' },
        { channel_id: 'pqc_sig', channel_name: 'ML-DSA-65 Signature Check', raw_measurement: 0.0, llr: -8.0, reliability: 1.0, effective_llr: -8.0, status: 'FORGED', type: 'INDEPENDENT' }
      ],
      explanation: [
        'Recipient ID declared as "alice" does not match signature token generated for "bob"',
        'Cryptographic non-repudiation binding protects Alice from being framed',
        'Fail-closed decision: ABSTAIN (INSUFFICIENT_EVIDENCE)'
      ],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'heavy_jpeg') {
    return {
      state: 'INSUFFICIENT_EVIDENCE',
      candidate: null,
      confidence: 0.35,
      confidence_level: 'LOW',
      watermark_status: 'PARTIAL',
      summary: 'Abstain: Severe DCT quantization noise (JPEG Q=10, BER 38%) corrupted Reed-Solomon parity bytes beyond error correction limit t=8. Engine safely ABSTAINS.',
      should_abstain: true,
      fused_score: 1.82,
      margin: 0.90,
      metrics: { psnr: 19.4, ssim: 0.58, ber: 0.38, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark', raw_measurement: 0.35, llr: 1.82, reliability: 0.24, effective_llr: 0.44, status: 'DEGRADED', type: 'INDEPENDENT' }
      ],
      explanation: [
        'High bit error rate (38%) exceeded Reed-Solomon correction capacity',
        'Channel reliability discount factor rho = 0.24 reduces effective score below threshold tau_attr 8.0',
        'Fail-closed decision: ABSTAIN (INSUFFICIENT_EVIDENCE)'
      ],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'cross_doc_scope') {
    return {
      state: 'CONFLICT',
      candidate: null,
      confidence: 0.0,
      confidence_level: 'NONE',
      watermark_status: 'UNAVAILABLE',
      summary: 'Abstain: Document-release binding digest (32-bit DocRel ID) does not match the active release context rel_20260926_001. Cross-document contamination detected -> ABSTAIN.',
      should_abstain: true,
      fused_score: 0.0,
      margin: 0.0,
      metrics: { psnr: 38.0, ssim: 0.89, ber: 0.50, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'doc_rel_binding', channel_name: 'Document-Release Scope Binding', raw_measurement: 0.0, llr: -10.0, reliability: 1.0, effective_llr: -10.0, status: 'FORGED', type: 'INDEPENDENT' }
      ],
      explanation: [
        'Marker was transplanted from an external document into this target document',
        'DocRel digest mismatch proves cross-document contamination',
        'Fail-closed decision: ABSTAIN (CONFLICT)'
      ],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'evidence_conflict_bob_charlie') {
    return {
      state: 'CONFLICT',
      candidate: null,
      confidence: 0.0,
      confidence_level: 'NONE',
      watermark_status: 'RECOVERED',
      summary: 'Abstain: Cross-channel evidence contradiction. Tardos score (Z=14.82) and decryption ledger indicate Bob, but spatial watermark payload decodes to Charlie. Under the Fail-Closed Axiom, the engine ABSTAINS rather than selecting the highest numeric score.',
      should_abstain: true,
      fused_score: 0.0,
      margin: 0.0,
      metrics: { psnr: 32.5, ssim: 0.82, ber: 0.22, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'tardos_fp', channel_name: 'Tardos Traitor Tracing (Candidate: Bob)', raw_measurement: 14.82, llr: 6.50, reliability: 0.85, effective_llr: 5.52, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark (Candidate: Charlie)', raw_measurement: 0.95, llr: 5.90, reliability: 0.80, effective_llr: 4.72, status: 'VALID', type: 'INDEPENDENT' },
        { channel_id: 'pqc_sig', channel_name: 'Decryption Ledger Provenance (Signer: Bob)', raw_measurement: 1.0, llr: 4.80, reliability: 1.0, effective_llr: 4.80, status: 'VALID', type: 'INDEPENDENT' }
      ],
      explanation: [
        'Tardos correlation indicates Bob Martinez (Score: 14.82 >= tau_Z 6.50)',
        'Decryption provenance event on ledger is signed by Bob Martinez',
        'Spatial watermark carrier payload decodes to Charlie Zhang',
        'Contradictory evidence signals detected across independent channels',
        'Fail-Closed Rule: When independent channels point to conflicting candidates, system MUST return CONFLICT and ABSTAIN'
      ],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  if (scenario.id === 'review_required_anomaly') {
    return {
      state: 'REVIEW_REQUIRED',
      candidate: null,
      confidence: 0.48,
      confidence_level: 'MEDIUM',
      watermark_status: 'PARTIAL',
      summary: 'Review Required: Candidate separation margin Delta = 1.45 is below the mandatory separation threshold Delta_min = 3.0. Forensic anomaly requires human auditor review.',
      should_abstain: true,
      fused_score: 5.80,
      margin: 1.45,
      metrics: { psnr: 22.1, ssim: 0.65, ber: 0.28, execution_mode: 'SIMULATED' },
      channels: [
        { channel_id: 'wm_spatial', channel_name: 'Spatial Watermark', raw_measurement: 0.65, llr: 3.20, reliability: 0.60, effective_llr: 1.92, status: 'DEGRADED', type: 'INDEPENDENT' },
        { channel_id: 'tardos_fp', channel_name: 'Tardos Traitor Tracing', raw_measurement: 6.20, llr: 3.80, reliability: 0.70, effective_llr: 2.66, status: 'DEGRADED', type: 'INDEPENDENT' }
      ],
      explanation: [
        'Score for Top Candidate (Bob) = 5.80, Runner-up (Alice) = 4.35',
        'Separation margin Delta = 1.45 < 3.0 required threshold',
        'Ambiguity exceeds automated threshold; flagged for REVIEW_REQUIRED'
      ],
      origin: 'SIMULATED_DEMO_SCENARIO'
    };
  }

  // Default fallback
  return {
    state: 'NO_SIGNAL',
    candidate: null,
    confidence: 0.0,
    confidence_level: 'NONE',
    watermark_status: 'NO_SIGNAL',
    summary: 'Unrecognized artifact payload. Fail-closed policy abstains from accusation.',
    should_abstain: true,
    fused_score: 0.0,
    margin: 0.0,
    origin: 'SIMULATED_DEMO_SCENARIO'
  };
}

export const DEMO_FIXTURES = {
  DOCUMENTS: INITIAL_DOCUMENTS,
  RECIPIENTS: INITIAL_RECIPIENTS,
  RELEASES: INITIAL_RELEASES,
  LEDGER_EVENTS: INITIAL_LEDGER_EVENTS,
  IDENTITIES: DIRECTORY_IDENTITIES,
  GROUPS: DIRECTORY_GROUPS,
  HISTORICAL_INVESTIGATIONS: HISTORICAL_INVESTIGATIONS,
  EVIDENCE_RECORDS: EVIDENCE_RECORDS,
  INTEGRATION_PROVIDERS: INTEGRATION_PROVIDERS
};

