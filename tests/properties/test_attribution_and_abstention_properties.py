import pytest
import hashlib
from typing import List, Dict, Any, Optional

from core.testing.property_engine import (
    PropertyRunner,
    DeterministicGenerator,
)
from core.security.invariants import assert_invariant
from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceObservation,
    WatermarkObservation,
    ProvenanceObservation,
    EvidenceFamily,
    DependencyType,
    EvidenceConfidenceLevel,
    TargetBinding,
    AttributionState,
)
from core.attribution.fusion import EvidenceFusionEngine, FusedAttributionResult
from core.attribution.dependency import EvidenceDependencyGraph
from core.attribution.policy import DecisionPolicy
from core.attribution.engine import AttributionEngine, AttributionResult
from core.identity.resolver import IdentityResolver


def test_property_invariant_007_insufficient_evidence_mandatory_abstention(runner: PropertyRunner):
    """
    INVARIANT-007: Insufficient Evidence Mandatory Abstention.
    When evidence is absent, weak, uncorroborated, conflicting, or mismatched,
    the attribution system MUST abstain (should_abstain == True, state != ATTRIBUTED).
    """
    engine = EvidenceFusionEngine()

    def prop(g: DeterministicGenerator):
        scenario = g.choice([
            "empty_bundle",
            "all_invalid_signals",
            "weak_non_crypto_only",
            "competing_conflict",
            "mismatched_target_binding",
        ])

        doc_id = g.generate_document_id()
        rel_id = f"REL-{g.alphanumeric(6, 8)}"
        target_bind = TargetBinding(document_id=doc_id, release_id=rel_id)
        bundle = EvidenceBundle(bundle_id=f"BNDL-{g.alphanumeric(6, 8)}", target_binding=target_bind)

        c1 = g.generate_recipient_id(1)
        c2 = g.generate_recipient_id(2)

        if scenario == "empty_bundle":
            pass  # Bundle has 0 observations

        elif scenario == "all_invalid_signals":
            num_obs = g.integer(1, 5)
            for i in range(num_obs):
                bundle.add_observation(WatermarkObservation(
                    source_id=f"wm_corrupt_{i}",
                    primary_candidate=c1,
                    log_likelihood_ratio=g.float_val(5.0, 15.0),
                    is_valid=False,
                    target_binding=target_bind,
                ))

        elif scenario == "weak_non_crypto_only":
            # Document structure without any primary cryptographic marker
            bundle.add_observation(EvidenceObservation(
                source_id="struct_1",
                family=EvidenceFamily.DOCUMENT_STRUCTURE,
                primary_candidate=c1,
                log_likelihood_ratio=g.float_val(0.5, 3.0),
                is_valid=True,
                target_binding=target_bind,
            ))

        elif scenario == "competing_conflict":
            # Two strong primary cryptographic signals pointing to different candidates
            llr = g.float_val(8.0, 14.0)
            bundle.add_observation(WatermarkObservation(
                source_id="wm_c1",
                primary_candidate=c1,
                log_likelihood_ratio=llr,
                is_valid=True,
                target_binding=target_bind,
            ))
            bundle.add_observation(WatermarkObservation(
                source_id="wm_c2",
                primary_candidate=c2,
                log_likelihood_ratio=llr + g.float_val(-0.5, 0.5),  # very narrow margin
                is_valid=True,
                target_binding=target_bind,
            ))

        elif scenario == "mismatched_target_binding":
            # Observation belongs to a completely different document
            alien_doc = g.generate_document_id()
            bundle.add_observation(WatermarkObservation(
                source_id="wm_alien",
                primary_candidate=c1,
                log_likelihood_ratio=15.0,
                is_valid=True,
                target_binding=TargetBinding(document_id=alien_doc, release_id=rel_id),
            ))

        # Run multi-channel Bayesian fusion
        result = engine.fuse(bundle)

        # Invariant Assertion
        assert_invariant(
            result.should_abstain is True,
            "INVARIANT-007",
            f"Attribution engine failed to abstain under scenario '{scenario}'",
            g.seed,
            counterexample={"scenario": scenario, "state": str(result.state), "score": result.fused_score},
        )
        assert_invariant(
            result.state != AttributionState.ATTRIBUTED,
            "INVARIANT-007",
            f"Attribution state was forced to ATTRIBUTED under scenario '{scenario}'",
            g.seed,
            counterexample={"scenario": scenario, "state": str(result.state)},
        )

    res = runner.run_property("insufficient_evidence_mandatory_abstention", prop, iterations=250)
    assert res.passed, res.error_message


