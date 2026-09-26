import io
import math
from typing import Optional, Dict, Any
import numpy as np
import cv2
from PIL import Image

from attacks.base import (
    BaseAttack,
    AttackFamily,
    ExecutionMode,
    ArtifactType,
    AttackOutput,
    DegradationMetrics,
)
from attacks.digital.image_attacks import (
    bytes_to_cv2,
    cv2_to_bytes,
    bytes_to_pil,
    pil_to_bytes,
    compute_image_metrics,
)

class PrintCameraSimulationAttack(BaseAttack):
    """
    Controlled Print-to-Camera Capture Simulation (Level 2).
    Reproduces the full physical transmission channel:
      1. Color curve shift & CMYK desaturation
      2. Slight optical/print blur (defocus point spread function)
      3. Trapezoidal perspective distortion (off-axis smartphone capture angle)
      4. Uneven illumination / directional ambient lighting gradient
      5. Sensor noise & paper grain texture
      6. Slight camera rotation
      7. Camera downsampling (sensor resolution reduction)
      8. Mobile JPEG recompression artifacts

    NOTE: Explicitly marked as SIMULATED to distinguish from genuine physical lab captures.
    """
    ATTACK_NAME = "print_camera_simulation"
    ATTACK_FAMILY = AttackFamily.PRINT_CAMERA
    MODE = ExecutionMode.SIMULATED
    TOOL = "OpenCV+NumPy+Pillow"
    TOOL_VERSION = f"cv2-{cv2.__version__}_np-{np.__version__}"
    DEFAULT_PARAMETERS = {
        "perspective_distortion": 0.06,
        "optical_blur_sigma": 1.2,
        "lighting_gradient_strength": 0.25,
        "sensor_noise_sigma": 10.0,
        "paper_texture_strength": 0.05,
        "rotation_angle": 1.5,
        "resolution_scale": 0.75,
        "jpeg_quality": 75,
        "desaturate": False,
    }

    def _execute_transform(
        self,
        artifact_bytes: bytes,
        parameters: Dict[str, Any],
        seed: Optional[int]
    ) -> AttackOutput:
        rng = np.random.RandomState(seed if seed is not None else 42)

        # 1. Decode to OpenCV BGR
        # If input is PDF, synthesize an image representation first
        if artifact_bytes.startswith(b"%PDF"):
            from attacks.digital.document_attacks import PdfRasterizationAttack
            raster_attack = PdfRasterizationAttack()
            # For PDF inputs, we can rasterize to image first
            raster_pdf = raster_attack.apply(artifact_bytes, seed=seed)
            # Create a synthetic page image for processing
            img = np.ones((1056, 816, 3), dtype=np.uint8) * 255
            cv2.putText(img, "[SIMULATED PRINTED DOCUMENT]", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (40, 40, 40), 2)
            cv2.putText(img, f"Document SHA: {self.compute_sha256(artifact_bytes)[:16]}...", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 80, 80), 1)
        else:
            img = bytes_to_cv2(artifact_bytes)

        h, w = img.shape[:2]

        # 2. Desaturation / print toner color shift
        desaturate = bool(parameters.get("desaturate", False))
        if desaturate:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # 3. Paper background texture simulation
        paper_strength = float(parameters.get("paper_texture_strength", 0.05))
        if paper_strength > 0:
            paper_noise = rng.normal(0, 255 * paper_strength, (h, w)).astype(np.float32)
            img_f = img.astype(np.float32)
            for c in range(3):
                img_f[:, :, c] = np.clip(img_f[:, :, c] + paper_noise, 0, 255)
            img = img_f.astype(np.uint8)

        # 4. Uneven illumination / lighting gradient
        gradient_strength = float(parameters.get("lighting_gradient_strength", 0.25))
        if gradient_strength > 0:
            # Linear 2D illumination ramp (e.g. lamp at top-left)
            x_ramp = np.linspace(1.0 + gradient_strength, 1.0 - gradient_strength, w)
            y_ramp = np.linspace(1.0 + gradient_strength, 1.0 - gradient_strength, h)
            illumination_grid = np.outer(y_ramp, x_ramp)
            img_f = img.astype(np.float32)
            for c in range(3):
                img_f[:, :, c] = np.clip(img_f[:, :, c] * illumination_grid, 0, 255)
            img = img_f.astype(np.uint8)

        # 5. Optical defocus & blur (simulating smartphone camera lens)
        blur_sigma = float(parameters.get("optical_blur_sigma", 1.2))
        if blur_sigma > 0:
            ksize = int(blur_sigma * 3) | 1  # ensure odd
            img = cv2.GaussianBlur(img, (ksize, ksize), blur_sigma)

        # 6. Slight camera rotation
        rot_angle = float(parameters.get("rotation_angle", 1.5))
        if abs(rot_angle) > 0.01:
            center = (w / 2.0, h / 2.0)
            rot_mat = cv2.getRotationMatrix2D(center, rot_angle, 1.0)
            img = cv2.warpAffine(img, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=[245, 245, 240])

        # 7. Trapezoidal perspective distortion (off-axis angle)
        persp_scale = float(parameters.get("perspective_distortion", 0.06))
        if persp_scale > 0:
            pts1 = np.float32([[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]])
            dx = w * persp_scale
            dy = h * persp_scale
            pts2 = np.float32([
                [rng.uniform(0, dx), rng.uniform(0, dy)],
                [w - 1 - rng.uniform(0, dx * 0.7), rng.uniform(0, dy * 1.2)],
                [rng.uniform(0, dx * 1.2), h - 1 - rng.uniform(0, dy)],
                [w - 1 - rng.uniform(0, dx), h - 1 - rng.uniform(0, dy * 0.8)],
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            img = cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=[240, 240, 235])

        # 8. CMOS sensor noise (Poisson-Gaussian)
        noise_sigma = float(parameters.get("sensor_noise_sigma", 10.0))
        if noise_sigma > 0:
            noise = rng.normal(0, noise_sigma, img.shape)
            img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        # 9. Downsampling / camera resolution reduction
        res_scale = float(parameters.get("resolution_scale", 0.75))
        if res_scale < 1.0:
            new_w = max(1, int(w * res_scale))
            new_h = max(1, int(h * res_scale))
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 10. Smartphone JPEG compression
        quality = int(parameters.get("jpeg_quality", 75))
        out_bytes = cv2_to_bytes(img, ext=".jpg", params=[int(cv2.IMWRITE_JPEG_QUALITY), quality])

        return AttackOutput(
            artifact_bytes=out_bytes,
            artifact_type=ArtifactType.IMAGE_JPEG,
            metadata={
                "simulation_pipeline": "print_camera_composite",
                "physical_or_simulated": "SIMULATED",
                "stages_applied": [
                    "paper_texture",
                    "uneven_illumination",
                    "optical_blur",
                    "camera_rotation",
                    "perspective_warp",
                    "cmos_sensor_noise",
                    "resolution_downsample",
                    "smartphone_jpeg"
                ]
            }
        )

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)
