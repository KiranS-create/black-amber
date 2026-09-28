import pytest
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState

from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.digital.document_attacks import (
    PdfRewriteAttack,
    PdfMetadataRemovalAttack,
    PdfMetadataModificationAttack,
    PdfObjectReorderingAttack,
    PdfPageExtractionAttack,
    PdfPageDeletionAttack,
    PdfPageDuplicationAttack,
    PdfPageReorderingAttack,
    PdfMergeAttack,
    PdfSplitAttack,
    PdfRasterizationAttack,
    PdfImageReplacementAttack,
    PrintToPdfSimulationAttack,
    PdfCompressionChangesAttack,
    PdfTextExtractionRegenerationAttack,
    PdfScreenshotInsertionAttack,
    PdfDocumentSubstitutionAttack,
)

@pytest.fixture
def document_attack_env():
    registry = RecipientRegistry()
    alice = registry.enroll("Alice", "alice")
    bob = registry.enroll("Bob", "bob")
    charlie = registry.enroll("Charlie", "charlie")

    ledger = TamperEvidentLedger()
    trace_provider = PrototypeTraceabilityProvider()
    release_manager = ReleaseManager(registry=registry)
    decryption_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=trace_provider)
    engine = AttributionEngine(traceability_provider=trace_provider, ledger=ledger, registry=registry)

    sample_doc = BaselineTestCorpus.generate_multipage_pdf()
    release = release_manager.create_release(
        document_bytes=sample_doc,
        document_name="classified_operations.pdf",
        issuer_id="HQ_OPS",
        recipient_ids=["alice", "bob", "charlie"]
    )
    # Bob decrypts legitimately
    bob_pkg = release.packages["bob"]
    _, bob_copy, bob_event, _ = decryption_client.decrypt_package(bob_pkg, bob)

    return {
        "registry": registry,
        "bob": bob,
        "bob_copy": bob_copy,
        "release": release,
        "engine": engine,
        "trace_provider": trace_provider,
    }

def _assert_secure_attribution_or_abstain(res, expected_recipient="bob"):
    """
    Core AegisTrace Security Invariant:
    A transformed artifact must EITHER:
    1. Attribute correctly to the genuine recipient, OR
    2. Explicitly degrade to a fail-closed state (NO_SIGNAL / INSUFFICIENT_EVIDENCE / CONFLICT).
    It must NEVER attribute an innocent recipient.
    """
    if res.state == AttributionState.ATTRIBUTED:
        assert res.candidate is not None
        assert res.candidate.recipient_id == expected_recipient
        assert res.should_abstain is False
    else:
        assert res.should_abstain is True
        assert res.candidate is None
        assert res.state in (AttributionState.NO_SIGNAL, AttributionState.INSUFFICIENT_EVIDENCE, AttributionState.CONFLICT)

def test_doc_metadata_removal_preserves_or_abstains(document_attack_env):
    env = document_attack_env
    attack = PdfMetadataRemovalAttack()
    transformed = attack._execute_transform(env["bob_copy"], {}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_metadata_modification_preserves_or_abstains(document_attack_env):
    env = document_attack_env
    attack = PdfMetadataModificationAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"title": "SPOOFED TITLE"}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_pdf_rewrite_and_reserialization(document_attack_env):
    env = document_attack_env
    attack = PdfRewriteAttack()
    transformed = attack._execute_transform(env["bob_copy"], {}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_object_reordering(document_attack_env):
    env = document_attack_env
    attack = PdfObjectReorderingAttack()
    transformed = attack._execute_transform(env["bob_copy"], {}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_compression_changes(document_attack_env):
    env = document_attack_env
    attack = PdfCompressionChangesAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"compress_streams": True}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_page_extraction_preserves_or_abstains(document_attack_env):
    env = document_attack_env
    attack = PdfPageExtractionAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"page_index": 0}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_page_reordering(document_attack_env):
    env = document_attack_env
    attack = PdfPageReorderingAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"mode": "reverse"}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_page_duplication(document_attack_env):
    env = document_attack_env
    attack = PdfPageDuplicationAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"duplicate_page_index": 0, "count": 2}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_page_deletion(document_attack_env):
    env = document_attack_env
    attack = PdfPageDeletionAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"delete_page_index": 1}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_decoy_merge_prepend(document_attack_env):
    env = document_attack_env
    attack = PdfMergeAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"position": "prepend"}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_split_attack(document_attack_env):
    env = document_attack_env
    attack = PdfSplitAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"split_at": 2}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_rasterization_destroys_marker_and_fails_closed(document_attack_env):
    env = document_attack_env
    attack = PdfRasterizationAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"dpi": 150}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)

    # Flattened raster PDF strips structural trailer marker; must abstain cleanly
    assert res.state == AttributionState.NO_SIGNAL
    assert res.should_abstain is True
    assert res.candidate is None

def test_doc_text_extraction_regeneration_cleansed_fails_closed(document_attack_env):
    env = document_attack_env
    attack = PdfTextExtractionRegenerationAttack()
    transformed = attack._execute_transform(env["bob_copy"], {}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)

    assert res.state == AttributionState.NO_SIGNAL
    assert res.should_abstain is True
    assert res.candidate is None

def test_doc_image_replacement(document_attack_env):
    env = document_attack_env
    attack = PdfImageReplacementAttack()
    transformed = attack._execute_transform(env["bob_copy"], {}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_print_to_pdf_spooler(document_attack_env):
    env = document_attack_env
    attack = PrintToPdfSimulationAttack()
    transformed = attack._execute_transform(env["bob_copy"], {}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_overlay_screenshot_stamp(document_attack_env):
    env = document_attack_env
    attack = PdfScreenshotInsertionAttack()
    transformed = attack._execute_transform(env["bob_copy"], {"stamp_text": "LEAKED COPY"}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)
    _assert_secure_attribution_or_abstain(res, "bob")

def test_doc_unrelated_substitution_fails_closed(document_attack_env):
    env = document_attack_env
    attack = PdfDocumentSubstitutionAttack()
    transformed = attack._execute_transform(env["bob_copy"], {}, seed=42).artifact_bytes
    res = env["engine"].analyze_leak(transformed, expected_release_id=env["release"].release_id)

    assert res.state == AttributionState.NO_SIGNAL
    assert res.should_abstain is True
    assert res.candidate is None