def test_property_attribution_monotonicity(runner: PropertyRunner):
    """
    Forensic Monotonicity:
    1. Adding evidence supporting candidate B must never increase candidate A's score.
    2. Removing evidence supporting candidate A must never increase candidate A's score.
    3. Adding corrupted/invalid evidence must never increase any candidate's score.
    """
    engine = EvidenceFusionEngine()

    def prop(g: DeterministicGenerator):
        doc_id = g.generate_document_id()
        rel_id = f"REL-{g.alphanumeric(6, 8)}"
        target_bind = TargetBinding(document_id=doc_id, release_id=rel_id)

        target_candidate = g.generate_recipient_id(1)
        other_candidate = g.generate_recipient_id(2)

        # Baseline: Authentic observation for target_candidate
        base_llr = g.float_val(6.0, 12.0)
        base_obs = WatermarkObservation(
            source_id="wm_base_target",
            primary_candidate=target_candidate,
            log_likelihood_ratio=base_llr,
            is_valid=True,
            target_binding=target_bind,
        )

        b_base = EvidenceBundle(bundle_id="b_base", target_binding=target_bind)
        b_base.add_observation(base_obs)
        res_base = engine.fuse(b_base)
        score_base = res_base.fused_score

        # Monotonicity Test 1: Add unrelated evidence for other_candidate
        b_with_unrelated = EvidenceBundle(bundle_id="b_unrelated", target_binding=target_bind)
        b_with_unrelated.add_observation(base_obs)
        b_with_unrelated.add_observation(EvidenceObservation(
            source_id="struct_other",
            family=EvidenceFamily.DOCUMENT_STRUCTURE,
            primary_candidate=other_candidate,
            log_likelihood_ratio=g.float_val(1.0, 4.0),
            is_valid=True,
            target_binding=target_bind,
        ))
        res_unrelated = engine.fuse(b_with_unrelated)
        target_eval = next((e for e in res_unrelated.candidate_evaluations if e.candidate_id == target_candidate), None)
        score_target_after_unrelated = target_eval.fused_score if target_eval else 0.0

        assert_invariant(
            score_target_after_unrelated <= score_base + 1e-6,
            "INVARIANT-007",
            f"Score of target candidate increased after adding evidence for another candidate",
            g.seed,
            counterexample={
                "before": score_base,
                "after": score_target_after_unrelated,
            },
        )

        # Monotonicity Test 2: Add additional valid supporting evidence for target_candidate
        # Score must be non-decreasing
        b_strengthened = EvidenceBundle(bundle_id="b_strong", target_binding=target_bind)
        b_strengthened.add_observation(base_obs)
        b_strengthened.add_observation(ProvenanceObservation(
            source_id="pqc_target",
            signer_recipient_id=target_candidate,
            signature_valid=True,
            log_likelihood_ratio=g.float_val(4.0, 8.0),
            primary_candidate=target_candidate,
            is_valid=True,
            target_binding=target_bind,
        ))
        res_strengthened = engine.fuse(b_strengthened)
        assert_invariant(
            res_strengthened.fused_score >= score_base - 1e-6,
            "INVARIANT-007",
            "Score decreased after adding independent supporting evidence",
            g.seed,
            counterexample={
                "before": score_base,
                "after": res_strengthened.fused_score,
            },
        )

        # Monotonicity Test 3: Add invalid/corrupted evidence for target_candidate
        # Score must not increase
        b_corrupted = EvidenceBundle(bundle_id="b_corrupt", target_binding=target_bind)
        b_corrupted.add_observation(base_obs)
        b_corrupted.add_observation(WatermarkObservation(
            source_id="wm_corrupt_target",
            primary_candidate=target_candidate,
            log_likelihood_ratio=g.float_val(10.0, 20.0),
            is_valid=False,  # Explicitly invalid
            target_binding=target_bind,
        ))
        res_corrupted = engine.fuse(b_corrupted)
        assert_invariant(
            res_corrupted.fused_score <= score_base + 1e-6,
            "INVARIANT-007",
            "Score increased after adding invalid/corrupted evidence",
            g.seed,
            counterexample={
                "before": score_base,
                "after": res_corrupted.fused_score,
            },
        )

    res = runner.run_property("attribution_monotonicity", prop, iterations=200)
    assert res.passed, res.error_message


