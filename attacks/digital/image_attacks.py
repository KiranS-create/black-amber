import io
import math
from typing import Optional, Dict, Any, Tuple
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageOps

from attacks.base import (
    BaseAttack,
    AttackFamily,
    ExecutionMode,
    ArtifactType,
    AttackOutput,
    DegradationMetrics,
)

def bytes_to_pil(data: bytes) -> Image.Image:
    """Decode image bytes to PIL Image, converting palette/CMYK/RGBA as needed."""
    img = Image.open(io.BytesIO(data))
    img.load()
    return img

def pil_to_bytes(img: Image.Image, format_name: str = "PNG", **save_kwargs) -> bytes:
    """Encode PIL Image to bytes."""
    buf = io.BytesIO()
    # Format normalization: if saving as JPEG, ensure RGB
    if format_name.upper() in ("JPEG", "JPG"):
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
    img.save(buf, format=format_name, **save_kwargs)
    return buf.getvalue()

def bytes_to_cv2(data: bytes) -> np.ndarray:
    """Decode image bytes to OpenCV BGR numpy array."""
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image bytes using OpenCV.")
    return img

def cv2_to_bytes(img: np.ndarray, ext: str = ".png", params: Optional[list] = None) -> bytes:
    """Encode OpenCV numpy array to bytes."""
    success, enc = cv2.imencode(ext, img, params or [])
    if not success:
        raise ValueError(f"Failed to encode image to {ext} using OpenCV.")
    return enc.tobytes()

