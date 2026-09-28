/**
 * AegisTrace Semantic Service Abstraction Layer
 * ============================================
 * Provides high-level, task-oriented interfaces following the Car Analogy:
 * Operators and investigators interact with semantic concepts:
 *   - Import (ArtifactService)
 *   - Protect & Distribute (ProtectionService & ReleaseService)
 *   - Investigate (InvestigationService)
 *   - Examine (EvidenceService)
 *   - Audit & Validate (VerificationService)
 *
 * Engineering implementations (ML-KEM-768, ML-DSA-65, DSSS, RS-ECC, RFC-6962 Merkle proofs)
 * are encapsulated beneath these boundaries and exposed selectively via Level 3 Technical Details.
 */

import { apiService } from './api';
import { 
  DocumentMetadata, 
  DocumentRelease, 
  AttributionResult, 
  EvidenceRecord, 
  InvestigationRecord,
  AttackTelemetryInput
} from '../types';

// ---------------------------------------------------------------------------
// Semantic Domain Models
// ---------------------------------------------------------------------------

export interface ArtifactItem {
  id: string;
  name: string;
  hash: string;
  sizeBytes: number;
  mimeType: string;
  classification?: string;
  ownerName?: string;
  createdAt: string;
}

export interface ProtectionResult {
  releaseId: string;
  documentId: string;
  recipientCount: number;
  recipientNames: string[];
  sealedAt: string;
  technicalDetails: {
    cipher: string;
    kemAlgorithm: string;
    signatureAlgorithm: string;
    keyWrapping: string;
    watermarkType: string;
  };
}

export interface InvestigationVerdict {
  investigationId: string;
  verdict: 'ATTRIBUTED' | 'NO_SIGNAL' | 'INSUFFICIENT_EVIDENCE' | 'CONFLICT' | 'ABSTAIN';
  suspectedActor?: {
    id: string;
    name: string;
    organization?: string;
    role?: string;
  };
  confidenceRating: 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
  confidencePercentage: number;
  shouldAbstain: boolean;
  facts: {
    artifactHash: string;
    leakSource: string;
    timestamp: string;
    channelsEvaluated: number;
  };
  technicalDetails: {
    fusedScore: number;
    separationMargin: number;
    bayesianPosterior: number;
    channels: Array<{
      channel: string;
      weight: number;
      rawScore: number;
      contribution: number;
    }>;
  };
}

export interface PackageVerificationOutcome {
  packageId: string;
  isVerified: boolean;
  statusText: string;
  verifiedAt: string;
  errors: string[];
  warnings: string[];
  technicalDetails: {
    manifestSignatureValid: boolean;
    merkleRootValid: boolean;
    objectHashesValid: boolean;
    dependencyGraphValid: boolean;
    custodyChainValid: boolean;
    historicalKeysValid: boolean;
    ledgerProofValid: boolean;
  };
}

// ---------------------------------------------------------------------------
// 1. ArtifactService (Import & Catalog Management)
// ---------------------------------------------------------------------------
export class ArtifactService {
  static async importArtifact(file: File, name?: string): Promise<ArtifactItem> {
    const doc = await apiService.uploadDocument(file, name);
    return {
      id: doc.document_id,
      name: doc.document_name,
      hash: doc.original_document_hash,
      sizeBytes: doc.size_bytes,
      mimeType: doc.mime_type,
      classification: doc.classification,
      ownerName: doc.owner_name,
      createdAt: doc.created_at
    };
  }

  static async listArtifacts(): Promise<ArtifactItem[]> {
    const docs = await apiService.getDocuments();
    return docs.map(doc => ({
      id: doc.document_id,
      name: doc.document_name,
      hash: doc.original_document_hash,
      sizeBytes: doc.size_bytes,
      mimeType: doc.mime_type,
      classification: doc.classification,
      ownerName: doc.owner_name,
      createdAt: doc.created_at
    }));
  }
}

// ---------------------------------------------------------------------------
// 2. ProtectionService & ReleaseService (Cryptographic Sealing & Distribution)
// ---------------------------------------------------------------------------
export class ProtectionService {
  static async protectAndDistribute(params: {
    documentName: string;
    documentBase64: string;
    recipientIds: string[];
    documentId?: string;
    tardosEnabled?: boolean;
    targets?: Array<{ target_type: 'INDIVIDUAL' | 'GROUP'; target_id: string }>;
  }): Promise<ProtectionResult> {
    const release = await apiService.createRelease(
      params.documentName,
      params.documentBase64,
      params.recipientIds,
      params.documentId,
      params.tardosEnabled,
      params.targets
    );

    return {
      releaseId: release.release_id,
      documentId: release.document_id,
      recipientCount: release.packages ? Object.keys(release.packages).length : params.recipientIds.length,
      recipientNames: release.packages ? Object.keys(release.packages) : params.recipientIds,
      sealedAt: release.created_at,
      technicalDetails: {
        cipher: 'AES-256-GCM',
        kemAlgorithm: 'ML-KEM-768 (NIST FIPS 203)',
        signatureAlgorithm: 'ML-DSA-65 (NIST FIPS 204)',
        keyWrapping: 'RFC 3394 AES-KW via HKDF-SHA256',
        watermarkType: 'Decryption-Time 2D DSSS Carrier'
      }
    };
  }

