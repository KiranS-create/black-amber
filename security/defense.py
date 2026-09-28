import base64
import math
import re
from typing import Any, Dict, List, Optional, Tuple

class SecurityValidationError(ValueError):
    """Raised when an input fails security boundary validation."""
    pass

def validate_base64_payload(
    b64_str: str,
    max_size_bytes: int = 50 * 1024 * 1024,
    min_size_bytes: int = 1
) -> bytes:
    """
    Validates a base64 string before full decoding to prevent memory exhaustion (DoS).
    - Checks length of base64 string against maximum allowed decoded size.
    - Ensures valid base64 character set.
    - Decodes and verifies exact output length bounds.
    """
    if not isinstance(b64_str, str):
        raise SecurityValidationError("Payload must be a base64 string")

    # Estimate decoded length: len(b64_str) * 3 / 4
    # If the base64 string is suspiciously large, reject before decoding
    max_b64_len = int(max_size_bytes * 4 / 3) + 8
    if len(b64_str) > max_b64_len:
        raise SecurityValidationError(
            f"Base64 payload length ({len(b64_str)}) exceeds maximum allowed size ({max_b64_len})"
        )

    # Validate character set (alphanumerics, +, /, =, and whitespace)
    clean_b64 = re.sub(r"\s+", "", b64_str)
    if len(clean_b64) % 4 == 1:
        raise SecurityValidationError("Invalid base64 payload length: cannot be 1 more than multiple of 4")
    if ('=' in clean_b64 and len(clean_b64) % 4 != 0) or clean_b64.count('=') > 2 or ('=' in clean_b64 and not clean_b64.endswith('=')):
        raise SecurityValidationError("Invalid base64 padding detected")
    if not re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", clean_b64):
        raise SecurityValidationError("Invalid base64 encoding characters detected")

    try:
        raw_bytes = base64.b64decode(clean_b64, validate=True)
    except Exception as e:
        raise SecurityValidationError(f"Base64 decoding failed: {str(e)}")

    if len(raw_bytes) < min_size_bytes:
        raise SecurityValidationError(f"Decoded payload too small ({len(raw_bytes)} bytes)")
    if len(raw_bytes) > max_size_bytes:
        raise SecurityValidationError(f"Decoded payload exceeds limit ({len(raw_bytes)} > {max_size_bytes} bytes)")

    return raw_bytes

def sanitize_header_value(value: str, fallback: str = "artifact.bin") -> str:
    """
    Sanitize values destined for HTTP response headers (e.g. Content-Disposition).
    Strips carriage returns, newlines, null bytes, and quotes to prevent HTTP Response Splitting.
    """
    if not value or not isinstance(value, str):
        return fallback
    # Remove control characters, quotes, semicolons, backslashes
    sanitized = re.sub(r'[\r\n\x00"\\;]', '_', value)
    sanitized = sanitized.strip()
    return sanitized or fallback

def sanitize_numeric_bounds(
    val: float,
    min_val: float = 0.0,
    max_val: float = 1.0,
    default: float = 0.0
) -> float:
    """
    Ensures a numeric score/reliability is a valid finite float within [min_val, max_val].
    Replaces NaN, +Inf, -Inf with default or clamped value.
    """
    if not isinstance(val, (int, float)):
        return default
    if math.isnan(val) or math.isinf(val):
        return default
    return max(min_val, min(max_val, float(val)))

def sanitize_log_likelihood(
    val: float,
    max_abs_val: float = 100.0,
    default: float = 0.0
) -> float:
    """
    Sanitizes Log-Likelihood Ratio (LLR) values.
    Rejects NaN / Infinity and clamps extreme values to [-max_abs_val, max_abs_val].
    """
    if not isinstance(val, (int, float)):
        return default
    if math.isnan(val) or math.isinf(val):
        return default
    return max(-max_abs_val, min(max_abs_val, float(val)))