def compute_image_metrics(orig_bytes: bytes, mod_bytes: bytes) -> Optional[DegradationMetrics]:
    """Compute PSNR, SSIM, MAE, and size ratio between original and transformed image."""
    try:
        orig = bytes_to_cv2(orig_bytes)
        mod = bytes_to_cv2(mod_bytes)
        
        # Resize mod to orig if dimensions differ
        if orig.shape[:2] != mod.shape[:2]:
            mod_aligned = cv2.resize(mod, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_LINEAR)
        else:
            mod_aligned = mod

        # MAE
        mae = float(np.mean(np.abs(orig.astype(np.float64) - mod_aligned.astype(np.float64))))

        # PSNR
        mse = float(np.mean((orig.astype(np.float64) - mod_aligned.astype(np.float64)) ** 2))
        if mse == 0:
            psnr = 100.0
        else:
            psnr = float(10.0 * math.log10((255.0 ** 2) / mse))

        # Basic SSIM (luminance + contrast + structure on grayscale)
        g_orig = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY).astype(np.float64)
        g_mod = cv2.cvtColor(mod_aligned, cv2.COLOR_BGR2GRAY).astype(np.float64)

        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2
        mu1 = cv2.GaussianBlur(g_orig, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(g_mod, (11, 11), 1.5)
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(g_orig ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(g_mod ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(g_orig * g_mod, (11, 11), 1.5) - mu1_mu2

        ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
        ssim = float(np.mean(ssim_map))

        ratio = len(mod_bytes) / max(len(orig_bytes), 1)

        return DegradationMetrics(
            psnr=round(psnr, 2),
            ssim=round(ssim, 4),
            mae=round(mae, 2),
            file_size_ratio=round(ratio, 4)
        )
    except Exception:
        ratio = len(mod_bytes) / max(len(orig_bytes), 1)
        return DegradationMetrics(file_size_ratio=round(ratio, 4))


# 1. JPEG Recompression Attack
class JpegRecompressionAttack(BaseAttack):
    ATTACK_NAME = "jpeg_recompression"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"quality": 75, "subsampling": 0}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        quality = int(parameters.get("quality", 75))
        subsampling = int(parameters.get("subsampling", 0))
        img = bytes_to_pil(artifact_bytes)
        out_bytes = pil_to_bytes(img, format_name="JPEG", quality=quality, subsampling=subsampling)
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_JPEG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 2. PNG Conversion Attack
class PngConversionAttack(BaseAttack):
    ATTACK_NAME = "png_conversion"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"optimize": True}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        optimize = bool(parameters.get("optimize", True))
        img = bytes_to_pil(artifact_bytes)
        out_bytes = pil_to_bytes(img, format_name="PNG", optimize=optimize)
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 3. Quality Reduction Attack
class QualityReductionAttack(BaseAttack):
    ATTACK_NAME = "quality_reduction"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"quality": 30}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        quality = int(parameters.get("quality", 30))
        img = bytes_to_pil(artifact_bytes)
        out_bytes = pil_to_bytes(img, format_name="JPEG", quality=quality)
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_JPEG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 4. Resizing Attack
class ResizeAttack(BaseAttack):
    ATTACK_NAME = "resizing"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"scale_factor": 0.5, "resample": "BILINEAR"}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        scale_factor = float(parameters.get("scale_factor", 0.5))
        resample_str = str(parameters.get("resample", "BILINEAR")).upper()
        resample_map = {
            "NEAREST": Image.Resampling.NEAREST,
            "BILINEAR": Image.Resampling.BILINEAR,
            "BICUBIC": Image.Resampling.BICUBIC,
            "LANCZOS": Image.Resampling.LANCZOS,
        }
        resample_method = resample_map.get(resample_str, Image.Resampling.BILINEAR)

        img = bytes_to_pil(artifact_bytes)
        new_w = max(1, int(img.width * scale_factor))
        new_h = max(1, int(img.height * scale_factor))
        resized = img.resize((new_w, new_h), resample=resample_method)
        out_bytes = pil_to_bytes(resized, format_name=img.format or "PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 5. Downscaling/Upscaling Attack
class DownscaleUpscaleAttack(BaseAttack):
    ATTACK_NAME = "downscale_upscale"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"factor": 0.25, "down_resample": "BILINEAR", "up_resample": "BILINEAR"}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        factor = float(parameters.get("factor", 0.25))
        img = bytes_to_pil(artifact_bytes)
        orig_w, orig_h = img.width, img.height

        down_w = max(1, int(orig_w * factor))
        down_h = max(1, int(orig_h * factor))
        down = img.resize((down_w, down_h), resample=Image.Resampling.BILINEAR)
        up = down.resize((orig_w, orig_h), resample=Image.Resampling.BILINEAR)

        out_bytes = pil_to_bytes(up, format_name=img.format or "PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 6. Blur Attack
class GaussianBlurAttack(BaseAttack):
    ATTACK_NAME = "gaussian_blur"
    TOOL = "OpenCV"
    TOOL_VERSION = cv2.__version__
    DEFAULT_PARAMETERS = {"kernel_size": 5, "sigma": 1.5}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        ksize = int(parameters.get("kernel_size", 5))
        if ksize % 2 == 0:
            ksize += 1
        sigma = float(parameters.get("sigma", 1.5))
        img = bytes_to_cv2(artifact_bytes)
        blurred = cv2.GaussianBlur(img, (ksize, ksize), sigma)
        out_bytes = cv2_to_bytes(blurred, ext=".png")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 7. Sharpening Attack
class SharpenAttack(BaseAttack):
    ATTACK_NAME = "sharpen"
    TOOL = "OpenCV"
    TOOL_VERSION = cv2.__version__
    DEFAULT_PARAMETERS = {"strength": 1.5}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        strength = float(parameters.get("strength", 1.5))
        img = bytes_to_cv2(artifact_bytes)
        # Unsharp masking
        gaussian = cv2.GaussianBlur(img, (0, 0), 2.0)
        sharpened = cv2.addWeighted(img, 1.0 + strength, gaussian, -strength, 0)
        out_bytes = cv2_to_bytes(sharpened, ext=".png")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 8. Gaussian Noise Attack
class GaussianNoiseAttack(BaseAttack):
    ATTACK_NAME = "gaussian_noise"
    TOOL = "NumPy"
    TOOL_VERSION = np.__version__
    DEFAULT_PARAMETERS = {"mean": 0.0, "std": 15.0}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        mean = float(parameters.get("mean", 0.0))
        std = float(parameters.get("std", 15.0))
        rng = np.random.RandomState(seed if seed is not None else 42)

        img = bytes_to_cv2(artifact_bytes)
        noise = rng.normal(mean, std, img.shape)
        noisy = np.clip(img.astype(np.float64) + noise, 0, 255).astype(np.uint8)

        out_bytes = cv2_to_bytes(noisy, ext=".png")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 9. Salt-and-Pepper Noise Attack
class SaltAndPepperNoiseAttack(BaseAttack):
    ATTACK_NAME = "salt_and_pepper_noise"
    TOOL = "NumPy"
    TOOL_VERSION = np.__version__
    DEFAULT_PARAMETERS = {"amount": 0.02, "salt_ratio": 0.5}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        amount = float(parameters.get("amount", 0.02))
        salt_ratio = float(parameters.get("salt_ratio", 0.5))
        rng = np.random.RandomState(seed if seed is not None else 42)

        img = bytes_to_cv2(artifact_bytes)
        noisy = img.copy()
        num_salt = int(amount * img.size * salt_ratio / img.shape[2])
        num_pepper = int(amount * img.size * (1.0 - salt_ratio) / img.shape[2])

        # Salt
        coords = [rng.randint(0, i, num_salt) for i in img.shape[:2]]
        noisy[tuple(coords)] = 255

        # Pepper
        coords = [rng.randint(0, i, num_pepper) for i in img.shape[:2]]
        noisy[tuple(coords)] = 0

        out_bytes = cv2_to_bytes(noisy, ext=".png")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 10. Brightness Changes Attack
class BrightnessAttack(BaseAttack):
    ATTACK_NAME = "brightness_change"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"factor": 1.25}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        factor = float(parameters.get("factor", 1.25))
        img = bytes_to_pil(artifact_bytes)
        enhancer = ImageEnhance.Brightness(img)
        enhanced = enhancer.enhance(factor)
        out_bytes = pil_to_bytes(enhanced, format_name=img.format or "PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 11. Contrast Changes Attack
class ContrastAttack(BaseAttack):
    ATTACK_NAME = "contrast_change"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"factor": 1.3}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        factor = float(parameters.get("factor", 1.3))
        img = bytes_to_pil(artifact_bytes)
        enhancer = ImageEnhance.Contrast(img)
        enhanced = enhancer.enhance(factor)
        out_bytes = pil_to_bytes(enhanced, format_name=img.format or "PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 12. Grayscale Conversion Attack
class GrayscaleConversionAttack(BaseAttack):
    ATTACK_NAME = "grayscale_conversion"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        img = bytes_to_pil(artifact_bytes)
        gray = ImageOps.grayscale(img)
        out_bytes = pil_to_bytes(gray, format_name="PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 13. Color-space Conversion Attack
class ColorSpaceConversionAttack(BaseAttack):
    ATTACK_NAME = "colorspace_conversion"
    TOOL = "OpenCV"
    TOOL_VERSION = cv2.__version__
    DEFAULT_PARAMETERS = {"target_space": "HSV"}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        target = str(parameters.get("target_space", "HSV")).upper()
        img = bytes_to_cv2(artifact_bytes)
        if target == "HSV":
            converted = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # Revert back to simulate round-trip quantization
            reverted = cv2.cvtColor(converted, cv2.COLOR_HSV2BGR)
        elif target == "LAB":
            converted = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            reverted = cv2.cvtColor(converted, cv2.COLOR_LAB2BGR)
        elif target == "YCRCB":
            converted = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
            reverted = cv2.cvtColor(converted, cv2.COLOR_YCrCb2BGR)
        else:
            reverted = img

        out_bytes = cv2_to_bytes(reverted, ext=".png")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 14. Rotation Attack
class RotationAttack(BaseAttack):
    ATTACK_NAME = "rotation"
    TOOL = "OpenCV"
    TOOL_VERSION = cv2.__version__
    DEFAULT_PARAMETERS = {"angle": 2.0, "fill_color": [255, 255, 255]}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        angle = float(parameters.get("angle", 2.0))
        fill_color = parameters.get("fill_color", [255, 255, 255])
        img = bytes_to_cv2(artifact_bytes)
        h, w = img.shape[:2]
        center = (w / 2.0, h / 2.0)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=fill_color)
        out_bytes = cv2_to_bytes(rotated, ext=".png")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 15. Slight Perspective Transformation Attack
class PerspectiveTransformAttack(BaseAttack):
    ATTACK_NAME = "perspective_transform"
    TOOL = "OpenCV"
    TOOL_VERSION = cv2.__version__
    DEFAULT_PARAMETERS = {"distortion_scale": 0.05}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        scale = float(parameters.get("distortion_scale", 0.05))
        rng = np.random.RandomState(seed if seed is not None else 42)

        img = bytes_to_cv2(artifact_bytes)
        h, w = img.shape[:2]

        pts1 = np.float32([[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]])
        dx = w * scale
        dy = h * scale

        # Apply random offsets to 4 corners
        pts2 = np.float32([
            [rng.uniform(0, dx), rng.uniform(0, dy)],
            [w - 1 - rng.uniform(0, dx), rng.uniform(0, dy)],
            [rng.uniform(0, dx), h - 1 - rng.uniform(0, dy)],
            [w - 1 - rng.uniform(0, dx), h - 1 - rng.uniform(0, dy)],
        ])

        M = cv2.getPerspectiveTransform(pts1, pts2)
        warped = cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=[255, 255, 255])
        out_bytes = cv2_to_bytes(warped, ext=".png")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 16. Crop Attack
