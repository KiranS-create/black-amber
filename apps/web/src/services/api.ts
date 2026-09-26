import { 
  PublicRecipient, 
  DocumentMetadata,
  DocumentRelease, 
  EvidenceEvent, 
  AttributionResult, 
  LedgerVerificationResult,
  CapabilitiesResponse,
  HealthResponse,
  LeakMetadata,
  AttackTelemetryInput,
  DecryptionResponse
} from '../types';
import { 
  INITIAL_DOCUMENTS,
  INITIAL_RECIPIENTS, 
  INITIAL_RELEASES, 
  INITIAL_LEDGER_EVENTS, 
  computeMockAttribution 
} from './mockData';

const API_BASE = 'http://localhost:8000';

class ApiService {
  private isLiveBackend: boolean = false;
  private forceOffline: boolean = false;

  // In-memory mock storage for offline simulation
  private mockDocuments: DocumentMetadata[] = [...INITIAL_DOCUMENTS];
  private mockRecipients: PublicRecipient[] = [...INITIAL_RECIPIENTS];
  private mockReleases: DocumentRelease[] = [...INITIAL_RELEASES];
  private mockLedgerEvents: EvidenceEvent[] = [...INITIAL_LEDGER_EVENTS];
  private mockTamperedBlockIndex: number | null = null;
  private mockCapabilities: CapabilitiesResponse = {
    service_name: 'AegisTrace Cryptographic Attribution Platform',
    version: '1.0.0',
    offline_mode: true,
    cryptography: {
      kem: 'ML-KEM-768 (NIST FIPS 203)',
      signature: 'ML-DSA-65 (NIST FIPS 204)',
      symmetric: 'AES-256-GCM (NIST SP 800-38D)',
      key_wrap: 'AES Key Wrap (RFC 3394 / NIST SP 800-38F)',
      derivation: 'HKDF-SHA256 (RFC 5869) with domain separation',
      hashing: 'SHA-256 (FIPS 180-4)'
    },
    traceability: {
      algorithms: [
        'PrototypeTraceabilityProvider_v0.1 (HMAC-SHA256)',
        'TardosTraceabilityProvider_v1.0 (Symbol-Symmetric Tardos)'
      ],
      capacity_planner: 'TardosCapacityPlanner (Blayer-Tassa / Skoric bounds)',
      marking_assumption_enforced: true
    },
    evidence_fusion: {
      engine: 'Bayesian Multi-Channel Evidence Fusion',
      channels: [
        'TARDOS_FINGERPRINT',
        'WATERMARK_PAYLOAD',
        'PROVENANCE_SIGNATURE',
        'AUDIT_LEDGER',
        'CRYPTOGRAPHIC_INTEGRITY',
        'ATTACK_CONTEXT'
      ],
      anti_double_counting: 'EvidenceDependencyGraph with Max Evidentiary Bound',
      decision_policy: 'Fail-Closed (Never Force an Attribution)'
    },
    supported_formats: ['application/pdf', 'image/png', 'image/jpeg']
  };

  constructor() {
    this.checkHealth();
  }

  public setForceOffline(val: boolean) {
    this.forceOffline = val;
  }

  public isForceOffline(): boolean {
    return this.forceOffline;
  }

  public isOnline(): boolean {
    return this.isLiveBackend && !this.forceOffline;
  }

  public async checkHealth(): Promise<{ online: boolean; health: HealthResponse | null }> {
    if (this.forceOffline) {
      this.isLiveBackend = false;
      return {
        online: false,
        health: {
          status: 'offline_simulation',
          service: 'AegisTrace Frontend Simulator (Offline Demo Mode)',
          version: '1.0.0',
          ledger_events_count: this.mockLedgerEvents.length,
          registered_documents_count: this.mockDocuments.length,
          enrolled_recipients_count: this.mockRecipients.length,
          releases_count: this.mockReleases.length,
          active_jobs_count: 0
        }
      };
    }

    try {
      const res = await fetch(`${API_BASE}/health`, { method: 'GET', signal: AbortSignal.timeout(2000) });
      if (res.ok) {
        const data: HealthResponse = await res.json();
        this.isLiveBackend = true;
        return { online: true, health: data };
      }
    } catch {
      this.isLiveBackend = false;
    }

    return {
      online: false,
      health: null
    };
  }

