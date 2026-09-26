import io
import pytest
from pypdf import PdfReader
from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.digital.document_attacks import (
    PdfMetadataRemovalAttack,
    PdfMetadataModificationAttack,
    PdfRewriteAttack,
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
def text_pdf_bytes():
    return BaselineTestCorpus.generate_simple_text_pdf()

@pytest.fixture
def multipage_pdf_bytes():
    return BaselineTestCorpus.generate_multipage_pdf()

@pytest.fixture
def image_pdf_bytes():
    return BaselineTestCorpus.generate_image_containing_pdf()

def test_all_17_pdf_attacks_execute_successfully(text_pdf_bytes, multipage_pdf_bytes, image_pdf_bytes):
    attacks = [
        (PdfMetadataRemovalAttack(), text_pdf_bytes, {}),
        (PdfMetadataModificationAttack(), text_pdf_bytes, {"title": "ADVERSARIAL LEAK"}),
        (PdfRewriteAttack(), text_pdf_bytes, {}),
        (PdfObjectReorderingAttack(), multipage_pdf_bytes, {}),
        (PdfPageExtractionAttack(), multipage_pdf_bytes, {"page_index": 1}),
        (PdfPageDeletionAttack(), multipage_pdf_bytes, {"delete_page_index": 0}),
        (PdfPageDuplicationAttack(), multipage_pdf_bytes, {"duplicate_page_index": 0}),
        (PdfPageReorderingAttack(), multipage_pdf_bytes, {"mode": "reverse"}),
        (PdfMergeAttack(), text_pdf_bytes, {"position": "append"}),
        (PdfSplitAttack(), multipage_pdf_bytes, {"split_at": 1}),
        (PdfRasterizationAttack(), text_pdf_bytes, {"dpi": 150}),
        (PdfImageReplacementAttack(), image_pdf_bytes, {}),
        (PrintToPdfSimulationAttack(), text_pdf_bytes, {"virtual_driver": "CUPS-PDF"}),
        (PdfCompressionChangesAttack(), text_pdf_bytes, {"compress_streams": True}),
        (PdfTextExtractionRegenerationAttack(), text_pdf_bytes, {}),
        (PdfScreenshotInsertionAttack(), text_pdf_bytes, {"stamp_text": "LEAKED DECLASSIFIED"}),
        (PdfDocumentSubstitutionAttack(), text_pdf_bytes, {"decoy_title": "BUDGET OVERVIEW"}),
    ]

    assert len(attacks) == 17

    for attack, target_bytes, params in attacks:
        result = attack.apply(target_bytes, parameters=params, seed=42)
        assert result.success is True, f"PDF Attack {attack.ATTACK_NAME} failed: {result.observed_effect}"
        assert result.output_hash != ""
        assert result.output_type == "DOCUMENT_PDF"
        assert result.input_hash != ""
        
        # Verify transformed bytes are valid readable PDF
        out_obj = attack._execute_transform(target_bytes, params, seed=42)
        out_reader = PdfReader(io.BytesIO(out_obj.artifact_bytes))
        assert len(out_reader.pages) >= 1

def test_pdf_page_surgery_counts(multipage_pdf_bytes):
    orig_reader = PdfReader(io.BytesIO(multipage_pdf_bytes))
    assert len(orig_reader.pages) == 3

    # Extraction of 1 page
    ext_attack = PdfPageExtractionAttack()
    out_obj = ext_attack._execute_transform(multipage_pdf_bytes, {"page_index": 0}, seed=None)
    ext_reader = PdfReader(io.BytesIO(out_obj.artifact_bytes))
    assert len(ext_reader.pages) == 1

    # Deletion of 1 page -> 2 pages
    del_attack = PdfPageDeletionAttack()
    out_del = del_attack._execute_transform(multipage_pdf_bytes, {"delete_page_index": 0}, seed=None)
    del_reader = PdfReader(io.BytesIO(out_del.artifact_bytes))
    assert len(del_reader.pages) == 2

    # Duplication of 1 page -> 4 pages
    dup_attack = PdfPageDuplicationAttack()
    out_dup = dup_attack._execute_transform(multipage_pdf_bytes, {"duplicate_page_index": 0, "count": 1}, seed=None)
    dup_reader = PdfReader(io.BytesIO(out_dup.artifact_bytes))
    assert len(dup_reader.pages) == 4

def test_pdf_text_extraction_regeneration_cleanses_trailer(text_pdf_bytes):
    from core.traceability.provider import PrototypeTraceabilityProvider
    provider = PrototypeTraceabilityProvider()
    marker = provider.issue_marker("d1", "r1", "alice", "h1")
    marked_doc = provider.embed_marker(text_pdf_bytes, marker)
    assert provider.extract_marker(marked_doc) is not None

    # Text extraction and regeneration should destroy the structural marker
    regen_attack = PdfTextExtractionRegenerationAttack()
    out = regen_attack._execute_transform(marked_doc, {}, seed=None)
    assert provider.extract_marker(out.artifact_bytes) is None
