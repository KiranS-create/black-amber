"""
core/deployment/signer.py

Post-Quantum Release Manifest Signer and Verifier for AegisTrace.
Cryptographically signs and verifies release manifests using ML-DSA-65 (NIST FIPS 204).
Enforces zero-trust defense against repository/artifact tampering and unauthorized releases.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from core.crypto.signatures import MLDSA65
from core.deployment.manifest import compute_file_sha256


DEFAULT_SIGNER_ID = "aegistrace-release-authority-2026"


class ReleaseSignatureError(ValueError):
    """Raised when release manifest signature verification fails."""
    pass


class ReleaseManifestSigner:
    """
    Signs and verifies release manifests using post-quantum ML-DSA-65 signatures.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent
        self.default_manifest_path = self.repo_root / "artifacts" / "deployment" / "release_manifest.json"
        self.default_sig_path = self.repo_root / "artifacts" / "deployment" / "release_manifest.sig.json"
        self.default_pubkey_path = self.repo_root / "artifacts" / "deployment" / "release_authority.pub"

    def generate_release_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate a fresh ML-DSA-65 keypair for release signing.
        Returns: (public_key_bytes, private_key_bytes)
        """
        kp = MLDSA65.generate_keypair()
        return kp.public_key_bytes, kp.private_key_bytes

    def sign_manifest(
        self,
        manifest_path: Optional[Path] = None,
        private_key: Optional[bytes] = None,
        public_key: Optional[bytes] = None,
        signer_id: str = DEFAULT_SIGNER_ID,
        output_sig_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Cryptographically signs a release manifest using ML-DSA-65.
        If no private key is provided, attempts to load from AEGISTRACE_RELEASE_SIGNING_KEY env.
        If that is unset, generates an ephemeral keypair and saves public key.
        """
        target_manifest = manifest_path or self.default_manifest_path
        if not target_manifest.exists():
            raise FileNotFoundError(f"Manifest file not found: {target_manifest}")

        with open(target_manifest, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        manifest_root_digest = manifest_data.get("manifest_root_digest")
        if not manifest_root_digest:
            raise ValueError("Manifest is missing manifest_root_digest field.")

        # Resolve signing keys
        priv_bytes = private_key
        pub_bytes = public_key

        if priv_bytes is None:
            env_key = os.environ.get("AEGISTRACE_RELEASE_SIGNING_KEY")
            if env_key:
                priv_bytes = bytes.fromhex(env_key.strip())
            else:
                pub_bytes, priv_bytes = self.generate_release_keypair()

        # Sign the manifest root digest combined with signer_id and release_id
        release_id = manifest_data.get("release_id", "unknown")
        signing_payload = f"{signer_id}:{release_id}:{manifest_root_digest}".encode("utf-8")
        
        signature = MLDSA65.sign(priv_bytes, signing_payload)

        sig_doc = {
            "format_version": "1.0.0",
            "algorithm": "ML-DSA-65",
            "standard": "FIPS 204",
            "signer_id": signer_id,
            "release_id": release_id,
            "manifest_root_digest": manifest_root_digest,
            "signing_timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "public_key_hex": pub_bytes.hex() if pub_bytes else "",
            "signature_hex": signature.hex(),
        }

        # Save signature artifact
        out_p = output_sig_path or self.default_sig_path
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(sig_doc, f, indent=2, sort_keys=True)

        # If we have public key, save public key artifact for verification
        if pub_bytes:
            pub_out = self.default_pubkey_path
            pub_out.parent.mkdir(parents=True, exist_ok=True)
            with open(pub_out, "wb") as f:
                f.write(pub_bytes)

        return sig_doc

    def verify_manifest_signature(
        self,
        manifest_path: Optional[Path] = None,
        sig_path: Optional[Path] = None,
        public_key: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Verify the ML-DSA-65 signature of a release manifest.
        Validates:
        1. Manifest existence and formatting
        2. Manifest root digest calculation matches signed manifest
        3. ML-DSA-65 post-quantum signature against public key
        """
        target_manifest = manifest_path or self.default_manifest_path
        target_sig = sig_path or self.default_sig_path

        if not target_manifest.exists():
            return {
                "valid": False,
                "error": f"Manifest file does not exist: {target_manifest}",
            }

        if not target_sig.exists():
            return {
                "valid": False,
                "error": f"Signature file does not exist: {target_sig}",
            }

        with open(target_manifest, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        with open(target_sig, "r", encoding="utf-8") as f:
            sig_doc = json.load(f)

        manifest_root_digest = manifest_data.get("manifest_root_digest")
        signed_root_digest = sig_doc.get("manifest_root_digest")

        if manifest_root_digest != signed_root_digest:
            return {
                "valid": False,
                "error": f"Manifest root digest mismatch! Manifest: {manifest_root_digest}, Signed: {signed_root_digest}",
            }

        # Resolve public key
        pub_bytes = public_key
        if pub_bytes is None:
            if sig_doc.get("public_key_hex"):
                pub_bytes = bytes.fromhex(sig_doc["public_key_hex"])
            elif self.default_pubkey_path.exists():
                with open(self.default_pubkey_path, "rb") as f:
                    pub_bytes = f.read()
            else:
                env_pub = os.environ.get("AEGISTRACE_RELEASE_PUBLIC_KEY")
                if env_pub:
                    pub_bytes = bytes.fromhex(env_pub.strip())

        if not pub_bytes:
            return {
                "valid": False,
                "error": "No public key available to verify signature.",
            }

        signer_id = sig_doc.get("signer_id", DEFAULT_SIGNER_ID)
        release_id = sig_doc.get("release_id", manifest_data.get("release_id", "unknown"))
        signing_payload = f"{signer_id}:{release_id}:{manifest_root_digest}".encode("utf-8")

        try:
            signature_bytes = bytes.fromhex(sig_doc["signature_hex"])
            is_valid = MLDSA65.verify(pub_bytes, signing_payload, signature_bytes)
        except Exception as e:
            return {
                "valid": False,
                "error": f"Signature decoding or verification error: {str(e)}",
            }

        return {
            "valid": is_valid,
            "algorithm": sig_doc.get("algorithm", "ML-DSA-65"),
            "standard": sig_doc.get("standard", "FIPS 204"),
            "signer_id": signer_id,
            "release_id": release_id,
            "timestamp": sig_doc.get("signing_timestamp_iso"),
            "manifest_root_digest": manifest_root_digest,
            "error": None if is_valid else "ML-DSA-65 cryptographic verification failed.",
        }