  static async listReleases(): Promise<DocumentRelease[]> {
    return apiService.getReleases();
  }
}

// ---------------------------------------------------------------------------
// 3. InvestigationService (Forensic Ingestion & Attribution)
// ---------------------------------------------------------------------------
export class InvestigationService {
  static async investigateLeak(params: {
    scenarioIdOrFileId: string;
    releaseId?: string;
    telemetry?: AttackTelemetryInput;
  }): Promise<InvestigationVerdict> {
    const res = await apiService.analyzeLeak(
      params.scenarioIdOrFileId,
      params.releaseId,
      params.telemetry
    );

    const verdict = res.state as InvestigationVerdict['verdict'];
    const confidenceRating = res.confidence_level as InvestigationVerdict['confidenceRating'];

    return {
      investigationId: (res as any).investigation_id || (res as any).analysis_id || `inv_${Date.now()}`,
      verdict,
      suspectedActor: res.candidate ? {
        id: res.candidate.recipient_id,
        name: res.candidate.name,
        organization: res.candidate.identity_summary?.organization_id || (res.candidate as any).organization_id || 'Defense Sector',
        role: res.candidate.identity_summary?.title || (res.candidate as any).role || 'Officer'
      } : undefined,
      confidenceRating,
      confidencePercentage: Math.round((res.confidence || 0) * 100),
      shouldAbstain: res.should_abstain ?? (verdict !== 'ATTRIBUTED'),
      facts: {
        artifactHash: (res as any).leak_artifact_hash || 'unknown',
        leakSource: params.releaseId || 'Broadcast Artifact',
        timestamp: (res as any).timestamp || new Date().toISOString(),
        channelsEvaluated: res.channels?.length || (res as any).fusion_scores?.length || 0
      },
      technicalDetails: {
        fusedScore: res.fused_score || 0,
        separationMargin: res.margin || 0,
        bayesianPosterior: res.confidence || 0,
        channels: (res.channels || (res as any).fusion_scores || []).map((ch: any) => ({
          channel: ch.channel_name,
          weight: ch.reliability || ch.channel_weight || 1.0,
          rawScore: ch.llr || ch.score || 0,
          contribution: ch.effective_llr || (ch.score ? ch.score * (ch.channel_weight || 1) : 0)
        }))
      }
    };
  }

  static async listHistoricalInvestigations(): Promise<InvestigationRecord[]> {
    return apiService.getHistoricalInvestigations();
  }
}

// ---------------------------------------------------------------------------
// 4. EvidenceService (Custody & Provenance Audit)
// ---------------------------------------------------------------------------
export class EvidenceService {
  static async listEvidenceRecords(): Promise<EvidenceRecord[]> {
    return apiService.getEvidenceRecords();
  }

  static async verifyLedgerAuditTrail(): Promise<{
    isValid: boolean;
    totalEvents: number;
    chainTip: string;
    errors: string[];
  }> {
    const res = await apiService.verifyLedger();
    return {
      isValid: res.is_valid,
      totalEvents: res.total_events,
      chainTip: res.chain_tip,
      errors: res.errors
    };
  }
}

// ---------------------------------------------------------------------------
// 5. VerificationService (Standalone Evidence Package Auditor)
// ---------------------------------------------------------------------------
export class VerificationService {
  static async verifyPackage(file: File): Promise<PackageVerificationOutcome> {
    try {
      const result = await apiService.verifyEvidencePackage(file);
      const isVerified = result.overall_status === 'VERIFIED';
      return {
        packageId: result.package_id || file.name,
        isVerified,
        statusText: result.overall_status || (isVerified ? 'VERIFIED' : 'FAILED'),
        verifiedAt: result.verified_at || new Date().toISOString(),
        errors: result.errors || [],
        warnings: result.warnings || [],
        technicalDetails: {
          manifestSignatureValid: result.manifest_signature_valid ?? false,
          merkleRootValid: result.merkle_root_valid ?? false,
          objectHashesValid: result.object_hashes_valid ?? false,
          dependencyGraphValid: result.dependency_graph_valid ?? false,
          custodyChainValid: result.custody_chain_valid ?? false,
          historicalKeysValid: result.historical_keys_valid ?? false,
          ledgerProofValid: result.ledger_proof_valid ?? false
        }
      };
    } catch (err: any) {
      return {
        packageId: file.name,
        isVerified: false,
        statusText: 'VERIFICATION FAILED',
        verifiedAt: new Date().toISOString(),
        errors: [err.message || 'Evidence package verification protocol failed.'],
        warnings: [],
        technicalDetails: {
          manifestSignatureValid: false,
          merkleRootValid: false,
          objectHashesValid: false,
          dependencyGraphValid: false,
          custodyChainValid: false,
          historicalKeysValid: false,
          ledgerProofValid: false
        }
      };
    }
  }
}
