"""
SIH26237 - Geometric Synchronization & Perspective Rectification Subsystem
Reuses OpenCV's ArUco marker subsystem and projective homography algorithms
to detect, localize, and rectify smartphone camera photos of printed pages.
"""

from typing import Tuple, Optional, Dict, Any, List
import numpy as np
import cv2
from pydantic import BaseModel


class CanonicalCanvasSpec(BaseModel):
    """Geometry specification for canonical document page coordinates."""
    width: int = 800
    height: int = 1000
    margin: int = 40
    marker_size: int = 60
    # Marker IDs in DICT_4X4_50: 0=TL, 1=TR, 2=BR, 3=BL
    marker_ids: List[int] = [0, 1, 2, 3]



class GeometricSynchronizer:
    """
    OpenCV-based geometric synchronizer using 4-corner ArUco fiducials.
    Detects markers under arbitrary rotation, scale, 3D perspective distortion,
    and uneven illumination, rectifying the camera capture back to canonical coordinates.
    """

    def __init__(self, spec: Optional[CanonicalCanvasSpec] = None):
        self.spec = spec or CanonicalCanvasSpec()
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        
        # Configure robust detector parameters
        params = cv2.aruco.DetectorParameters()
        params.adaptiveThreshWinSizeMin = 3
        params.adaptiveThreshWinSizeMax = 35
        params.adaptiveThreshWinSizeStep = 4
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        params.cornerRefinementWinSize = 5
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, params)

        # Precompute canonical marker corner coordinates
        self.canonical_marker_corners = self._compute_canonical_corners()

    def _compute_canonical_corners(self) -> Dict[int, np.ndarray]:
        """Calculates canonical 4-corner coordinates for each marker ID."""
        w, h = self.spec.width, self.spec.height
        m = self.spec.margin
        sz = self.spec.marker_size

        # Coordinates for [TL, TR, BR, BL] of each marker box
        # Marker 0: Top-Left
        m0 = np.float32([
            [m, m],
            [m + sz, m],
            [m + sz, m + sz],
            [m, m + sz]
        ])
        # Marker 1: Top-Right
        m1 = np.float32([
            [w - m - sz, m],
            [w - m, m],
            [w - m, m + sz],
            [w - m - sz, m + sz]
        ])
        # Marker 2: Bottom-Right
        m2 = np.float32([
            [w - m - sz, h - m - sz],
            [w - m, h - m - sz],
            [w - m, h - m],
            [w - m - sz, h - m]
        ])
        # Marker 3: Bottom-Left
        m3 = np.float32([
            [m, h - m - sz],
            [m + sz, h - m - sz],
            [m + sz, h - m],
            [m, h - m]
        ])

        return {0: m0, 1: m1, 2: m2, 3: m3}

    def embed_fiducial_anchors(self, canvas: np.ndarray) -> np.ndarray:
        """
        Draws the 4 canonical corner fiducials and subtle alignment frames
        onto the document canvas.
        """
        output = canvas.copy()
        if len(output.shape) == 2:
            output = cv2.cvtColor(output, cv2.COLOR_GRAY2BGR)

        m = self.spec.margin
        sz = self.spec.marker_size
        w, h = self.spec.width, self.spec.height

        # Generate each marker image
        for marker_id in self.spec.marker_ids:
            marker_img = cv2.aruco.generateImageMarker(self.dictionary, marker_id, sz)
            marker_bgr = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)

            if marker_id == 0:    # Top-Left
                output[m:m + sz, m:m + sz] = marker_bgr
            elif marker_id == 1:  # Top-Right
                output[m:m + sz, w - m - sz:w - m] = marker_bgr
            elif marker_id == 2:  # Bottom-Right
                output[h - m - sz:h - m, w - m - sz:w - m] = marker_bgr
            elif marker_id == 3:  # Bottom-Left
                output[h - m - sz:h - m, m:m + sz] = marker_bgr

        # Subtle alignment border connecting the markers (respecting quiet zone)
        color = (200, 200, 200)
        gap = 8
        # Top line between TL and TR
        cv2.line(output, (m + sz + gap, m + sz // 2), (w - m - sz - gap, m + sz // 2), color, 1)
        # Right line between TR and BR
        cv2.line(output, (w - m - sz // 2, m + sz + gap), (w - m - sz // 2, h - m - sz - gap), color, 1)
        # Bottom line between BR and BL
        cv2.line(output, (w - m - sz - gap, h - m - sz // 2), (m + sz + gap, h - m - sz // 2), color, 1)
        # Left line between BL and TL
        cv2.line(output, (m + sz // 2, h - m - sz - gap), (m + sz // 2, m + sz + gap), color, 1)

        return output


    def detect_and_rectify(
        self,
        image: np.ndarray
    ) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        """
        Detects corner fiducials in the captured image, estimates the projective
        homography matrix H via RANSAC, and warps the image back to canonical dimensions.

        Returns:
          (success: bool, rectified_canvas: Optional[np.ndarray], telemetry: Dict[str, Any])
        """
        telemetry: Dict[str, Any] = {
            "sync_success": False,
            "detected_markers": [],
            "reprojection_error": 0.0,
            "homography_matrix": None
        }

        # Convert to grayscale for detection if color
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Detect markers
        corners, ids, rejected = self.detector.detectMarkers(gray)

        if ids is None or len(ids) == 0:
            telemetry["reason"] = "no_fiducial_markers_found"
            return False, None, telemetry

        flat_ids = ids.flatten().tolist()
        telemetry["detected_markers"] = flat_ids

        # We require at least 3 markers to have 12 point correspondences (>= 4 required for homography)
        valid_markers = [mid for mid in self.spec.marker_ids if mid in flat_ids]
        if len(valid_markers) < 3:
            telemetry["reason"] = f"insufficient_markers_detected ({len(valid_markers)} < 3)"
            return False, None, telemetry

        src_points = []
        dst_points = []

        for mid in valid_markers:
            idx = flat_ids.index(mid)
            marker_corners = corners[idx][0]  # Shape (4, 2)
            canon_corners = self.canonical_marker_corners[mid]  # Shape (4, 2)

            for pt_idx in range(4):
                src_points.append(marker_corners[pt_idx])
                dst_points.append(canon_corners[pt_idx])

        src_pts_arr = np.float32(src_points)
        dst_pts_arr = np.float32(dst_points)

        # Compute Homography matrix
        H, inliers = cv2.findHomography(src_pts_arr, dst_pts_arr, cv2.RANSAC, 5.0)
        if H is None:
            telemetry["reason"] = "homography_estimation_failed"
            return False, None, telemetry

        # Reprojection error
        projected = cv2.perspectiveTransform(src_pts_arr.reshape(-1, 1, 2), H).reshape(-1, 2)
        errors = np.linalg.norm(projected - dst_pts_arr, axis=1)
        mean_err = float(np.mean(errors))
        telemetry["reprojection_error"] = mean_err
        telemetry["homography_matrix"] = H.tolist()

        # Warp captured photo back to canonical dimensions
        w, h = self.spec.width, self.spec.height
        rectified = cv2.warpPerspective(
            image,
            H,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255) if len(image.shape) == 3 else 255
        )

        telemetry["sync_success"] = True
        return True, rectified, telemetry
