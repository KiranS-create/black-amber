"""
SIH26237 - Visual Debug Artifact Generator
Generates visual diagnostic artifacts for physical and simulated watermark validation:
1. Original watermarked canvas
2. Simulated/Physical camera capture with lighting gradient and perspective
3. Fiducial detection overlay with corner coordinates and reprojection vectors
4. Homography-rectified canonical canvas
5. 2D DSSS chip correlation heatmap
6. Composite forensic debug dashboard
"""

import sys
import hashlib
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import cv2
import numpy as np

from core.watermark import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder,
    WatermarkPayload,
    GeometricSynchronizer,
    CanonicalCanvasSpec,
    CarrierConfig,
    CarrierStrategy,
)
from core.traceability import TardosTraceabilityProvider
from attacks.physical.simulation import PrintCameraSimulationAttack


def generate_visual_artifacts():
    out_dir = root_dir / "artifacts" / "physical_validation" / "debug_visuals"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating visual debugging artifacts in: {out_dir}")

    # 1. Base Document Canvas
    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 245
    cv2.putText(canvas, "NATIONAL FORENSIC DIRECTIVE", (130, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    cv2.putText(canvas, "SUBJECT: Physical Watermark Optical Alignment Telemetry", (130, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (60, 60, 60), 1)
    for y in range(250, 850, 40):
        cv2.line(canvas, (130, y), (670, y), (210, 210, 210), 1)
        cv2.putText(canvas, f"Confidential Data Record Section {y // 40 - 5}: [RESTRICTED ACCESS]", (140, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

    # 2. Encode Watermark
    tardos_provider = TardosTraceabilityProvider(
        coalition_size=2,
        false_accusation_epsilon=0.01,
        kappa_factor=5.0,
        recipient_count_hint=5,
    )
    marker = tardos_provider.issue_marker("DOC_VISUAL_01", "REL_VIS_01", "alice", "hash")
    cw = marker.metadata["tardos_codeword"]

    encoder = PrintCameraWatermarkEncoder()
    payload = WatermarkPayload(document_id="DOC_VISUAL_01", release_id="REL_VIS_01", codeword=cw)
    wm_img = encoder.encode(canvas, payload, as_bytes=False)
    cv2.imwrite(str(out_dir / "01_original_watermarked_canvas.png"), wm_img)

    # 3. Simulate Optical Camera Capture
    attack = PrintCameraSimulationAttack()
    params = {
        "perspective_distortion": 0.07,
        "optical_blur_sigma": 1.2,
        "lighting_gradient_strength": 0.30,
        "sensor_noise_sigma": 12.0,
        "jpeg_quality": 75,
        "paper_texture_strength": 0.05,
    }
    wm_bytes = cv2.imencode(".png", wm_img)[1].tobytes()
    attack_out = attack._execute_transform(wm_bytes, params, seed=42)
    captured_img = cv2.imdecode(np.frombuffer(attack_out.artifact_bytes, np.uint8), cv2.IMREAD_COLOR)
    cv2.imwrite(str(out_dir / "02_simulated_camera_capture.png"), captured_img)

    # 4. Fiducial Detection & Homography Overlay
    sync = GeometricSynchronizer(CanonicalCanvasSpec(width=800, height=1000))
    gray_cap = cv2.cvtColor(captured_img, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = sync.detector.detectMarkers(gray_cap)

    detection_vis = captured_img.copy()
    if ids is not None and len(ids) > 0:
        cv2.aruco.drawDetectedMarkers(detection_vis, corners, ids)
        for i, mid in enumerate(ids.flatten()):
            c = corners[i][0]
            center_x = int(np.mean(c[:, 0]))
            center_y = int(np.mean(c[:, 1]))
            cv2.putText(detection_vis, f"Anchor {mid}", (center_x - 30, center_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imwrite(str(out_dir / "03_fiducial_detection_and_homography.png"), detection_vis)

    # 5. Rectified Canonical Canvas
    sync_ok, rectified_img, sync_tel = sync.detect_and_rectify(captured_img)
    if sync_ok and rectified_img is not None:
        cv2.imwrite(str(out_dir / "04_rectified_canonical_canvas.png"), rectified_img)

    # 6. DSSS Spatial Chip Correlation Heatmap
    decoder = PrintCameraWatermarkDecoder()
    obs = decoder.decode(captured_img, expected_document_id="DOC_VISUAL_01", expected_release_id="REL_VIS_01", expected_codeword_length=len(cw))

    # Construct 2D correlation grid visual
    soft_confs = obs.soft_confidences or [0.5] * len(cw)
    grid_cols = (decoder.modulator.config.roi_right - decoder.modulator.config.roi_left) // decoder.modulator.config.block_size
    grid_rows = (decoder.modulator.config.roi_bottom - decoder.modulator.config.roi_top) // decoder.modulator.config.block_size

    heatmap_grid = np.zeros((grid_rows, grid_cols), dtype=np.float32)
    for idx, sc in enumerate(soft_confs[:grid_cols * grid_rows]):
        r = idx // grid_cols
        c = idx % grid_cols
        heatmap_grid[r, c] = abs(sc)

    # Resize to canvas size for visualization
    heatmap_norm = (heatmap_grid * 255.0).astype(np.uint8)
    heatmap_color = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
    heatmap_large = cv2.resize(heatmap_color, (800, 1000), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(str(out_dir / "05_dsss_correlation_heatmap.png"), heatmap_large)

    # 7. Composite Dashboard
    h, w = 500, 400
    p1 = cv2.resize(wm_img, (w, h))
    p2 = cv2.resize(captured_img, (w, h))
    p3 = cv2.resize(detection_vis, (w, h))
    p4 = cv2.resize(rectified_img if rectified_img is not None else captured_img, (w, h))

    # Add header text
    for panel, title in [(p1, "1. Watermarked Canvas"), (p2, "2. Simulated Optical Capture"), (p3, "3. Fiducial Anchors & RANSAC"), (p4, f"4. Rectified ({obs.status.value})")]:
        cv2.rectangle(panel, (0, 0), (w, 35), (30, 30, 30), -1)
        cv2.putText(panel, title, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    top_row = np.hstack([p1, p2])
    bot_row = np.hstack([p3, p4])
    composite = np.vstack([top_row, bot_row])
    cv2.imwrite(str(out_dir / "06_composite_forensic_dashboard.png"), composite)

    print("Successfully generated all 6 visual debugging artifacts.")


if __name__ == "__main__":
    generate_visual_artifacts()
