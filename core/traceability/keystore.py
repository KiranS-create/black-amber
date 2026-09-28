import os
import secrets
import hashlib
import base64
from typing import Optional, Tuple, Dict, List, Any

class TraceabilitySecurityError(Exception):
    """Base exception for traceability security & custody violations."""
    pass

class MissingSecretError(TraceabilitySecurityError):
    """Raised when a required traceability master secret is absent in production mode."""
    pass

class KeyEpochUnavailableError(TraceabilitySecurityError):
    """Raised when an artifact requires a historical key epoch that is unavailable in keystore."""
    pass

class KeyEpochMismatchError(TraceabilitySecurityError):
    """Raised when a supplied secret does not match the artifact's declared key epoch ID."""
    pass

class TraceabilityKeystore:
    """
    Traceability Secret Custody & Keystore Manager.
    
    Custody Hierarchy (Preferred Priority):
    1. Explicit Runtime Secret: Provided directly in function call / constructor.
    2. Environment Variable: SIH26237_TRACEABILITY_MASTER_SECRET (base64 or raw bytes).
    3. Multi-Epoch Registry: In-memory/configured historical keys indexed by key_id.
    4. Local Excluded Keystore: .secrets/traceability_master.key (strictly gitignored).
    5. Development/Demo Auto-Generation: Generated securely via secrets.token_bytes(32) on first run
       and stored in .secrets/ for subsequent runs in development/demo mode.
    6. Production Fail-Closed: When SIH26237_ENV == "production", missing secret raises MissingSecretError.
       NEVER falls back to a hardcoded string.
    """

    ENV_VAR_NAME = "SIH26237_TRACEABILITY_MASTER_SECRET"
    ENV_MODE_VAR = "SIH26237_ENV"
    DEFAULT_SECRETS_DIR = ".secrets"
    DEFAULT_KEY_FILENAME = "traceability_master.key"

    # Multi-epoch registry mapping key_id -> secret_bytes
    _registry: Dict[str, bytes] = {}
    _active_key_id: Optional[str] = None
    _cached_active_secret: Optional[bytes] = None

    @classmethod
    def register_key(cls, secret_bytes: bytes, set_as_active: bool = False) -> str:
        """
        Register a secret key into the multi-epoch keystore registry.
        Returns the derived key_id.
        """
        if isinstance(secret_bytes, str):
            secret_bytes = secret_bytes.encode('utf-8')
        if not secret_bytes or len(secret_bytes) == 0:
            raise ValueError("Secret bytes cannot be empty")
        
        key_id = cls.compute_key_id(secret_bytes)
        cls._registry[key_id] = secret_bytes
        if set_as_active:
            cls._active_key_id = key_id
            cls._cached_active_secret = secret_bytes
        return key_id

    @classmethod
    def get_key_by_id(cls, key_id: str) -> Optional[bytes]:
        """
        Retrieve secret bytes for a specific key epoch by its key_id.
        Direct O(1) lookup without iterating or brute-forcing across keys.
        """
        if not key_id or not isinstance(key_id, str):
            return None
        
        # 1. Direct registry lookup O(1)
        if key_id in cls._registry:
            return cls._registry[key_id]
        
        # 2. Check cached active secret
        if cls._cached_active_secret is not None:
            if cls.compute_key_id(cls._cached_active_secret) == key_id:
                return cls._cached_active_secret
            return None

        # 3. Resolve active secret once and cache
        try:
            active_secret = cls.resolve_secret(allow_dev_generation=False)
            cls._cached_active_secret = active_secret
            if cls.compute_key_id(active_secret) == key_id:
                return active_secret
        except Exception:
            pass

        return None

    @classmethod
    def resolve_key_for_epoch(
        cls,
        key_id: Optional[str] = None,
        explicit_secret: Optional[bytes] = None
    ) -> bytes:
        """
        Resolve secret for a specific key epoch.
        Guarantees:
        - If explicit_secret is provided, verifies that it matches key_id (if passed).
        - If key_id is provided, looks up direct key or fails closed with KeyEpochUnavailableError.
        - If neither is provided, resolves active secret.
        """
        # 1. Explicit secret
        if explicit_secret is not None:
            if isinstance(explicit_secret, str):
                explicit_secret = explicit_secret.encode('utf-8')
            computed_id = cls.compute_key_id(explicit_secret)
            if key_id is not None and key_id != computed_id:
                raise KeyEpochMismatchError(
                    f"Supplied secret has key_id '{computed_id}', which does not match "
                    f"required epoch '{key_id}'."
                )
            return explicit_secret

        # 2. Key ID specified (historical / target lookup)
        if key_id is not None:
            secret = cls.get_key_by_id(key_id)
            if secret is not None:
                return secret
            raise KeyEpochUnavailableError(
                f"Traceability key epoch '{key_id}' is unavailable in the keystore registry. "
                f"Historical analysis cannot proceed without the required epoch key."
            )

        # 3. Fall back to active default secret
        return cls.resolve_secret()

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the multi-epoch registry (primarily for test isolation)."""
        cls._registry.clear()
        cls._active_key_id = None
        cls._cached_active_secret = None

    @classmethod
    def list_known_epochs(cls) -> List[Dict[str, str]]:
        """
        List non-secret metadata for all registered epochs.
        Never exposes raw secret keys.
        """
        epochs = []
        active_id = None
        try:
            active_secret = cls.resolve_secret(allow_dev_generation=False)
            active_id = cls.compute_key_id(active_secret)
        except Exception:
            pass

        for kid in cls._registry:
            epochs.append({
                "key_id": kid,
                "status": "ACTIVE" if kid == (cls._active_key_id or active_id) else "HISTORICAL"
            })
        
        if active_id and active_id not in cls._registry:
            epochs.append({
                "key_id": active_id,
                "status": "ACTIVE"
            })

        return epochs

    @classmethod
    def is_production_mode(cls) -> bool:
        """Check if environment is explicitly configured for production."""
        mode = os.environ.get(cls.ENV_MODE_VAR, "").strip().lower()
        return mode in ("production", "prod")

    @classmethod
    def compute_key_id(cls, secret_bytes: bytes) -> str:
        """
        Derive a safe non-secret Key Identifier (Key Epoch Tag) for marker metadata.
        Format: tkey_<first 8 hex chars of SHA-256(secret)>
        """
        if not secret_bytes or not isinstance(secret_bytes, (bytes, bytearray)):
            raise ValueError("Secret must be non-empty bytes to derive key_id")
        digest = hashlib.sha256(secret_bytes).hexdigest()
        return f"tkey_{digest[:8]}"

    @classmethod
    def get_default_keystore_path(cls) -> str:
        """Return path to local gitignored development keystore file."""
        custom_path = os.environ.get("SIH26237_KEYSTORE_PATH")
        if custom_path:
            return custom_path
        return os.path.join(cls.DEFAULT_SECRETS_DIR, cls.DEFAULT_KEY_FILENAME)

    @classmethod
    def resolve_secret(
        cls,
        explicit_secret: Optional[bytes] = None,
        allow_dev_generation: bool = True
    ) -> bytes:
        """
        Resolve master traceability secret following the secure custody hierarchy.
        
        Returns:
            bytes: Cryptographically strong secret key.
            
        Raises:
            MissingSecretError: If secret is absent in production mode.
        """
        # 1. Explicit runtime secret
        if explicit_secret is not None:
            if isinstance(explicit_secret, str):
                explicit_secret = explicit_secret.encode('utf-8')
            if len(explicit_secret) == 0:
                raise ValueError("Explicit traceability secret cannot be empty bytes")
            return explicit_secret

        # 2. Environment variable
        env_val = os.environ.get(cls.ENV_VAR_NAME)
        if env_val:
            env_val = env_val.strip()
            # Check if base64 encoded
            try:
                decoded = base64.b64decode(env_val)
                if len(decoded) >= 16:
                    return decoded
            except Exception:
                pass
            return env_val.encode('utf-8')
        # 3. Local keystore file path (custom or default)
        custom_path = os.environ.get("SIH26237_KEYSTORE_PATH")
        keystore_path = custom_path if custom_path else os.path.join(cls.DEFAULT_SECRETS_DIR, cls.DEFAULT_KEY_FILENAME)

        # In production mode: allow only if custom path was explicitly set and exists
        if cls.is_production_mode():
            if custom_path and os.path.exists(custom_path):
                try:
                    with open(custom_path, "rb") as f:
                        stored_secret = f.read()
                    if len(stored_secret) >= 16:
                        return stored_secret
                except Exception:
                    pass
            raise MissingSecretError(
                f"Traceability master secret is required in production mode. "
                f"Configure {cls.ENV_VAR_NAME} or supply provider_secret explicitly. "
                f"Hardcoded fallbacks and default dev keystores are strictly prohibited."
            )

        # In development / demo mode: read keystore if it exists
        if os.path.exists(keystore_path):
            try:
                with open(keystore_path, "rb") as f:
                    stored_secret = f.read()
                if len(stored_secret) >= 16:
                    return stored_secret
            except Exception:
                pass

        # 4. Development / Demo Auto-Generation (first-run local secret)
        if allow_dev_generation:
            return cls._generate_and_store_dev_secret(keystore_path)

        raise MissingSecretError("No traceability secret could be resolved.")

    @classmethod
    def _generate_and_store_dev_secret(cls, keystore_path: str) -> bytes:
        """
        Securely generate a local development key and store it in .secrets/ directory.
        """
        new_secret = secrets.token_bytes(32)
        try:
            parent_dir = os.path.dirname(keystore_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(keystore_path, "wb") as f:
                f.write(new_secret)
            # Set restrictive permissions if POSIX
            if hasattr(os, "chmod"):
                try:
                    os.chmod(keystore_path, 0o600)
                except Exception:
                    pass
        except Exception:
            # If filesystem is read-only, return memory-only secret
            pass
        return new_secret

    @classmethod
    def get_custody_status(cls, secret_bytes: bytes) -> str:
        """
        Return safe, non-leaking status descriptor of secret custody for demo/CLI banners.
        """
        key_id = cls.compute_key_id(secret_bytes)
        if os.environ.get(cls.ENV_VAR_NAME):
            source = "ENVIRONMENT_VARIABLE"
        elif os.path.exists(cls.get_default_keystore_path()):
            source = "LOCAL_KEYSTORE (.secrets/)"
        else:
            source = "RUNTIME_SUPPLIED"
        
        mode = "PRODUCTION" if cls.is_production_mode() else "DEVELOPMENT_DEMO"
        return f"TRACEABILITY KEY CUSTODY: [{source}] | Mode: {mode} | KeyID: {key_id}"


# Backward compatibility alias
TraceabilityKeyStore = TraceabilityKeystore
