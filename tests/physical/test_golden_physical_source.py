"""
SIH26237 - Test Golden Physical Source Canvas Generation
"""

import pytest
import numpy as np
from core.physical.golden_source import GoldenPhysicalSourceBuilder, GoldenPhysicalSource


def test_golden_source_dimensions_and_type():
    """Verify golden source generates an exact 800x1000 3-channel RGB image."""
    golden = GoldenPhysicalSourceBuilder.generate_canvas(doc_id="DOC_PHYS_001")
    assert isinstance(golden, GoldenPhysicalSource)
    assert golden.image.shape == (1000, 800, 3)
    assert golden.image.dtype == np.uint8
    assert len(golden.content_hash) == 64


def test_golden_source_deterministic_hash():
    """Verify canvas generation is deterministic for identical doc_id and timestamp."""
    g1 = GoldenPhysicalSourceBuilder.generate_canvas(
        doc_id="DOC_PHYS_FIXED",
        created_at="2026-09-28T00:00:00Z"
    )
    g2 = GoldenPhysicalSourceBuilder.generate_canvas(
        doc_id="DOC_PHYS_FIXED",
        created_at="2026-09-28T00:00:00Z"
    )
    assert g1.content_hash == g2.content_hash
    assert np.array_equal(g1.image, g2.image)


def test_golden_source_verification():
    """Verify built-in integrity check."""
    golden = GoldenPhysicalSourceBuilder.generate_canvas(doc_id="DOC_VERIFY")
    assert golden.verify_integrity() is True

    # Corrupt pixel
    corrupted_img = golden.image.copy()
    corrupted_img[100, 100, 0] = (corrupted_img[100, 100, 0] + 50) % 256
    corrupted_golden = GoldenPhysicalSource(
        document_id=golden.document_id,
        classification=golden.classification,
        content_hash=golden.content_hash,
        image=corrupted_img,
        created_at=golden.created_at
    )
    assert corrupted_golden.verify_integrity() is False
