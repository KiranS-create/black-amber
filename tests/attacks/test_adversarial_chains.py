import pytest
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState

from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.digital.transformation_chains import (
    create_chain_document_raster_jpeg_crop,
    create_chain_image_screenshot_noise_compression,
    create_chain_multipage_reorder_extract_merge,
)

@pytest.fixture
def chain_env():
    registry = RecipientRegistry()
    alice = registry.enroll("Alice", "alice")
    bob = registry.enroll("Bob", "bob")

    ledger = TamperEvidentLedger()
    trace_provider = PrototypeTraceabilityProvider()
    release_manager = ReleaseManager(registry=registry)
    decryption_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=trace_provider)
    engine = AttributionEngine(traceability_provider=trace_provider, ledger=ledger, registry=registry)

    sample_doc = BaselineTestCorpus.generate_multipage_pdf()
    release = release_manager.create_release(
        document_bytes=sample_doc,
        document_name="chain_test.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob"]
    )
    bob_pkg = release.packages["bob"]
    _, bob_copy, bob_event, _ = decryption_client.decrypt_package(bob_pkg, bob)
    high_res_page = BaselineTestCorpus.generate_high_res_page_image()

    return {
        "bob_copy": bob_copy,
        "high_res_page": high_res_page,
        "release": release,
        "engine": engine,
    }

def test_chain_document_raster_jpeg_crop_fails_closed(chain_env):
    env = chain_env
    chain = create_chain_document_raster_jpeg_crop()
    res = chain.execute(env["bob_copy"], seed=42)

    assert res.success is True
    assert res.total_steps == 4
    assert res.final_hash != res.initial_hash

    # Analyze leak of final transformed artifact
    attr_res = env["engine"].analyze_leak(res.final_artifact_bytes, expected_release_id=env["release"].release_id)
    # Rasterization removes structural marker -> must fail-closed cleanly as NO_SIGNAL
    assert attr_res.state == AttributionState.NO_SIGNAL
    assert attr_res.should_abstain is True
    assert attr_res.candidate is None

def test_chain_image_screenshot_noise_compression(chain_env):
    env = chain_env
    chain = create_chain_image_screenshot_noise_compression()
    res = chain.execute(env["high_res_page"], seed=42)

    assert res.success is True
    assert res.total_steps == 5
    assert len(res.final_artifact_bytes) > 0

def test_chain_multipage_reorder_extract_merge(chain_env):
    env = chain_env
    chain = create_chain_multipage_reorder_extract_merge()
    res = chain.execute(env["bob_copy"], seed=42)

    assert res.success is True
    assert res.total_steps == 4

    attr_res = env["engine"].analyze_leak(res.final_artifact_bytes, expected_release_id=env["release"].release_id)
    # Either attributed to Bob or abstained, NEVER false attribution
    if attr_res.state == AttributionState.ATTRIBUTED:
        assert attr_res.candidate.recipient_id == "bob"
    else:
        assert attr_res.should_abstain is True
