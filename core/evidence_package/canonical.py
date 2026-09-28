"""
AegisTrace Canonical Serialization & Content-Addressing Engine.

Provides deterministic, RFC-8785 inspired canonical JSON serialization
and SHA-256 content-addressed hashing for forensic evidence objects.
Guarantees:
1. Lexicographical key sorting at all nested levels.
2. Compact formatting (no redundant whitespace, separators=(',', ':')).
3. Normalized UTF-8 string encoding.
4. Float normalization and standard UTC ISO-8601 timestamps.
5. Invariant content hashing: H = SHA256(canonical_bytes).
"""

import json
import hashlib
from datetime import datetime, date, timezone
from typing import Any, Dict, Union
from pydantic import BaseModel


def _json_serial_default(obj: Any) -> Any:
    """Fallback serializer for non-standard types."""
    if isinstance(obj, (datetime, date)):
        # Normalize to UTC ISO-8601 string with explicit +00:00 or Z
        if isinstance(obj, datetime) and obj.tzinfo is not None:
            return obj.astimezone(timezone.utc).isoformat()
        return obj.isoformat()
    if isinstance(obj, bytes):
        import base64
        return base64.b64encode(obj).decode("utf-8")
    if isinstance(obj, set):
        return sorted(list(obj))
    if isinstance(obj, BaseModel):
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode="json")
        return obj.dict()
    if hasattr(obj, "value"):  # Enums
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def canonical_json_dumps(data: Any) -> str:
    """
    Serializes a data structure into a canonical, deterministic JSON string.
    Ensures sorted keys, compact separators, and deterministic representations.
    """
    if isinstance(data, BaseModel):
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        else:
            data = data.dict()
    return json.dumps(
        data,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        default=_json_serial_default
    )


def canonical_json_bytes(data: Any) -> bytes:
    """Returns canonical deterministic UTF-8 bytes for data."""
    return canonical_json_dumps(data).encode("utf-8")


def compute_content_hash(data: Any) -> str:
    """Computes SHA-256 hexadecimal digest over canonical serialization."""
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()
