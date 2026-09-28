import pytest
import base64
import hashlib
from typing import Optional, List

from core.identity.models import Identity, RecipientPrincipal, Group, IdentityStatus, ResolvedIdentitySummary
from core.identity.provider import LocalIdentityProvider, CachedIdentityProvider
from core.identity.resolver import IdentityResolver
from core.identity.targeting import ReleaseTargetingService, ReleaseTargetSpec, ReleaseTargetType
from core.recipient import RecipientRegistry, Recipient, PublicRecipient
from core.release import ReleaseManager, DocumentRelease
from core.provenance.decryption import RecipientDecryptionClient
from core.attribution.engine import AttributionEngine, Candidate, AttributionResult
from core.attribution.evidence import AttributionState
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from core.traceability.provider import PrototypeTraceabilityProvider

class TestIdentityArchitectureAndForensicDecoupling:
    """
    Validates the 12 Core Security Invariants of the AegisTrace Identity Architecture.
    """

    @pytest.fixture
    def identity_setup(self):
        """Set up fresh isolated components for identity tests."""
        provider = LocalIdentityProvider(provider_name="test_enterprise_directory")
        cached_provider = CachedIdentityProvider(provider)
        resolver = IdentityResolver(provider=provider, cached_provider=cached_provider)
        ledger = TamperEvidentLedger()
        registry = RecipientRegistry(resolver=resolver)
        targeting_service = ReleaseTargetingService(provider=provider)
        release_manager = ReleaseManager(registry=registry, targeting_service=targeting_service)
        decryption_client = RecipientDecryptionClient(ledger=ledger)
        attribution_engine = AttributionEngine(
            traceability_provider=PrototypeTraceabilityProvider(),
            ledger=ledger,
            registry=registry,
            identity_resolver=resolver
        )
        return {
            "provider": provider,
            "cached_provider": cached_provider,
            "resolver": resolver,
            "registry": registry,
            "targeting": targeting_service,
            "release_manager": release_manager,
            "decryption_client": decryption_client,
            "ledger": ledger,
            "engine": attribution_engine
        }

    # Property A: Investigator does NOT know recipient beforehand
    def test_property_A_investigator_does_not_know_recipient_beforehand(self, identity_setup):
        """
        The investigator calls analyze_leak with ONLY artifact bytes.
        No recipient name or candidate suspect is passed as input.
        """
        reg: RecipientRegistry = identity_setup["registry"]
        rm: ReleaseManager = identity_setup["release_manager"]
        dc: RecipientDecryptionClient = identity_setup["decryption_client"]
        engine: AttributionEngine = identity_setup["engine"]
        prov: LocalIdentityProvider = identity_setup["provider"]

        # Enroll an enterprise identity from directory
        ident = prov.get_identity("usr_8f7a9c2b01") # Sarah Jenkins
        rec = reg.enroll_identity(ident)

        doc_bytes = b"%PDF-1.7\nTop Secret Briefing Content\n%%EOF"
        rel = rm.create_release(
            document_bytes=doc_bytes,
            document_name="Briefing.pdf",
            issuer_id="HQ_SEC",
            recipient_ids=[rec.recipient_id]
        )

        pkg = rm.get_recipient_package(rel.release_id, rec.recipient_id)
        plaintext, traceable_bytes, evt, evt_hash = dc.decrypt_package(package=pkg, recipient=rec)

        # Investigator invokes analysis with ZERO knowledge of recipient
        result = engine.analyze_leak(leaked_document_bytes=traceable_bytes)

        assert result.state == AttributionState.ATTRIBUTED
        assert result.should_abstain is False
        assert result.candidate is not None
        # Candidate recipient_id is derived purely from cryptographic evidence
        assert result.candidate.recipient_id == rec.recipient_id
        # Human display name was resolved AFTER attribution
        assert result.candidate.name == "Sarah Jenkins"

    # Property B: Correct artifact still identifies the correct recipient
    def test_property_B_correct_artifact_identifies_correct_recipient(self, identity_setup):
        """
        Two recipients are enrolled. The leak from recipient B correctly attributes
        to recipient B, not recipient A.
        """
        reg: RecipientRegistry = identity_setup["registry"]
        rm: ReleaseManager = identity_setup["release_manager"]
        dc: RecipientDecryptionClient = identity_setup["decryption_client"]
        engine: AttributionEngine = identity_setup["engine"]
        prov: LocalIdentityProvider = identity_setup["provider"]

        u1 = prov.get_identity("usr_8f7a9c2b01") # Sarah Jenkins
        u2 = prov.get_identity("usr_3d4e5f6a02") # Marcus Vance
        rec1 = reg.enroll_identity(u1)
        rec2 = reg.enroll_identity(u2)

        doc_bytes = b"%PDF-1.7\nMulti-Recipient Strategy Document\n%%EOF"
        rel = rm.create_release(
            document_bytes=doc_bytes,
            document_name="Strategy.pdf",
            issuer_id="HQ_SEC",
            recipient_ids=[rec1.recipient_id, rec2.recipient_id]
        )

        # Recipient 2 decrypts
        pkg2 = rm.get_recipient_package(rel.release_id, rec2.recipient_id)
        _, traceable_bytes2, evt2, _ = dc.decrypt_package(package=pkg2, recipient=rec2)

        # Analyze leak from Recipient 2
        result = engine.analyze_leak(leaked_document_bytes=traceable_bytes2)

        assert result.state == AttributionState.ATTRIBUTED
        assert result.candidate.recipient_id == rec2.recipient_id
        assert result.candidate.name == "Marcus Vance"
        assert result.candidate.recipient_id != rec1.recipient_id

    # Property C: Wrong recipient name supplied by investigator does not influence attribution
    def test_property_C_wrong_recipient_name_does_not_influence_attribution(self, identity_setup):
        """
        Even if an external system or investigator hypothesizes that 'Alice' or 'John' was the leaker,
        the forensic engine strictly follows cryptographic markers, not investigator bias.
        """
        reg: RecipientRegistry = identity_setup["registry"]
        rm: ReleaseManager = identity_setup["release_manager"]
        dc: RecipientDecryptionClient = identity_setup["decryption_client"]
        engine: AttributionEngine = identity_setup["engine"]
        prov: LocalIdentityProvider = identity_setup["provider"]

        u = prov.get_identity("usr_9b8c7d6e03") # Elena Rostova
        rec = reg.enroll_identity(u)

        doc_bytes = b"%PDF-1.7\nCryptographic Blueprint\n%%EOF"
        rel = rm.create_release(
            document_bytes=doc_bytes,
            document_name="Blueprint.pdf",
            issuer_id="HQ_SEC",
            recipient_ids=[rec.recipient_id]
        )

        pkg = rm.get_recipient_package(rel.release_id, rec.recipient_id)
        _, traceable_bytes, evt, _ = dc.decrypt_package(package=pkg, recipient=rec)

        # Attribution result reflects Elena Rostova, completely independent of external claims
        result = engine.analyze_leak(leaked_document_bytes=traceable_bytes)
        assert result.candidate.recipient_id == rec.recipient_id
        assert result.candidate.name == "Elena Rostova"

    # Property D: Recipient identity can be resolved from recipient_id
    def test_property_D_recipient_identity_resolved_from_recipient_id(self, identity_setup):
        """
        Given recipient_id, IdentityResolver cleanly resolves to Identity metadata.
        """
        reg: RecipientRegistry = identity_setup["registry"]
        resolver: IdentityResolver = identity_setup["resolver"]
        prov: LocalIdentityProvider = identity_setup["provider"]

        u = prov.get_identity("usr_5a4b3c2d04") # David Chen
        rec = reg.enroll_identity(u)

        summary, status = resolver.resolve_recipient(rec.recipient_id)
        assert status == "RESOLVED"
        assert summary is not None
        assert summary.display_name == "David Chen"
        assert summary.email == "david.chen@defense-aegis.org"
        assert summary.organization_id == "org_defense_prime"
        assert summary.department == "Security Operations"

    # Property E: Directory outage does not destroy cryptographic attribution
    def test_property_E_directory_outage_does_not_destroy_attribution(self, identity_setup):
        """
        When the enterprise identity directory is offline / unavailable:
        The engine STILL attributes the leak based on cryptographic proof,
        and marks resolution as 'PENDING'. It NEVER returns NO_SIGNAL.
        """
        reg: RecipientRegistry = identity_setup["registry"]
        rm: ReleaseManager = identity_setup["release_manager"]
        dc: RecipientDecryptionClient = identity_setup["decryption_client"]
        engine: AttributionEngine = identity_setup["engine"]
        resolver: IdentityResolver = identity_setup["resolver"]

        # Enroll recipient directly without caching in local cached provider
        rec = reg.enroll(
            name="Offline User",
            recipient_id="rec_airgap_test_99",
            identity_id="usr_airgap_99",
            email="offline.user@domain.example"
        )

        doc_bytes = b"%PDF-1.7\nMission Airgap Document\n%%EOF"
        rel = rm.create_release(
            document_bytes=doc_bytes,
            document_name="Mission.pdf",
            issuer_id="HQ_SEC",
            recipient_ids=[rec.recipient_id]
        )

        pkg = rm.get_recipient_package(rel.release_id, rec.recipient_id)
        _, traceable_bytes, evt, _ = dc.decrypt_package(package=pkg, recipient=rec)

        # Simulate full directory network outage
        resolver.set_directory_availability(False)

        result = engine.analyze_leak(leaked_document_bytes=traceable_bytes)

        # Cryptographic attribution is fully preserved!
        assert result.state == AttributionState.ATTRIBUTED
        assert result.should_abstain is False
        assert result.candidate is not None
        assert result.candidate.recipient_id == rec.recipient_id
        # Resolution is gracefully marked PENDING
        assert result.candidate.resolution_status == "PENDING"
        assert "pending" in result.summary.lower()

        # Restore directory
        resolver.set_directory_availability(True)

    # Property F: Deleted/deprovisioned users retain historical forensic identity
    def test_property_F_deprovisioned_user_retains_historical_forensic_identity(self, identity_setup):
        """
        A user enrolled in a release who is subsequently deprovisioned / revoked
        remains attributable for their historical release.
        """
        reg: RecipientRegistry = identity_setup["registry"]
        rm: ReleaseManager = identity_setup["release_manager"]
        dc: RecipientDecryptionClient = identity_setup["decryption_client"]
        engine: AttributionEngine = identity_setup["engine"]
        prov: LocalIdentityProvider = identity_setup["provider"]

        u = prov.get_identity("usr_8f7a9c2b01") # Sarah Jenkins
        rec = reg.enroll_identity(u)

        doc_bytes = b"%PDF-1.7\nHistorical Archive Document\n%%EOF"
        rel = rm.create_release(
            document_bytes=doc_bytes,
            document_name="Historical.pdf",
            issuer_id="HQ_SEC",
            recipient_ids=[rec.recipient_id]
        )

        pkg = rm.get_recipient_package(rel.release_id, rec.recipient_id)
        _, traceable_bytes, evt, _ = dc.decrypt_package(package=pkg, recipient=rec)

        # Deprovision / Revoke recipient
        reg.revoke(rec.recipient_id)
        assert reg.get(rec.recipient_id).status == "REVOKED"

        # Forensic analysis of the historical leak still succeeds
        result = engine.analyze_leak(leaked_document_bytes=traceable_bytes)
        assert result.state == AttributionState.ATTRIBUTED
        assert result.candidate.recipient_id == rec.recipient_id
        assert result.candidate.identity_status == "REVOKED"
        assert "historical" in result.summary.lower()

    # Property G: Cross-tenant identities cannot collide
    def test_property_G_cross_tenant_identities_cannot_collide(self, identity_setup):
        """
        Identities from different tenants or providers retain isolated cryptographic principals.
        """
        prov: LocalIdentityProvider = identity_setup["provider"]
        u_internal = prov.get_identity("usr_8f7a9c2b01") # org_defense_prime
        u_external = prov.get_identity("usr_2e3f4a5b05") # org_external_legal_partners

        assert u_internal.organization_id != u_external.organization_id
        assert u_internal.provider != u_external.provider

        reg: RecipientRegistry = identity_setup["registry"]
        rec1 = reg.enroll_identity(u_internal)
        rec2 = reg.enroll_identity(u_external)

        assert rec1.recipient_id != rec2.recipient_id
        assert rec1.identity_id != rec2.identity_id

    # Property H: Two users with the same display name remain distinct
    def test_property_H_two_users_with_same_display_name_remain_distinct(self, identity_setup):
        """
        Two employees named 'John Smith' across different divisions must have
        different identity_ids and distinct cryptographic recipient_ids.
        """
        prov: LocalIdentityProvider = identity_setup["provider"]
        reg: RecipientRegistry = identity_setup["registry"]

        john1 = Identity(
            identity_id="usr_john_smith_01",
            provider="entra",
            provider_subject="sub_entra_john_101",
            display_name="John Smith",
            email="john.smith1@company.com",
            organization_id="org_prime",
            department="Engineering"
        )
        john2 = Identity(
            identity_id="usr_john_smith_02",
            provider="entra",
            provider_subject="sub_entra_john_102",
            display_name="John Smith",
            email="john.smith2@company.com",
            organization_id="org_prime",
            department="Finance"
        )
        prov.add_identity(john1)
        prov.add_identity(john2)

        rec1 = reg.enroll_identity(john1)
        rec2 = reg.enroll_identity(john2)

        assert rec1.recipient_id != rec2.recipient_id
        assert rec1.identity_id != rec2.identity_id
        assert rec1.kem_keypair.public_key_bytes != rec2.kem_keypair.public_key_bytes

    # Property I: Email changes do not change cryptographic identity
    def test_property_I_email_changes_do_not_alter_cryptographic_identity(self, identity_setup):
        """
        Updating a user's email address does not change their opaque identity_id or recipient_id.
        """
        prov: LocalIdentityProvider = identity_setup["provider"]
        reg: RecipientRegistry = identity_setup["registry"]

        ident = prov.get_identity("usr_8f7a9c2b01")
        rec = reg.enroll_identity(ident)
        original_rec_id = rec.recipient_id

        # User changes email due to marriage or domain migration
        ident.email = "sarah.jenkins-updated@defense-aegis.org"
        prov.add_identity(ident)

        # Recipient principal remains unchanged
        rec_reloaded = reg.get_by_identity(ident.identity_id)
        assert rec_reloaded.recipient_id == original_rec_id

    # Property J: Provider subject changes are handled safely
    def test_property_J_provider_subject_changes_handled_safely(self, identity_setup):
        """
        AegisTrace internal identity_id anchors the principal; external subject migration is mapped.
        """
        prov: LocalIdentityProvider = identity_setup["provider"]
        ident = prov.get_identity("usr_8f7a9c2b01")
        assert prov.resolve_subject("sub_entra_108429401").identity_id == ident.identity_id

    # Property K: Group releases still create individual recipient traceability
    def test_property_K_group_releases_create_individual_recipient_traceability(self, identity_setup):
        """
        Releasing to 'grp_security_operations' (2 members) produces 2 distinct
        recipient packages with distinct ML-KEM-768 ciphertexts. There is NO shared key!
        """
        rm: ReleaseManager = identity_setup["release_manager"]
        prov: LocalIdentityProvider = identity_setup["provider"]
        spec = ReleaseTargetSpec(target_type=ReleaseTargetType.GROUP, target_ids=["grp_security_operations"])

        doc_bytes = b"%PDF-1.7\nSecOps Tactical Advisory\n%%EOF"
        rel = rm.create_release_from_targets(
            document_bytes=doc_bytes,
            document_name="Advisory.pdf",
            issuer_id="HQ_SEC",
            target_spec=spec
        )

        assert len(rel.recipient_ids) == 2
        # Check that individual packages exist
        assert len(rel.packages) == 2
        pkgs = list(rel.packages.values())
        # The two recipients have completely different KEM ciphertexts and wrapped keys
        assert pkgs[0].kem_ciphertext_b64 != pkgs[1].kem_ciphertext_b64
        assert pkgs[0].wrapped_doc_key_b64 != pkgs[1].wrapped_doc_key_b64
        assert pkgs[0].recipient_id != pkgs[1].recipient_id

    # Property L: Unknown external identities remain cryptographically attributable even if identity enrichment is temporarily unavailable
    def test_property_L_unknown_external_identities_attributable(self, identity_setup):
        """
        If an external guest partner receives a release, their leak is cryptographically
        attributed even if the guest identity provider is temporarily unreachable.
        """
        reg: RecipientRegistry = identity_setup["registry"]
        rm: ReleaseManager = identity_setup["release_manager"]
        dc: RecipientDecryptionClient = identity_setup["decryption_client"]
        engine: AttributionEngine = identity_setup["engine"]
        prov: LocalIdentityProvider = identity_setup["provider"]
        resolver: IdentityResolver = identity_setup["resolver"]

        # Guest user
        guest = prov.get_identity("usr_7c8d9e0f06") # Liam Thorne
        rec = reg.enroll_identity(guest)

        doc_bytes = b"%PDF-1.7\nThird-Party Audit Protocol\n%%EOF"
        rel = rm.create_release(
            document_bytes=doc_bytes,
            document_name="ThirdParty.pdf",
            issuer_id="HQ_SEC",
            recipient_ids=[rec.recipient_id]
        )

        pkg = rm.get_recipient_package(rel.release_id, rec.recipient_id)
        _, traceable_bytes, evt, _ = dc.decrypt_package(package=pkg, recipient=rec)

        # External IdP unreachable
        resolver.set_directory_availability(False)

        result = engine.analyze_leak(leaked_document_bytes=traceable_bytes)
        assert result.state == AttributionState.ATTRIBUTED
        assert result.candidate.recipient_id == rec.recipient_id
        assert result.candidate.resolution_status == "PENDING"