class CropAttack(BaseAttack):
    ATTACK_NAME = "crop"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"crop_fraction": 0.1, "anchor": "center"}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        frac = float(parameters.get("crop_fraction", 0.1))
        anchor = str(parameters.get("anchor", "center")).lower()

        img = bytes_to_pil(artifact_bytes)
        w, h = img.width, img.height

        dx = int(w * frac / 2.0)
        dy = int(h * frac / 2.0)

        if anchor == "center":
            box = (dx, dy, w - dx, h - dy)
        elif anchor == "top_left":
            box = (0, 0, w - 2 * dx, h - 2 * dy)
        elif anchor == "bottom_right":
            box = (2 * dx, 2 * dy, w, h)
        else:
            box = (dx, dy, w - dx, h - dy)

        cropped = img.crop(box)
        out_bytes = pil_to_bytes(cropped, format_name=img.format or "PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 17. Partial Crop Attack
class PartialCropAttack(BaseAttack):
    ATTACK_NAME = "partial_crop"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"side": "bottom", "fraction": 0.15}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        side = str(parameters.get("side", "bottom")).lower()
        fraction = float(parameters.get("fraction", 0.15))

        img = bytes_to_pil(artifact_bytes)
        w, h = img.width, img.height

        if side == "bottom":
            box = (0, 0, w, int(h * (1.0 - fraction)))
        elif side == "top":
            box = (0, int(h * fraction), w, h)
        elif side == "left":
            box = (int(w * fraction), 0, w, h)
        elif side == "right":
            box = (0, 0, int(w * (1.0 - fraction)), h)
        else:
            box = (0, 0, w, int(h * (1.0 - fraction)))

        cropped = img.crop(box)
        out_bytes = pil_to_bytes(cropped, format_name=img.format or "PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 18. Screenshot Simulation Attack
class ScreenshotSimulationAttack(BaseAttack):
    ATTACK_NAME = "screenshot_simulation"
    TOOL = "OpenCV"
    TOOL_VERSION = cv2.__version__
    DEFAULT_PARAMETERS = {"device_scale": 0.85, "display_gamma": 1.1, "add_border": True}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        scale = float(parameters.get("device_scale", 0.85))
        gamma = float(parameters.get("display_gamma", 1.1))
        add_border = bool(parameters.get("add_border", True))

        img = bytes_to_cv2(artifact_bytes)
        h, w = img.shape[:2]

        # 1. Scale down to device viewport
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        scaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 2. Display gamma shift
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
        tinted = cv2.LUT(scaled, table)

        # 3. Add simulated OS frame / border if requested
        if add_border:
            border_top = 30
            border_bottom = 20
            border_side = 10
            framed = cv2.copyMakeBorder(
                tinted, border_top, border_bottom, border_side, border_side,
                borderType=cv2.BORDER_CONSTANT, value=[40, 40, 40]
            )
        else:
            framed = tinted

        out_bytes = cv2_to_bytes(framed, ext=".png")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)


# 19. Image Re-encoding Attack
class ImageReEncodingAttack(BaseAttack):
    ATTACK_NAME = "image_reencoding"
    TOOL = "Pillow"
    TOOL_VERSION = Image.__version__
    DEFAULT_PARAMETERS = {"cycles": 3, "quality": 85}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        cycles = int(parameters.get("cycles", 3))
        quality = int(parameters.get("quality", 85))

        current_bytes = artifact_bytes
        for _ in range(cycles):
            img = bytes_to_pil(current_bytes)
            current_bytes = pil_to_bytes(img, format_name="JPEG", quality=quality)

        return AttackOutput(artifact_bytes=current_bytes, artifact_type=ArtifactType.IMAGE_JPEG)

    def _compute_metrics(self, orig_bytes: bytes, mod_bytes: bytes, parameters: Dict[str, Any]) -> Optional[DegradationMetrics]:
        return compute_image_metrics(orig_bytes, mod_bytes)