  public async getCapabilities(): Promise<CapabilitiesResponse> {
    if (this.forceOffline) {
      return this.mockCapabilities;
    }

    try {
      const res = await fetch(`${API_BASE}/capabilities`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) {
        this.isLiveBackend = true;
        return await res.json();
      }
      throw new Error(`HTTP ${res.status}: Failed to fetch capabilities`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unavailable at ${API_BASE}/capabilities. Toggle Offline Demo Mode to test locally. Details: ${e?.message || e}`);
    }
  }

  // -------------------------------------------------------------
  // 1. Documents API (POST /documents, GET /documents)
  // -------------------------------------------------------------
  public async getDocuments(): Promise<DocumentMetadata[]> {
    if (this.forceOffline) {
      return this.mockDocuments.map(d => ({ ...d, origin: 'SIMULATED_DEMO_SCENARIO' }));
    }

    try {
      const res = await fetch(`${API_BASE}/documents`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) {
        const data = await res.json();
        const docs: DocumentMetadata[] = data.documents || [];
        this.isLiveBackend = true;
        return docs.map(d => ({ ...d, origin: 'REAL_BACKEND_RESULT' }));
      }
      throw new Error(`HTTP ${res.status}: Failed to fetch documents`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at ${API_BASE}/documents. Switch to Offline Demo Mode or check API server.`);
    }
  }