def test_property_anti_double_counting_invariant(runner: PropertyRunner):
    """
    Anti-Double-Counting Invariant:
    1. Replaying the identical observation or identical signal payload fingerprint
       must NOT increase the candidate's fused score.
    2. Adding DERIVED signals in a derivation tree must be bounded by the maximum
       evidentiary contribution in that tree, NOT additive accumulation.
    """
    dep_graph = EvidenceDependencyGraph()

    def prop(g: DeterministicGenerator):
        doc_id = g.generate_document_id()
        rel_id = f"REL-{g.alphanumeric(6, 8)}"
        target_bind = TargetBinding(document_id=doc_id, release_id=rel_id)
        candidate = g.generate_recipient_id(1)

        parent_llr = g.float_val(5.0, 10.0)
        parent_obs = WatermarkObservation(
            source_id="parent_wm",
            primary_candidate=candidate,
            log_likelihood_ratio=parent_llr,
            is_valid=True,
            target_binding=target_bind,
        )

        # Baseline: single observation
        b_base = EvidenceBundle(bundle_id="b_base", target_binding=target_bind)
        b_base.add_observation(parent_obs)
        scores_base = dep_graph.compute_fused_candidate_scores(b_base)
        base_score = scores_base.get(candidate, 0.0)

        # Test A: Adversarial Replay / Duplication
        # Add 1 to 5 duplicate copies of the same observation
        b_dup = EvidenceBundle(bundle_id="b_dup", target_binding=target_bind)
        b_dup.add_observation(parent_obs)
        num_dups = g.integer(1, 5)
        for i in range(num_dups):
            # Same source_id or same payload
            dup_obs = WatermarkObservation(
                source_id=f"parent_wm",  # identical ID
                primary_candidate=candidate,
                log_likelihood_ratio=parent_llr,
                is_valid=True,
                target_binding=target_bind,
            )
            b_dup.add_observation(dup_obs)

        scores_dup = dep_graph.compute_fused_candidate_scores(b_dup)
        dup_score = scores_dup.get(candidate, 0.0)

        assert_invariant(
            abs(dup_score - base_score) < 1e-6,
            "INVARIANT-007",
            f"Adversarial replay caused double-counting (base={base_score}, dup={dup_score})",
            g.seed,
            counterexample={"base_score": base_score, "dup_score": dup_score, "num_dups": num_dups},
        )

        # Test B: Derived Tree Bounded Contribution
        # Add child observations derived from parent_wm with smaller LLRs
        b_derived = EvidenceBundle(bundle_id="b_derived", target_binding=target_bind)
        b_derived.add_observation(parent_obs)
        num_children = g.integer(1, 4)
        for i in range(num_children):
            child_llr = g.float_val(1.0, parent_llr * 0.8)  # strictly less than parent
            child_obs = EvidenceObservation(
                source_id=f"derived_child_{i}",
                family=EvidenceFamily.TARDOS_FINGERPRINT,
                dependency_type=DependencyType.DERIVED,
                parent_source_id="parent_wm",
                primary_candidate=candidate,
                log_likelihood_ratio=child_llr,
                is_valid=True,
                target_binding=target_bind,
            )
            b_derived.add_observation(child_obs)

        scores_derived = dep_graph.compute_fused_candidate_scores(b_derived)
        derived_score = scores_derived.get(candidate, 0.0)

        # Because child LLRs are less than parent LLR, the tree maximum is the parent LLR
        assert_invariant(
            abs(derived_score - base_score) < 1e-6,
            "INVARIANT-007",
            f"Derived tree improperly accumulated additively (base={base_score}, derived={derived_score})",
            g.seed,
            counterexample={"base_score": base_score, "derived_score": derived_score, "num_children": num_children},
        )

    res = runner.run_property("anti_double_counting_invariant", prop, iterations=200)
    assert res.passed, res.error_message


