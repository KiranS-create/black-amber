export interface PublicRecipient {
  recipient_id: string;
  name: string;
  kem_public_key_b64: string;
  dsa_public_key_b64: string;
  algorithm_kem: string;
  algorithm_dsa: string;
  created_at: string;
  status: string;
}

export interface DocumentRelease {
  release_id: string;
  document_id: string;
  document_name: string;
  original_hash: string;
  issuer_id: string;
  recipient_ids: string[];
  created_at: string;
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
}

export interface AttributionResult {
  state: "ATTRIBUTED" | "CONFLICT" | "INSUFFICIENT_EVIDENCE" | "NO_SIGNAL";
  candidate: {
    recipient_id: string;
    name: string;
    confidence: number;
    verified_events: string[];
  } | null;
  confidence: number;
  confidence_level: string;
  summary: string;
  should_abstain: boolean;
}
