import math
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field

from core.attribution.evidence import (
    AttributionState,
    EvidenceFamily,
    DependencyType,
    EvidenceConfidenceLevel,
    EvidenceObservation,
    EvidenceBundle,
    ProvenanceObservation,
    LineageObservation,
)
from core.lineage.models import (
    ForensicAttributionLevel,
    ForensicBoundaryState,
)
from core.attribution.dependency import EvidenceDependencyGraph
from core.attribution.reliability import AttackAwareReliabilityCalibrator
from core.attribution.policy import DecisionPolicy

class CandidateEvaluation(BaseModel):
    candidate_id: str
    fused_score: float
    posterior_probability: float
    supporting_observations: List[str] = Field(default_factory=list)
    contradicting_observations: List[str] = Field(default_factory=list)

class FusedAttributionResult(BaseModel):
    """
    Complete forensic fusion result with explainability and audit trail.
    """
    state: AttributionState
    top_candidate_id: Optional[str] = None
    confidence: float = 0.0
    confidence_level: EvidenceConfidenceLevel = EvidenceConfidenceLevel.NONE
    fused_score: float = 0.0
    runner_up_candidate_id: Optional[str] = None
    runner_up_score: float = 0.0
    separation_margin: float = 0.0

    candidate_evaluations: List[CandidateEvaluation] = Field(default_factory=list)
    supporting_sources: List[str] = Field(default_factory=list)
    contradicting_sources: List[str] = Field(default_factory=list)
    
    summary: str
    should_abstain: bool = True
    
    # Comprehensive forensic breakdown fields
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    attack_telemetry: Optional[Dict[str, Any]] = None
    
    reasoning_steps: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)

    # Active Cryptographic Copy Lineage forensic outputs
    forensic_attribution_level: Optional[ForensicAttributionLevel] = None
    forensic_boundary_state: Optional[ForensicBoundaryState] = None
    last_known_holder: Optional[str] = None
    lineage_proof: Optional[Dict[str, Any]] = None
    candidate: Optional[Any] = None

