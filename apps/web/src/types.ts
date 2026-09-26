export type DataSourceOrigin = 
  | 'REAL_BACKEND_RESULT' 
  | 'REAL_LOCAL_COMPUTATION' 
  | 'SIMULATED_DEMO_SCENARIO' 
  | 'PLACEHOLDER_UNAVAILABLE';

export type AttributionStateType = 
  | 'ATTRIBUTED' 
  | 'NO_SIGNAL' 
  | 'INSUFFICIENT_EVIDENCE' 
  | 'CONFLICT' 
  | 'REVIEW_REQUIRED' 
  | 'ABSTAINED' 
  | 'FAILED';

export type EvidenceConfidenceLevelType = 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';

export type WatermarkStatusType = 
  | 'RECOVERED' 
  | 'PARTIAL' 
  | 'NO_SIGNAL' 
  | 'INVALID' 
  | 'UNAVAILABLE' 
  | 'NO_WATERMARK' 
  | 'DECODER_UNAVAILABLE' 
  | 'PHYSICAL_CAPTURE' 
  | 'SIMULATED_CAPTURE';

export type ProvenanceVerificationStatusType = 
  | 'RECIPIENT_SIGNED_VERIFIED' 
  | 'SIMULATED_RECIPIENT_ACTION' 
  | 'UNAVAILABLE';

export interface PublicRecipient {
  recipient_id: string;
  name: string;
  kem_public_key_b64: string;
  dsa_public_key_b64: string;
  algorithm_kem: string;
  algorithm_dsa: string;
  created_at: string;
  status: string;
  role?: string;
  origin?: DataSourceOrigin;
}

export interface DocumentMetadata {
  document_id: string;
  document_name: string;
  original_document_hash: string;
  size_bytes: number;
  mime_type: string;
  created_at: string;
  artifact_id: string;
  origin?: DataSourceOrigin;
}

export interface ReleaseRecipientPackage {
  release_id: string;
  document_id: string;
  recipient_id: string;
  kem_ciphertext_b64: string;
  wrapped_doc_key_b64: string;
  encrypted_doc_nonce_b64: string;
  encrypted_doc_tag_b64: string;
  encrypted_doc_ciphertext_b64: string;
  algorithm_kem: string;
  algorithm_sym: string;
  document_hash: string;
  timestamp: string;
}

export interface DocumentRelease {
  release_id: string;
  document_id: string;
  document_name: string;
  original_hash: string;
  original_document_hash?: string;
  issuer_id: string;
  recipient_ids: string[];
  created_at: string;
  packages?: Record<string, ReleaseRecipientPackage | any>;
  origin?: DataSourceOrigin;
}

export interface DecryptionResponse {
  status: string;
  release_id: string;
  document_id: string;
  recipient_id: string;
  original_document_hash: string;
  traceable_artifact_hash: string;
  event_id: string;
  event_hash: string;
  timestamp: string;
  traceable_document_base64?: string;
  artifact_download_url?: string;
  provenance_status?: ProvenanceVerificationStatusType;
  origin?: DataSourceOrigin;
}

export interface EvidenceEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  document_id: string;
  release_id: string;
  recipient_id: string;
  algorithm: string;
  artifact_hash: string;
  evidence_hash: string;
  previous_event_hash: string;
  signature: string;
  is_tampered?: boolean;
  origin?: DataSourceOrigin;
}

export interface EvidenceItem {
  source: string;
  title: string;
  is_valid: boolean;
  confidence: number;
  details: Record<string, any>;
}

export interface Candidate {
  recipient_id: string;
  name: string;
  confidence: number;
  verified_events: string[];
}

export interface ChannelFusionScore {
  channel_id: string;
  channel_name: string;
  raw_measurement: number;
  llr: number;
  reliability: number;
  effective_llr: number;
  status: 'VALID' | 'DEGRADED' | 'NO_SIGNAL' | 'FORGED' | 'UNAVAILABLE';
  type: 'INDEPENDENT' | 'PARTIAL_DEPENDENT' | 'DERIVED';
}

export interface AttributionResult {
  state: AttributionStateType;
  candidate: Candidate | null;
  confidence: number; // Raw heuristic or LLR-derived score in [0, 1]
  confidence_level: EvidenceConfidenceLevelType;
  summary: string;
  should_abstain: boolean;
  fused_score?: number; // Fused Log-Likelihood Ratio
  margin?: number;      // Candidate separation margin
  watermark_status?: WatermarkStatusType;
  evidence_items?: EvidenceItem[];
  channels?: ChannelFusionScore[];
  metrics?: {
    psnr?: number;
    ssim?: number;
    ber?: number;
    crop_ratio?: number;
    perspective_skew?: number;
    execution_mode?: 'PHYSICAL' | 'SIMULATED';
  };
  explanation?: string[];
  assumptions?: Record<string, any>;
  origin?: DataSourceOrigin;
}

export interface LeakMetadata {
  leak_id: string;
  leak_artifact_hash: string;
  size_bytes: number;
  mime_type: string;
  suspected_document_id?: string;
  suspected_release_id?: string;
  created_at: string;
  artifact_id: string;
  origin?: DataSourceOrigin;
}

export interface AttackTelemetryInput {
  attack_id?: string;
  attack_family?: string;
  attack_name?: string;
  execution_mode: 'PHYSICAL' | 'SIMULATED';
  parameters?: Record<string, any>;
  input_hash?: string;
  output_hash?: string;
  observed_effect?: string;
  traceability_result?: string;
  psnr?: number;
  ssim?: number;
  crop_ratio?: number;
  noise_level?: number;
}

export interface AttackTestScenario {
  id: string;
  name: string;
  category: 'PRINT_SCAN' | 'DIGITAL_COMPRESSION' | 'FORGERY' | 'COLLUSION' | 'CROPPING' | 'CLEAN';
  description: string;
  expected_state: AttributionStateType;
  expected_candidate_name: string;
  attack_params: {
    distortion_type: string;
    intensity: string;
    psnr: number;
    ssim: number;
    ber: number;
    execution_mode: 'PHYSICAL' | 'SIMULATED';
  };
  input_artifact_hash: string;
  output_artifact_hash: string;
  simulated_payload_b64: string;
  watermark_status?: WatermarkStatusType;
  origin: DataSourceOrigin;
}

export interface LedgerVerificationResult {
  is_valid: boolean;
  total_events: number;
  chain_tip: string;
  errors: string[];
  tampered_index?: number | null;
  origin?: DataSourceOrigin;
}

export interface CapabilitiesResponse {
  service_name: string;
  version: string;
  offline_mode: boolean;
  cryptography: Record<string, any>;
  traceability: Record<string, any>;
  evidence_fusion: Record<string, any>;
  supported_formats: string[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  ledger_events_count: number;
  registered_documents_count: number;
  enrolled_recipients_count: number;
  releases_count: number;
  active_jobs_count: number;
}
