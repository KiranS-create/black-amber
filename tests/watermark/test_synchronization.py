"""
SIH26237 - Geometric Synchronization & Perspective Tests
Verifies ArUco fiducial detection, projective homography estimation,
multi-angle rotation recovery, scaling, and fail-closed marker loss behavior.
"""

import pytest
import numpy as np
import cv2

from core.watermark.sync import GeometricSynchronizer, CanonicalCanvasSpec


@pytest.fixture
def spec():
    return CanonicalCanvasSpec(width=800, height=1000, margin=40, marker_size=60)


@pytest.fixture
def synchronizer(spec):
    return GeometricSynchronizer(spec)


@pytest.fixture
def marked_canvas(synchronizer, spec):
    canvas = np.ones((spec.height, spec.width, 3), dtype=np.uint8) * 255
    cv2.putText(canvas, "TEST SYNCHRONIZATION DOCUMENT", (150, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 40, 40), 2)
    return synchronizer.embed_fiducial_anchors(canvas)


def test_clean_synchronization(synchronizer, marked_canvas, spec):
    """Verifies that un-distorted canvas rectifies with near-zero reprojection error."""
    ok, rectified, tele = synchronizer.detect_and_rectify(marked_canvas)
    assert ok is True
    assert rectified is not None
    assert rectified.shape == (spec.height, spec.width, 3)
    assert tele["reprojection_error"] < 0.20
    assert len(tele["detected_markers"]) == 4


@pytest.mark.parametrize("rotation_flag, expected_angle", [
    (cv2.ROTATE_90_CLOCKWISE, "90 CW"),
    (cv2.ROTATE_180, "180"),
    (cv2.ROTATE_90_COUNTERCLOCKWISE, "270 CW"),
])
def test_cardinal_rotations(synchronizer, marked_canvas, spec, rotation_flag, expected_angle):
    """Verifies that 90, 180, and 270 degree camera rotations are automatically rectified."""
    rotated = cv2.rotate(marked_canvas, rotation_flag)
    ok, rectified, tele = synchronizer.detect_and_rectify(rotated)

    assert ok is True, f"Failed rotation for {expected_angle}"
    assert rectified is not None
    assert rectified.shape == (spec.height, spec.width, 3)
    assert tele["reprojection_error"] < 0.35


def test_perspective_homography_warp(synchronizer, marked_canvas, spec):
    """Verifies recovery under non-trivial trapezoidal smartphone perspective skew."""
    w, h = spec.width, spec.height
    pts1 = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    # Simulate off-axis camera pitch and yaw
    pts2 = np.float32([[50, 70], [w - 60, 30], [w - 20, h - 50], [30, h - 80]])
    M = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(marked_canvas, M, (w + 40, h + 40))

    ok, rectified, tele = synchronizer.detect_and_rectify(warped)
    assert ok is True
    assert rectified.shape == (h, w, 3)
    assert tele["reprojection_error"] < 0.50


def test_partial_marker_occlusion_tolerance(synchronizer, marked_canvas, spec):
    """
    Verifies that when 1 marker is occluded/erased (3 remaining),
    the synchronizer still recovers homography from the 12 remaining point correspondences.
    """
    damaged = marked_canvas.copy()
    # Occlude Marker 2 (Bottom-Right) with white rectangle
    m, sz = spec.margin, spec.marker_size
    damaged[spec.height - m - sz:spec.height - m, spec.width - m - sz:spec.width - m] = 255

    ok, rectified, tele = synchronizer.detect_and_rectify(damaged)
    assert ok is True
    assert len(tele["detected_markers"]) == 3
    assert rectified is not None


def test_excessive_marker_loss_fails_closed(synchronizer, marked_canvas, spec):
    """
    Verifies that when 2 or more markers are destroyed (leaving <3 markers),
    the synchronizer fails closed and does not guess a false homography.
    """
    damaged = marked_canvas.copy()
    m, sz = spec.margin, spec.marker_size
    # Erase Marker 0 (TL) and Marker 2 (BR)
    damaged[m:m + sz, m:m + sz] = 255
    damaged[spec.height - m - sz:spec.height - m, spec.width - m - sz:spec.width - m] = 255

    ok, rectified, tele = synchronizer.detect_and_rectify(damaged)
    assert ok is False
    assert rectified is None
    assert "insufficient_markers" in tele.get("reason", "")