def sanitize_evidence_observation(obs_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deeply sanitizes an incoming evidence observation dictionary before fusion.
    Prevents NaN/Inf injection, negative reliabilities, or corrupted candidate scores.
    """
    sanitized = dict(obs_dict)
    
    # Sanitize LLR
    raw_llr = sanitized.get("log_likelihood_ratio", 0.0)
    sanitized["log_likelihood_ratio"] = sanitize_log_likelihood(raw_llr)

    # Sanitize reliabilities
    raw_rel = sanitized.get("effective_reliability", 1.0)
    sanitized["effective_reliability"] = sanitize_numeric_bounds(raw_rel, 0.0, 1.0, default=0.5)

    raw_prior = sanitized.get("reliability_prior", 1.0)
    sanitized["reliability_prior"] = sanitize_numeric_bounds(raw_prior, 0.0, 1.0, default=1.0)

    # Sanitize candidate scores dictionary
    candidate_scores = sanitized.get("candidate_scores", {})
    if isinstance(candidate_scores, dict):
        clean_scores = {}
        for cand, score in candidate_scores.items():
            if isinstance(cand, str) and cand.strip():
                clean_scores[cand.strip()] = sanitize_log_likelihood(score)
        sanitized["candidate_scores"] = clean_scores
    else:
        sanitized["candidate_scores"] = {}

    return sanitized

def check_evidence_contradiction(
    candidate_scores: Dict[str, float],
    conflict_threshold: float = 5.0,
    min_separation_margin: float = 2.5
) -> Tuple[bool, Optional[str], Optional[str], float, float]:
    """
    Evaluates whether candidate scores represent an irreconcilable conflict.
    Safety Axiom: If two candidates both exhibit high scores (>= conflict_threshold),
    the system MUST flag a contradiction even if one score is higher, unless one candidate
    completely eclipses the other by an overwhelming margin.
    
    Returns: (is_conflict, top_cand, runnerup_cand, top_score, runnerup_score)
    """
    if not candidate_scores or len(candidate_scores) < 2:
        return False, None, None, 0.0, 0.0

    sorted_scores = sorted(candidate_scores.items(), key=lambda kv: kv[1], reverse=True)
    top_cand, top_score = sorted_scores[0]
    runnerup_cand, runnerup_score = sorted_scores[1]
    margin = top_score - runnerup_score

    # If runner-up independently exceeds the conflict threshold:
    # Contradiction exists if runnerup_score >= conflict_threshold and margin < min_separation_margin
    # OR if runnerup has a verified strong signal that cannot be casually dismissed.
    if runnerup_score >= conflict_threshold and margin < min_separation_margin:
        return True, top_cand, runnerup_cand, top_score, runnerup_score

    return False, top_cand, runnerup_cand, top_score, runnerup_score

def verify_caller_signature(
    public_key_bytes: bytes,
    message: bytes,
    signature_bytes: bytes,
    algorithm: str = "ML-DSA-65"
) -> bool:
    """
    Defensive verification of digital signatures to protect API endpoints against caller spoofing.
    """
    from core.crypto.signatures import MLDSA65
    if len(public_key_bytes) == 0 or len(signature_bytes) == 0:
        return False
    try:
        return MLDSA65.verify(public_key_bytes, message, signature_bytes)
    except Exception:
        return False

def safe_mime_check(payload: bytes, allowed_mimes: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Sniffs magic bytes and verifies that executable/PE headers are rejected.
    """
    allowed = allowed_mimes or [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/csv",
        "application/rtf",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
        "application/zip",
        "application/x-zip-compressed",
        "application/json",
        "application/octet-stream",
    ]
    if len(payload) == 0:
        return False, "empty"

    # Reject Windows PE executables / DLLs
    if payload.startswith(b"MZ"):
        return False, "application/x-dosexec"
    # Reject ELF binaries
    if payload.startswith(b"\x7fELF"):
        return False, "application/x-executable"
    if payload.startswith(b"#!"):
        return False, "text/x-shellscript"

    try:
        from core.formats.detector import FormatDetector
        res = FormatDetector.identify_format(payload)
        detected = res.mime_type
    except Exception:
        if payload.startswith(b"%PDF"):
            detected = "application/pdf"
        elif payload.startswith(b"\x89PNG\r\n\x1a\n"):
            detected = "image/png"
        elif payload.startswith(b"\xff\xd8\xff"):
            detected = "image/jpeg"
        elif payload.startswith(b"{\\rtf"):
            detected = "application/rtf"
        elif payload.startswith(b"PK\x03\x04"):
            detected = "application/zip"
        else:
            detected = "application/octet-stream"

    return (detected in allowed or "application/octet-stream" in allowed), detected