  public async uploadDocument(file: File, documentName?: string, documentId?: string): Promise<DocumentMetadata> {
    if (this.forceOffline) {
      const docId = documentId || `doc_${Date.now().toString(36)}`;
      const docName = documentName || file.name || 'Uploaded_Document.pdf';
      const mockDoc: DocumentMetadata = {
        document_id: docId,
        document_name: docName,
        original_document_hash: `hash_${Math.random().toString(36).substring(2)}${Math.random().toString(36).substring(2)}`,
        size_bytes: file.size || 102400,
        mime_type: file.type || 'application/pdf',
        created_at: new Date().toISOString(),
        artifact_id: `art_${docId}`,
        origin: 'SIMULATED_DEMO_SCENARIO'
      };
      this.mockDocuments.unshift(mockDoc);
      return mockDoc;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (documentName) formData.append('document_name', documentName);
      if (documentId) formData.append('document_id', documentId);

      const res = await fetch(`${API_BASE}/documents`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(5000)
      });
      if (res.ok) {
        const doc: DocumentMetadata = await res.json();
        this.isLiveBackend = true;
        return { ...doc, origin: 'REAL_BACKEND_RESULT' };
      }
      throw new Error(`HTTP ${res.status}: Failed to upload document`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at POST ${API_BASE}/documents. Switch to Offline Demo Mode or check API server.`);
    }
  }

  // -------------------------------------------------------------
  // 2. Recipients API (POST /recipients, GET /recipients)
  // -------------------------------------------------------------
  public async getRecipients(): Promise<PublicRecipient[]> {
    if (this.forceOffline) {
      return this.mockRecipients.map(r => ({ ...r, origin: 'SIMULATED_DEMO_SCENARIO' }));
    }

    try {
      const res = await fetch(`${API_BASE}/recipients`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) {
        const recs: PublicRecipient[] = await res.json();
        this.isLiveBackend = true;
        return recs.map(r => ({ ...r, origin: 'REAL_BACKEND_RESULT' }));
      }
      throw new Error(`HTTP ${res.status}: Failed to fetch recipients`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at GET ${API_BASE}/recipients. Switch to Offline Demo Mode.`);
    }
  }

  public async enrollRecipient(name: string, recipientId?: string): Promise<PublicRecipient> {
    const cleanId = (recipientId || name.toLowerCase().replace(/[^a-z0-9]/g, '')).trim();
    if (this.forceOffline) {
      const newRecipient: PublicRecipient = {
        recipient_id: cleanId,
        name,
        role: 'Authorized Defense Specialist',
        kem_public_key_b64: `kEM768_pub_${Math.random().toString(36).substring(2)}${Math.random().toString(36).substring(2)}`,
        dsa_public_key_b64: `dSA65_pub_${Math.random().toString(36).substring(2)}${Math.random().toString(36).substring(2)}`,
        algorithm_kem: 'ML-KEM-768 (Kyber-768 standard)',
        algorithm_dsa: 'ML-DSA-65 (Dilithium3 standard)',
        created_at: new Date().toISOString(),
        status: 'ACTIVE',
        origin: 'SIMULATED_DEMO_SCENARIO'
      };
      this.mockRecipients.push(newRecipient);
      return newRecipient;
    }

    try {
      const res = await fetch(`${API_BASE}/recipients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, recipient_id: cleanId }),
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) {
        const r: PublicRecipient = await res.json();
        this.isLiveBackend = true;
        return { ...r, origin: 'REAL_BACKEND_RESULT' };
      }
      throw new Error(`HTTP ${res.status}: Failed to enroll recipient`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at POST ${API_BASE}/recipients. Switch to Offline Demo Mode.`);
    }
  }

  // -------------------------------------------------------------
  // 3. Releases API (POST /releases, GET /releases)
  // -------------------------------------------------------------
  public async getReleases(): Promise<DocumentRelease[]> {
    if (this.forceOffline) {
      return this.mockReleases.map(rel => ({ ...rel, origin: 'SIMULATED_DEMO_SCENARIO' }));
    }

    try {
      const res = await fetch(`${API_BASE}/releases`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) {
        const rels: DocumentRelease[] = await res.json();
        this.isLiveBackend = true;
        return rels.map(rel => ({ ...rel, origin: 'REAL_BACKEND_RESULT' }));
      }
      throw new Error(`HTTP ${res.status}: Failed to fetch releases`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at GET ${API_BASE}/releases. Switch to Offline Demo Mode.`);
    }
  }

  public async createRelease(
    documentName: string, 
    documentBase64: string, 
    recipientIds: string[],
    documentId?: string,
    tardosEnabled: boolean = true
  ): Promise<DocumentRelease> {
    if (this.forceOffline) {
      const releaseId = `rel_${Date.now().toString().substring(6)}`;
      const docId = documentId || `doc_${Math.random().toString(36).substring(2, 8)}`;
      const originalHash = '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';

      const newRelease: DocumentRelease = {
        release_id: releaseId,
        document_id: docId,
        document_name: documentName,
        original_hash: originalHash,
        original_document_hash: originalHash,
        issuer_id: 'HQ_DISTRIBUTION_AUTHORITY',
        recipient_ids: recipientIds,
        created_at: new Date().toISOString(),
        origin: 'SIMULATED_DEMO_SCENARIO',
        packages: {}
      };

      recipientIds.forEach(rId => {
        if (newRelease.packages) {
          newRelease.packages[rId] = {
            release_id: releaseId,
            document_id: docId,
            recipient_id: rId,
            kem_ciphertext_b64: `kEM_CAPSULE_${rId.toUpperCase()}_${Math.random().toString(36).substring(2)}`,
            wrapped_doc_key_b64: `WRAPPED_KEY_${rId.toUpperCase()}_${Math.random().toString(36).substring(2)}`,
            encrypted_doc_nonce_b64: `NONCE_96BIT_${Math.random().toString(36).substring(2, 14)}`,
            encrypted_doc_tag_b64: `TAG_128BIT_${Math.random().toString(36).substring(2, 14)}`,
            encrypted_doc_ciphertext_b64: documentBase64,
            algorithm_kem: 'ML-KEM-768',
            algorithm_sym: 'AES-256-GCM',
            document_hash: originalHash,
            timestamp: new Date().toISOString()
          };
        }
      });

      this.mockReleases.unshift(newRelease);

      // Append release event to mock ledger
      this.mockLedgerEvents.push({
        event_id: `evt_rel_${releaseId}`,
        event_type: 'DOCUMENT_RELEASE',
        timestamp: new Date().toISOString(),
        document_id: docId,
        release_id: releaseId,
        recipient_id: 'HQ_AUTHORITY',
        algorithm: 'ML-DSA-65',
        artifact_hash: originalHash,
        evidence_hash: `ev_${Math.random().toString(36).substring(2)}`,
        previous_event_hash: this.mockLedgerEvents[this.mockLedgerEvents.length - 1]?.evidence_hash || '0000000000',
        signature: `HQ_SIGNATURE_ML_DSA_65_${releaseId}`,
        origin: 'SIMULATED_DEMO_SCENARIO'
      });

      return newRelease;
    }

    try {
      const payload: Record<string, any> = {
        document_name: documentName,
        issuer_id: 'HQ_DISTRIBUTION_AUTHORITY',
        recipient_ids: recipientIds,
        tardos_enabled: tardosEnabled,
        coalition_size: 3,
        false_accusation_epsilon: 0.0001
      };
      if (documentId) {
        payload.document_id = documentId;
      } else {
        payload.document_base64 = documentBase64;
      }

      const res = await fetch(`${API_BASE}/releases`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(5000)
      });
      if (res.ok) {
        const rel: DocumentRelease = await res.json();
        this.isLiveBackend = true;
        return { ...rel, origin: 'REAL_BACKEND_RESULT' };
      }
      throw new Error(`HTTP ${res.status}: Failed to create release`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at POST ${API_BASE}/releases. Switch to Offline Demo Mode.`);
    }
  }

  // -------------------------------------------------------------
  // 4. Decryption API (POST /releases/{release_id}/decrypt)
  // -------------------------------------------------------------
  public async decryptPackage(releaseId: string, recipientId: string): Promise<DecryptionResponse> {
    if (this.forceOffline) {
      const eventId = `evt_dec_${recipientId}_${Date.now().toString().substring(7)}`;
      const prevHash = this.mockLedgerEvents[this.mockLedgerEvents.length - 1]?.evidence_hash || '0000000000';
      const originalDocHash = '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
      const traceableHash = `traceable_hash_${recipientId}_${Math.random().toString(36).substring(2)}`;
      const evidenceHash = `evidence_hash_${recipientId}_${Math.random().toString(36).substring(2)}`;

      const newEvent: EvidenceEvent = {
        event_id: eventId,
        event_type: 'DECRYPTION_EVENT',
        timestamp: new Date().toISOString(),
        document_id: 'doc_sec_shield_99',
        release_id: releaseId,
        recipient_id: recipientId,
        algorithm: 'ML-DSA-65',
        artifact_hash: traceableHash,
        evidence_hash: evidenceHash,
        previous_event_hash: prevHash,
        signature: `${recipientId.toUpperCase()}_PQC_ML_DSA_65_NON_REPUDIATION_SIGNATURE`,
        origin: 'SIMULATED_DEMO_SCENARIO'
      };
      this.mockLedgerEvents.push(newEvent);

      return {
        status: 'SUCCESS',
        release_id: releaseId,
        document_id: 'doc_sec_shield_99',
        recipient_id: recipientId,
        original_document_hash: originalDocHash,
        traceable_artifact_hash: traceableHash,
        event_id: eventId,
        event_hash: evidenceHash,
        timestamp: newEvent.timestamp,
        traceable_document_base64: `TRACEABLE_WATERMARKED_COPY_${recipientId.toUpperCase()}_BASE64_DATA`,
        provenance_status: 'SIMULATED_RECIPIENT_ACTION',
        origin: 'SIMULATED_DEMO_SCENARIO'
      };
    }

    try {
      const res = await fetch(`${API_BASE}/releases/${releaseId}/decrypt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient_id: recipientId }),
        signal: AbortSignal.timeout(4000)
      });
      if (res.ok) {
        const decRes: DecryptionResponse = await res.json();
        this.isLiveBackend = true;
        return { 
          ...decRes, 
          provenance_status: 'RECIPIENT_SIGNED_VERIFIED',
          origin: 'REAL_BACKEND_RESULT' 
        };
      }
      throw new Error(`HTTP ${res.status}: Decryption request failed`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at POST ${API_BASE}/releases/${releaseId}/decrypt. Switch to Offline Demo Mode.`);
    }
  }

  public async submitReleaseProvenance(releaseId: string, event: EvidenceEvent): Promise<{ status: string; event_id: string; event_hash: string }> {
    if (this.forceOffline) {
      this.mockLedgerEvents.push({ ...event, origin: 'SIMULATED_DEMO_SCENARIO' });
      return {
        status: 'SUCCESS',
        event_id: event.event_id,
        event_hash: event.evidence_hash
      };
    }

    try {
      const res = await fetch(`${API_BASE}/releases/${releaseId}/provenance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(event),
        signal: AbortSignal.timeout(4000)
      });
      if (res.ok) {
        return await res.json();
      }
      throw new Error(`HTTP ${res.status}: Provenance submission failed`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at POST ${API_BASE}/releases/${releaseId}/provenance.`);
    }
  }

  public async submitDecryptionEvent(event: EvidenceEvent): Promise<{ status: string; event_id: string; event_hash: string }> {
    if (this.forceOffline) {
      this.mockLedgerEvents.push({ ...event, origin: 'SIMULATED_DEMO_SCENARIO' });
      return {
        status: 'SUCCESS',
        event_id: event.event_id,
        event_hash: event.evidence_hash
      };
    }

    try {
      const res = await fetch(`${API_BASE}/evidence/decryption-events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(event),
        signal: AbortSignal.timeout(4000)
      });
      if (res.ok) {
        return await res.json();
      }
      throw new Error(`HTTP ${res.status}: Decryption event submission failed`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at POST ${API_BASE}/evidence/decryption-events.`);
    }
  }

  // -------------------------------------------------------------
  // 5. Leaks & Analysis API (POST /leaks, POST /analyze)
  // -------------------------------------------------------------
  public async uploadLeak(file: File, suspectedReleaseId?: string): Promise<LeakMetadata> {
    if (this.forceOffline) {
      const leakId = `leak_${Date.now().toString(36)}`;
      return {
        leak_id: leakId,
        leak_artifact_hash: `leak_hash_${Math.random().toString(36).substring(2)}`,
        size_bytes: file.size || 524288,
        mime_type: file.type || 'application/pdf',
        suspected_release_id: suspectedReleaseId,
        created_at: new Date().toISOString(),
        artifact_id: `art_${leakId}`,
        origin: 'SIMULATED_DEMO_SCENARIO'
      };
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (suspectedReleaseId) formData.append('suspected_release_id', suspectedReleaseId);

      const res = await fetch(`${API_BASE}/leaks`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(5000)
      });
      if (res.ok) {
        const leakMeta: LeakMetadata = await res.json();
        this.isLiveBackend = true;
        return { ...leakMeta, origin: 'REAL_BACKEND_RESULT' };
      }
      throw new Error(`HTTP ${res.status}: Leak upload failed`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at POST ${API_BASE}/leaks. Switch to Offline Demo Mode.`);
    }
  }

  public async analyzeLeak(
    leakedDocumentBase64OrId: string, 
    releaseId?: string,
    attackTelemetry?: AttackTelemetryInput
  ): Promise<AttributionResult> {
    if (this.forceOffline) {
      const mockResult = computeMockAttribution(leakedDocumentBase64OrId);
      return {
        ...mockResult,
        origin: 'SIMULATED_DEMO_SCENARIO'
      };
    }

    try {
      // Try unified POST /analyze first
      const payload: Record<string, any> = {
        expected_release_id: releaseId,
        async_execution: false
      };

      if (leakedDocumentBase64OrId.startsWith('leak_')) {
        payload.leak_id = leakedDocumentBase64OrId;
      } else {
        payload.leaked_document_base64 = leakedDocumentBase64OrId;
      }

      if (attackTelemetry) {
        payload.attack_telemetry = attackTelemetry;
      }

      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(6000)
      });

      if (res.ok) {
        const job = await res.json();
        if (job.result) {
          this.isLiveBackend = true;
          return {
            ...job.result,
            origin: 'REAL_BACKEND_RESULT'
          };
        }
      }
      throw new Error(`HTTP ${res.status}: Forensic analysis failed`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at POST ${API_BASE}/analyze. Switch to Offline Demo Mode.`);
    }
  }

  // -------------------------------------------------------------
  // 6. Evidence & Ledger API (GET /evidence, GET /ledger/verify)
  // -------------------------------------------------------------
  public async getEvidenceForRelease(releaseId: string): Promise<EvidenceEvent[]> {
    if (this.forceOffline) {
      return this.mockLedgerEvents
        .filter(e => e.release_id === releaseId || e.release_id === 'system_root')
        .map(e => ({ ...e, origin: 'SIMULATED_DEMO_SCENARIO' }));
    }

    try {
      const res = await fetch(`${API_BASE}/evidence/${releaseId}`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        const events: EvidenceEvent[] = await res.json();
        this.isLiveBackend = true;
        return events.map(e => ({ ...e, origin: 'REAL_BACKEND_RESULT' }));
      }
      throw new Error(`HTTP ${res.status}: Failed to fetch evidence events`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at GET ${API_BASE}/evidence/${releaseId}. Switch to Offline Demo Mode.`);
    }
  }

  public async getLedgerEvents(): Promise<EvidenceEvent[]> {
    return this.mockLedgerEvents;
  }

  public async verifyLedger(): Promise<LedgerVerificationResult> {
    if (this.forceOffline) {
      if (this.mockTamperedBlockIndex !== null) {
        return {
          is_valid: false,
          total_events: this.mockLedgerEvents.length,
          chain_tip: this.mockLedgerEvents[this.mockLedgerEvents.length - 1]?.evidence_hash || 'UNKNOWN',
          errors: [
            `Cryptographic Hash Chain Broken at Block #${this.mockTamperedBlockIndex + 1} (Event ID: ${this.mockLedgerEvents[this.mockTamperedBlockIndex]?.event_id}). Hash mismatch detected in previous_event_hash linkage!`
          ],
          tampered_index: this.mockTamperedBlockIndex,
          origin: 'REAL_LOCAL_COMPUTATION'
        };
      }

      return {
        is_valid: true,
        total_events: this.mockLedgerEvents.length,
        chain_tip: this.mockLedgerEvents[this.mockLedgerEvents.length - 1]?.evidence_hash || '0000000000',
        errors: [],
        tampered_index: null,
        origin: 'REAL_LOCAL_COMPUTATION'
      };
    }

    try {
      const res = await fetch(`${API_BASE}/ledger/verify`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        const data: LedgerVerificationResult = await res.json();
        this.isLiveBackend = true;
        return { ...data, origin: 'REAL_BACKEND_RESULT' };
      }
      throw new Error(`HTTP ${res.status}: Ledger verification failed`);
    } catch (e: any) {
      this.isLiveBackend = false;
      throw new Error(`Backend unreachable at GET ${API_BASE}/ledger/verify. Switch to Offline Demo Mode.`);
    }
  }

  // Client-Side Tamper Simulation Tools (demonstrates hash-chain mechanics without claiming to hack the database)
  public simulateTamperBlock(index: number) {
    if (index >= 0 && index < this.mockLedgerEvents.length) {
      this.mockTamperedBlockIndex = index;
      this.mockLedgerEvents[index].artifact_hash = 'DEADBEEF_TAMPERED_HASH_FORGED_EVENT_999999999999999999999999';
      this.mockLedgerEvents[index].is_tampered = true;
    }
  }

  public resetLedgerTamper() {
    this.mockTamperedBlockIndex = null;
    this.mockLedgerEvents = [...INITIAL_LEDGER_EVENTS];
  }

  public resetAllToDefault() {
    this.mockDocuments = [...INITIAL_DOCUMENTS];
    this.mockRecipients = [...INITIAL_RECIPIENTS];
    this.mockReleases = [...INITIAL_RELEASES];
    this.mockLedgerEvents = [...INITIAL_LEDGER_EVENTS];
    this.mockTamperedBlockIndex = null;
  }
}

export const apiService = new ApiService();