class EvidenceFusionEngine:
    """
    Multi-Channel Bayesian Evidence Fusion Engine for SIH26237.
    
    Combines heterogeneous, noisy, and potentially adversarial evidence signals:
    - Tardos Traitor-Tracing fingerprints
    - Spatial/Frequency Watermark extractions
    - ML-DSA-65 Post-Quantum provenance signatures
    - SHA-256 Tamper-evident ledger chain verification
    - Attack context & physical capture metrics
    
    Adheres strictly to the principle: NEVER FORCE AN ATTRIBUTION.
    """

    def __init__(
        self,
        dependency_graph: Optional[EvidenceDependencyGraph] = None,
        calibrator: Optional[AttackAwareReliabilityCalibrator] = None,
        policy: Optional[DecisionPolicy] = None
    ):
        self.dependency_graph = dependency_graph or EvidenceDependencyGraph()
        self.calibrator = calibrator or AttackAwareReliabilityCalibrator()
        self.policy = policy or DecisionPolicy()

    def _extract_lineage_metadata(
        self,
        bundle: EvidenceBundle,
        state: AttributionState,
        top_cand_id: Optional[str]
    ) -> Tuple[Optional[ForensicAttributionLevel], Optional[ForensicBoundaryState], Optional[str], Optional[Dict[str, Any]]]:
        lineage_obs: Optional[LineageObservation] = None
        for o in bundle.observations:
            if isinstance(o, LineageObservation) or getattr(o, "family", None) == EvidenceFamily.COPY_LINEAGE:
                lineage_obs = o
                break

        # Check for corroborating external telemetry
        has_telemetry_corroboration = False
        if lineage_obs and getattr(lineage_obs, "telemetry_corroborated", False):
            has_telemetry_corroboration = True
        else:
            for o in bundle.observations:
                if getattr(o, "family", None) == EvidenceFamily.EXTERNAL_TELEMETRY:
                    if getattr(o, "is_human_corroborated", False):
                        has_telemetry_corroboration = True
                        break

        if lineage_obs:
            level = getattr(lineage_obs, "attribution_level", ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED)
            b_state = getattr(lineage_obs, "boundary_state", ForensicBoundaryState.LINEAGE_CONTINUES)
            holder = getattr(lineage_obs, "last_known_holder", top_cand_id)
            proof = getattr(lineage_obs, "proof_details", {})

            # Elevate to Level 5 if state is ATTRIBUTED and external corroborating telemetry exists
            if state == AttributionState.ATTRIBUTED and has_telemetry_corroboration:
                level = ForensicAttributionLevel.LEVEL_5_HUMAN_IDENTITY_RESOLVED

            return level, b_state, holder, proof

        if state == AttributionState.ATTRIBUTED:
            level = (
                ForensicAttributionLevel.LEVEL_5_HUMAN_IDENTITY_RESOLVED
                if has_telemetry_corroboration
                else ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED
            )
            return (
                level,
                ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR,
                top_cand_id,
                None,
            )
        else:
            b_st = ForensicBoundaryState.INSUFFICIENT_EVIDENCE if state == AttributionState.INSUFFICIENT_EVIDENCE else ForensicBoundaryState.ABSTAINED
            return (
                ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED,
                b_st,
                None,
                None,
            )

    def fuse(self, bundle: EvidenceBundle) -> FusedAttributionResult:
        reasoning_steps: List[str] = []
        recommended_next_steps: List[str] = []

        reasoning_steps.append(f"Initiated multi-channel fusion for bundle '{bundle.bundle_id}'.")

        # Step 1: Validate bundle target binding
        is_binding_valid, binding_violations = self.dependency_graph.validate_bundle_binding(bundle)
        if not is_binding_valid:
            reasoning_steps.append(f"Binding check failed: {'; '.join(binding_violations)}")
            f_level, f_state, f_holder, f_proof = self._extract_lineage_metadata(bundle, AttributionState.CONFLICT, None)
            return FusedAttributionResult(
                state=AttributionState.CONFLICT,
                top_candidate_id=None,
                confidence=0.0,
                confidence_level=EvidenceConfidenceLevel.NONE,
                fused_score=0.0,
                summary="Abstain: Evidence bundle contains conflicting target bindings (cross-document contamination).",
                should_abstain=True,
                reasoning_steps=reasoning_steps,
                recommended_next_steps=[
                    "Isolate carrier artifacts by document_id and release_id.",
                    "Verify provenance logs for release scope contamination."
                ],
                details={"binding_violations": binding_violations},
                forensic_attribution_level=f_level,
                forensic_boundary_state=f_state,
                last_known_holder=f_holder,
                lineage_proof=f_proof,
            )

        reasoning_steps.append("Document and release target bindings validated successfully.")

        # Step 2: Calibrate observation reliabilities based on attack context
        self.calibrator.calibrate_bundle(bundle)
        valid_observations = [o for o in bundle.observations if o.is_valid]
        invalid_observations = [o for o in bundle.observations if not o.is_valid]

        if not valid_observations:
            reasoning_steps.append("No valid forensic signals detected across any channel.")
            f_level, f_state, f_holder, f_proof = self._extract_lineage_metadata(bundle, AttributionState.NO_SIGNAL, None)
            return FusedAttributionResult(
                state=AttributionState.NO_SIGNAL,
                top_candidate_id=None,
                confidence=0.0,
                confidence_level=EvidenceConfidenceLevel.NONE,
                fused_score=0.0,
                summary="Abstain: No valid forensic signal detected across any evidence channel.",
                should_abstain=True,
                reasoning_steps=reasoning_steps,
                recommended_next_steps=[
                    "Attempt higher-sensitivity frequency-domain watermark extraction.",
                    "Inspect carrier artifact for structural truncation or heavy cropping."
                ],
                forensic_attribution_level=f_level,
                forensic_boundary_state=f_state,
                last_known_holder=f_holder,
                lineage_proof=f_proof,
            )

        reasoning_steps.append(
            f"Calibrated {len(valid_observations)} valid forensic observations "
            f"({len(invalid_observations)} invalid/suppressed)."
        )

        # Step 3: Compute candidate scores via Anti-Double-Counting Dependency Graph
        candidate_scores = self.dependency_graph.compute_fused_candidate_scores(bundle)

        if not candidate_scores:
            reasoning_steps.append("No candidates identified by any evidence channel.")
            f_level, f_state, f_holder, f_proof = self._extract_lineage_metadata(bundle, AttributionState.NO_SIGNAL, None)
            return FusedAttributionResult(
                state=AttributionState.NO_SIGNAL,
                top_candidate_id=None,
                confidence=0.0,
                confidence_level=EvidenceConfidenceLevel.NONE,
                fused_score=0.0,
                summary="Abstain: No candidates identified in evidence signals.",
                should_abstain=True,
                reasoning_steps=reasoning_steps,
                recommended_next_steps=["Verify if leak matches known enrollment registry."],
                forensic_attribution_level=f_level,
                forensic_boundary_state=f_state,
                last_known_holder=f_holder,
                lineage_proof=f_proof,
            )

        # Sort candidates descending by score
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        top_cand_id, top_score = sorted_candidates[0]

        runner_up_cand_id = sorted_candidates[1][0] if len(sorted_candidates) > 1 else None
        runner_up_score = sorted_candidates[1][1] if len(sorted_candidates) > 1 else 0.0
        separation_margin = top_score - runner_up_score

        reasoning_steps.append(
            f"Candidate ranking computed: Top '{top_cand_id}' (score={top_score:.2f}), "
            f"Runner-up '{runner_up_cand_id}' (score={runner_up_score:.2f}), "
            f"Margin={separation_margin:.2f}."
        )

        # Build candidate evaluation breakdowns
        evaluations: List[CandidateEvaluation] = []
        for cid, sc in sorted_candidates:
            supp = [
                o.source_id for o in valid_observations
                if (o.primary_candidate == cid or o.candidate_scores.get(cid, 0) > 0)
            ]
            contra = [
                o.source_id for o in valid_observations
                if (o.primary_candidate and o.primary_candidate != cid and o.candidate_scores.get(cid, 0) <= 0)
            ]
            evaluations.append(CandidateEvaluation(
                candidate_id=cid,
                fused_score=sc,
                posterior_probability=self.policy.compute_probability(sc),
                supporting_observations=supp,
                contradicting_observations=contra
            ))

        top_evaluation = evaluations[0]
        supporting_sources = top_evaluation.supporting_observations
        contradicting_sources = top_evaluation.contradicting_observations

        # Step 4: Strict Provenance Signature Check (if required by policy)
        if self.policy.strict_provenance_required:
            prov_obs = [
                o for o in bundle.get_by_family(EvidenceFamily.PROVENANCE_SIGNATURE)
                if isinstance(o, ProvenanceObservation) and o.signature_valid and o.signer_recipient_id == top_cand_id
            ]
            if not prov_obs:
                reasoning_steps.append(
                    f"Strict provenance required, but no valid signature found for top candidate '{top_cand_id}'."
                )
                return FusedAttributionResult(
                    state=AttributionState.INSUFFICIENT_EVIDENCE,
                    top_candidate_id=top_cand_id,
                    confidence=self.policy.compute_probability(top_score),
                    confidence_level=EvidenceConfidenceLevel.LOW,
                    fused_score=top_score,
                    runner_up_candidate_id=runner_up_cand_id,
                    runner_up_score=runner_up_score,
                    separation_margin=separation_margin,
                    candidate_evaluations=evaluations,
                    supporting_sources=supporting_sources,
                    contradicting_sources=contradicting_sources,
                    summary=f"Abstain: Candidate '{top_cand_id}' lacks mandatory cryptographic provenance signature.",
                    should_abstain=True,
                    reasoning_steps=reasoning_steps,
                    recommended_next_steps=["Inspect audit ledger for corresponding recipient decryption event."]
                )

        # Step 4.5: Primary Cryptographic Marker Corroboration Check
        # Non-cryptographic secondary channels (e.g. DOCUMENT_STRUCTURE) CANNOT trigger ATTRIBUTED on their own
        # without at least ONE primary cryptographic evidence source (WATERMARK_PAYLOAD, TARDOS_FINGERPRINT, PROVENANCE_SIGNATURE).
        primary_crypto_families = {
            EvidenceFamily.WATERMARK_PAYLOAD,
            EvidenceFamily.TARDOS_FINGERPRINT,
            EvidenceFamily.PROVENANCE_SIGNATURE
        }
        supporting_obs_objs = [
            o for o in valid_observations if o.source_id in supporting_sources
        ]
        has_crypto_corroboration = any(
            o.family in primary_crypto_families for o in supporting_obs_objs
        )

        if not has_crypto_corroboration:
            reasoning_steps.append(
                f"Abstain: Top candidate '{top_cand_id}' supported only by non-cryptographic channels without primary marker corroboration."
            )
            return FusedAttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                top_candidate_id=top_cand_id,
                confidence=self.policy.compute_probability(top_score),
                confidence_level=EvidenceConfidenceLevel.LOW,
                fused_score=top_score,
                runner_up_candidate_id=runner_up_cand_id,
                runner_up_score=runner_up_score,
                separation_margin=separation_margin,
                candidate_evaluations=evaluations,
                supporting_sources=supporting_sources,
                contradicting_sources=contradicting_sources,
                summary=f"Abstain: Non-cryptographic evidence for '{top_cand_id}' lacks primary marker corroboration.",
                should_abstain=True,
                reasoning_steps=reasoning_steps,
                recommended_next_steps=[
                    "Extract primary spatial or frequency watermark from carrier.",
                    "Verify decryption provenance events in audit ledger."
                ]
            )

        # Step 5: Check for Conflict (distinct reliable independent sources pointing to different candidates)
        # A conflict occurs if EITHER:
        # (a) Runner-up score >= conflict_runnerup_threshold AND margin < min_separation_margin
        # (b) Runner-up candidate is supported by a distinct primary cryptographic channel with score >= conflict_runnerup_threshold
        is_narrow_margin_conflict = (
            len(sorted_candidates) > 1
            and runner_up_score >= self.policy.conflict_runnerup_threshold
            and separation_margin < self.policy.min_separation_margin
        )

        runner_up_obs = [
            o for o in valid_observations
            if o.source_id in (evaluations[1].supporting_observations if len(evaluations) > 1 else [])
        ]
        is_crypto_channel_conflict = (
            len(sorted_candidates) > 1
            and runner_up_score >= self.policy.conflict_runnerup_threshold
            and any(o.family in primary_crypto_families for o in runner_up_obs)
        )

        if is_narrow_margin_conflict or is_crypto_channel_conflict:
            reasoning_steps.append(
                f"Conflict detected: Candidate '{top_cand_id}' ({top_score:.2f}) and '{runner_up_cand_id}' "
                f"({runner_up_score:.2f}) represent an irreconcilable multi-source cryptographic disagreement."
            )
            f_level, f_state, f_holder, f_proof = self._extract_lineage_metadata(bundle, AttributionState.CONFLICT, top_cand_id)
            return FusedAttributionResult(
                state=AttributionState.CONFLICT,
                top_candidate_id=top_cand_id,
                confidence=self.policy.compute_probability(top_score),
                confidence_level=EvidenceConfidenceLevel.LOW,
                fused_score=top_score,
                runner_up_candidate_id=runner_up_cand_id,
                runner_up_score=runner_up_score,
                separation_margin=separation_margin,
                candidate_evaluations=evaluations,
                supporting_sources=supporting_sources,
                contradicting_sources=contradicting_sources,
                summary=f"Abstain: Irreconcilable conflict between candidates '{top_cand_id}' and '{runner_up_cand_id}'.",
                should_abstain=True,
                reasoning_steps=reasoning_steps,
                recommended_next_steps=[
                    "Check for multi-recipient collusion attack.",
                    "Verify if leaked artifact represents a spliced or blended composite."
                ],
                forensic_attribution_level=f_level,
                forensic_boundary_state=f_state,
                last_known_holder=f_holder,
                lineage_proof=f_proof,
            )

        # Step 6: Check Attribution Thresholds
        if top_score < self.policy.min_attribution_score:
            reasoning_steps.append(
                f"Top score {top_score:.2f} is below minimum attribution threshold {self.policy.min_attribution_score}."
            )
            f_level, f_state, f_holder, f_proof = self._extract_lineage_metadata(bundle, AttributionState.INSUFFICIENT_EVIDENCE, top_cand_id)
            return FusedAttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                top_candidate_id=top_cand_id,
                confidence=self.policy.compute_probability(top_score),
                confidence_level=self.policy.evaluate_confidence_level(top_score),
                fused_score=top_score,
                runner_up_candidate_id=runner_up_cand_id,
                runner_up_score=runner_up_score,
                separation_margin=separation_margin,
                candidate_evaluations=evaluations,
                supporting_sources=supporting_sources,
                contradicting_sources=contradicting_sources,
                summary=f"Abstain: Evidence strength ({top_score:.2f}) is insufficient for reliable attribution.",
                should_abstain=True,
                reasoning_steps=reasoning_steps,
                recommended_next_steps=[
                    "Collect additional document pages or higher resolution scans.",
                    "Correlate ledger logs for suspicious release access timing."
                ],
                forensic_attribution_level=f_level,
                forensic_boundary_state=f_state,
                last_known_holder=f_holder,
                lineage_proof=f_proof,
            )

        # Step 7: Check Separation Margin
        if len(sorted_candidates) > 1 and separation_margin < self.policy.min_separation_margin:
            reasoning_steps.append(
                f"Separation margin {separation_margin:.2f} is below minimum requirement {self.policy.min_separation_margin}."
            )
            f_level, f_state, f_holder, f_proof = self._extract_lineage_metadata(bundle, AttributionState.INSUFFICIENT_EVIDENCE, top_cand_id)
            return FusedAttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                top_candidate_id=top_cand_id,
                confidence=self.policy.compute_probability(top_score),
                confidence_level=EvidenceConfidenceLevel.LOW,
                fused_score=top_score,
                runner_up_candidate_id=runner_up_cand_id,
                runner_up_score=runner_up_score,
                separation_margin=separation_margin,
                candidate_evaluations=evaluations,
                supporting_sources=supporting_sources,
                contradicting_sources=contradicting_sources,
                summary=f"Abstain: Insufficient candidate separation margin ({separation_margin:.2f} < {self.policy.min_separation_margin}).",
                should_abstain=True,
                reasoning_steps=reasoning_steps,
                recommended_next_steps=[
                    "Analyze collusion probability across top candidates.",
                    "Extract secondary forensic markers from supplementary carrier channels."
                ],
                forensic_attribution_level=f_level,
                forensic_boundary_state=f_state,
                last_known_holder=f_holder,
                lineage_proof=f_proof,
            )

        # Step 8: Attribution Decision
        confidence_level = self.policy.evaluate_confidence_level(top_score)
        prob = self.policy.compute_probability(top_score)
        reasoning_steps.append(
            f"Attribution criteria satisfied for '{top_cand_id}' with fused score {top_score:.2f}, "
            f"confidence {confidence_level.value}, posterior {prob:.4f}."
        )

        default_assumptions = {
            "prior_odds": "UNIFORM_ACROSS_RECIPIENTS",
            "correlation_discount_gamma": self.dependency_graph.correlation_discount,
            "min_attribution_score_threshold": self.policy.min_attribution_score,
            "min_separation_margin_threshold": self.policy.min_separation_margin,
            "heuristic_policy_scaling": True
        }
        telemetry = bundle.attack_context.model_dump() if bundle.attack_context else None

        f_level, f_state, f_holder, f_proof = self._extract_lineage_metadata(bundle, AttributionState.ATTRIBUTED, top_cand_id)

        if f_state == ForensicBoundaryState.LAST_KNOWN_HOLDER:
            summary_text = f"Attributed to last known controlled custodian '{top_cand_id}' (Downstream uncontrolled leakage detected; intermediary not personally accused)."
        else:
            summary_text = f"Successfully attributed leak to recipient '{top_cand_id}' ({confidence_level.value} confidence)."

        return FusedAttributionResult(
            state=AttributionState.ATTRIBUTED,
            top_candidate_id=top_cand_id,
            confidence=prob,
            confidence_level=confidence_level,
            fused_score=top_score,
            runner_up_candidate_id=runner_up_cand_id,
            runner_up_score=runner_up_score,
            separation_margin=separation_margin,
            candidate_evaluations=evaluations,
            supporting_sources=supporting_sources,
            contradicting_sources=contradicting_sources,
            summary=summary_text,
            should_abstain=False,
            assumptions=default_assumptions,
            attack_telemetry=telemetry,
            reasoning_steps=reasoning_steps,
            recommended_next_steps=[
                "Document forensic chain of custody in tamper-evident ledger.",
                "Export verification package for compliance audit."
            ],
            details={
                "calibrated_observations_count": len(valid_observations),
                "top_candidate_score": top_score,
                "separation_margin": separation_margin
            },
            forensic_attribution_level=f_level,
            forensic_boundary_state=f_state,
            last_known_holder=f_holder,
            lineage_proof=f_proof,
        )