from core.identity.models import ResolvedIdentitySummary, Identity, IdentityStatus
from core.identity.resolver import IdentityResolver
from core.identity.provider import LocalIdentityProvider


def test_property_directory_outage_fail_closed_attribution(runner: PropertyRunner):
    """
    Fail-Closed Directory Resolution Invariant:
    When IdP/LDAP/directory services encounter offline outages, missing records,
    or deprovisioned users, the IdentityResolver MUST fail-closed:
    - Never crash or raise unhandled exceptions.
    - Opaque cryptographic recipient_id resolution cleanly handles PENDING or NOT_FOUND.
    - Deprovisioned/revoked identities retain historical forensic auditability.
    """
    def prop(g: DeterministicGenerator):
        mode = g.choice(["offline_outage", "missing_user", "deprovisioned", "cached_offline"])
        local_provider = LocalIdentityProvider()
        resolver = IdentityResolver(provider=local_provider)

        rec_id = g.generate_recipient_id()
        ident_id = f"usr_{g.alphanumeric(8, 10).lower()}"

        if mode == "offline_outage":
            # Unbound or bound recipient when directory is completely offline
            resolver.set_directory_availability(False)
            summary, status = resolver.resolve_recipient(rec_id)
            assert_invariant(
                status in ("PENDING", "NOT_FOUND"),
                "INVARIANT-007",
                f"Directory offline outage did not return PENDING/NOT_FOUND: got {status}",
                g.seed,
            )

        elif mode == "missing_user":
            # Recipient not in directory at all
            resolver.set_directory_availability(True)
            summary, status = resolver.resolve_recipient(f"rec-missing-{g.alphanumeric(6, 8)}")
            assert_invariant(
                status == "NOT_FOUND" and summary is None,
                "INVARIANT-007",
                f"Missing user did not return NOT_FOUND (got {status})",
                g.seed,
            )

        elif mode == "deprovisioned":
            # Identity exists but is marked DEPROVISIONED / REVOKED
            dep_ident = Identity(
                identity_id=ident_id,
                provider="local_directory",
                provider_subject=f"sub_{ident_id}",
                display_name=f"Former Staff {g.alphanumeric(4, 6)}",
                email=f"former.{ident_id}@corp.internal",
                organization_id="org-acme",
                status=IdentityStatus.DEPROVISIONED,
            )
            local_provider.add_identity(dep_ident)
            resolver.bind_recipient_identity(rec_id, ident_id)
            resolver.set_directory_availability(True)

            summary, status = resolver.resolve_recipient(rec_id)
            assert_invariant(
                summary is not None and summary.status == "DEPROVISIONED",
                "INVARIANT-007",
                f"Deprovisioned identity failed to report DEPROVISIONED status (got {getattr(summary, 'status', None)})",
                g.seed,
            )

        elif mode == "cached_offline":
            # Identity was resolved once while online, then directory goes offline
            active_ident = Identity(
                identity_id=ident_id,
                provider="local_directory",
                provider_subject=f"sub_{ident_id}",
                display_name=f"Alice {g.alphanumeric(4, 6)}",
                email=f"alice.{ident_id}@corp.internal",
                organization_id="org-acme",
                status=IdentityStatus.ACTIVE,
            )
            local_provider.add_identity(active_ident)
            resolver.bind_recipient_identity(rec_id, ident_id)
            
            # 1. Warm cache while online
            resolver.set_directory_availability(True)
            sum1, st1 = resolver.resolve_recipient(rec_id)
            assert st1 == "RESOLVED"

            # 2. Simulate IdP outage
            resolver.set_directory_availability(False)
            sum2, st2 = resolver.resolve_recipient(rec_id)
            assert_invariant(
                st2 == "CACHED" and sum2 is not None and sum2.identity_id == ident_id,
                "INVARIANT-007",
                f"Cached offline resolution failed (got {st2})",
                g.seed,
            )

    res = runner.run_property("directory_outage_fail_closed_attribution", prop, iterations=150)
    assert res.passed, res.error_message
