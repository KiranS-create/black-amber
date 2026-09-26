import math
from typing import List, Dict, Set, Tuple, Optional
from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceObservation,
    DependencyType,
    EvidenceFamily,
    TargetBinding,
    LedgerObservation
)

class DependencyResolutionError(Exception):
    """Raised when evidence graph contains circular dependencies or invalid references."""
    pass

class CrossDocumentContaminationError(Exception):
    """Raised when evidence from a different document/release is found in the bundle."""
    pass

class EvidenceDependencyGraph:
    """
    Forensic Dependency Graph and Anti-Double-Counting Engine.
    
    Prevents artificial inflation of attribution confidence by:
    1. Deduplicating identical or re-submitted observation payloads.
    2. Tracking derivation trees (e.g. watermark bitstreams -> Tardos statistics).
    3. Applying the Maximum Evidentiary Bound across derivation trees instead of additive summation.
    4. Applying correlation discount gamma (HEURISTIC POLICY PARAMETER, default 0.65) to partially dependent channels.
    5. Validating target bindings (document_id, release_id, artifact_hash) to prevent
       cross-document evidence contamination.
    """

    DEFAULT_CORRELATION_DISCOUNT = 0.65

    def __init__(self, correlation_discount: float = DEFAULT_CORRELATION_DISCOUNT):
        if not (0.0 < correlation_discount <= 1.0):
            raise ValueError(f"Correlation discount must be in (0, 1], got {correlation_discount}")
        self.correlation_discount = correlation_discount

    def validate_bundle_binding(
        self,
        bundle: EvidenceBundle,
        strict_hash: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Verify that all observations in the bundle belong to the same document/release scope.
        Returns (is_valid, list_of_violations).
        """
        violations = []
        target = bundle.target_binding

        for obs in bundle.observations:
            obs_bind = obs.target_binding
            # Check document_id mismatch
            if target.document_id and obs_bind.document_id and target.document_id != obs_bind.document_id:
                violations.append(
                    f"Observation '{obs.source_id}' document_id '{obs_bind.document_id}' "
                    f"does not match target document_id '{target.document_id}'"
                )
            # Check release_id mismatch
            if target.release_id and obs_bind.release_id and target.release_id != obs_bind.release_id:
                violations.append(
                    f"Observation '{obs.source_id}' release_id '{obs_bind.release_id}' "
                    f"does not match target release_id '{target.release_id}'"
                )
            # Check artifact_hash mismatch if strict
            if strict_hash and target.artifact_hash and obs_bind.artifact_hash and target.artifact_hash != obs_bind.artifact_hash:
                violations.append(
                    f"Observation '{obs.source_id}' artifact_hash '{obs_bind.artifact_hash}' "
                    f"does not match target artifact_hash '{target.artifact_hash}'"
                )

        return (len(violations) == 0, violations)

    def deduplicate_observations(
        self,
        observations: List[EvidenceObservation]
    ) -> List[EvidenceObservation]:
        """
        Adversarial deduplication: collapse observations that share the same signal payload
        fingerprint or identical (family, source_id) to prevent repetition attacks.
        """
        seen_fingerprints: Set[str] = set()
        seen_source_ids: Set[str] = set()
        deduped: List[EvidenceObservation] = []

        for obs in observations:
            if not obs.is_valid:
                continue
            
            # Source ID deduplication
            if obs.source_id in seen_source_ids:
                continue

            # Payload fingerprint deduplication
            fp = obs.compute_signal_fingerprint()
            if fp in seen_fingerprints:
                continue

            seen_source_ids.add(obs.source_id)
            seen_fingerprints.add(fp)
            deduped.append(obs)

        return deduped

    def compute_fused_candidate_scores(
        self,
        bundle: EvidenceBundle,
        candidate_ids: Optional[Set[str]] = None
    ) -> Dict[str, float]:
        """
        Compute anti-double-counted, reliability-calibrated log-likelihood scores for all candidates.
        
        Fusion Mathematics:
        For candidate c:
          - Independent channels i: contribute rho_i * LLR_i(c)
          - Partially dependent channels p: contribute gamma * rho_p * LLR_p(c)
          - Derived trees (parent, children, grandchildren): contribute max contribution across tree
        """
        if candidate_ids is None:
            candidate_ids = bundle.get_candidate_ids()

        if not candidate_ids:
            return {}

        # 1. Adversarial deduplication of valid observations
        valid_observations = self.deduplicate_observations(bundle.observations)

        obs_map: Dict[str, EvidenceObservation] = {o.source_id: o for o in valid_observations}

        # 2. Build derivation tree mapping parent -> children
        derived_children_map: Dict[str, List[EvidenceObservation]] = {}
        for obs in obs_map.values():
            if obs.dependency_type == DependencyType.DERIVED and obs.parent_source_id:
                derived_children_map.setdefault(obs.parent_source_id, []).append(obs)

        processed_sources: Set[str] = set()
        candidate_scores: Dict[str, float] = {c: 0.0 for c in candidate_ids}

        def get_all_tree_nodes(parent_id: str) -> List[EvidenceObservation]:
            nodes = []
            if parent_id in obs_map:
                nodes.append(obs_map[parent_id])
            children = derived_children_map.get(parent_id, [])
            for child in children:
                nodes.extend(get_all_tree_nodes(child.source_id))
            return nodes

        for source_id, obs in obs_map.items():
            if source_id in processed_sources:
                continue

            # Ledger integrity alone without candidate assignment does not score candidates
            if obs.family == EvidenceFamily.AUDIT_LEDGER and isinstance(obs, LedgerObservation):
                if not obs.primary_candidate and not obs.candidate_scores:
                    processed_sources.add(source_id)
                    continue

            # Case 1: Root of a derivation tree
            if source_id in derived_children_map:
                tree_nodes = get_all_tree_nodes(source_id)
                for node in tree_nodes:
                    processed_sources.add(node.source_id)

                for c in candidate_ids:
                    # Maximum Evidentiary Bound across derivation tree
                    tree_contribs = [
                        node.effective_reliability * node.get_candidate_llr(c)
                        for node in tree_nodes
                    ]
                    max_contrib = max(tree_contribs) if tree_contribs else 0.0
                    candidate_scores[c] += max(0.0, max_contrib)

            # Case 2: Standalone derived node whose parent is not in bundle
            elif obs.dependency_type == DependencyType.DERIVED:
                processed_sources.add(source_id)
                for c in candidate_ids:
                    contrib = obs.effective_reliability * obs.get_candidate_llr(c)
                    candidate_scores[c] += max(0.0, contrib)

            # Case 3: Partially dependent channel (apply policy correlation discount gamma)
            elif obs.dependency_type == DependencyType.PARTIALLY_DEPENDENT:
                processed_sources.add(source_id)
                for c in candidate_ids:
                    contrib = self.correlation_discount * obs.effective_reliability * obs.get_candidate_llr(c)
                    candidate_scores[c] += max(0.0, contrib)

            # Case 4: Fully independent channel
            else:
                processed_sources.add(source_id)
                for c in candidate_ids:
                    contrib = obs.effective_reliability * obs.get_candidate_llr(c)
                    candidate_scores[c] += max(0.0, contrib)

        return candidate_scores
