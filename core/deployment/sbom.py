"""
core/deployment/sbom.py

Deterministic Software Bill of Materials (SBOM) generator for AegisTrace.
Supports:
  1. CycloneDX 1.5 JSON standard
  2. SPDX 2.3 JSON standard

Ensures strict determinism via canonical component sorting, normalized license IDs,
and reproducible timestamps via SOURCE_DATE_EPOCH.
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

from core.deployment.inventory import DependencyInventoryResolver, DependencyType


class SBOMFormat:
    CYCLONEDX_1_5 = "cyclonedx_1_5"
    SPDX_2_3 = "spdx_2_3"


def get_deterministic_timestamp() -> str:
    """
    Return deterministic ISO timestamp based on SOURCE_DATE_EPOCH or default release epoch.
    """
    epoch_str = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch_str:
        try:
            dt = datetime.fromtimestamp(int(epoch_str), tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass
    # Canonical project release timestamp for build reproducibility
    return "2026-09-27T00:00:00Z"


def get_deterministic_serial(inventory: Dict[str, Any]) -> str:
    """Derive deterministic UUID from inventory hash."""
    inv_str = json.dumps(inventory["summary"], sort_keys=True)
    digest = hashlib.sha256(inv_str.encode()).hexdigest()
    # Format as urn:uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    return f"urn:uuid:{digest[:8]}-{digest[8:12]}-4{digest[13:16]}-8{digest[17:20]}-{digest[20:32]}"


class CycloneDXGenerator:
    """Generates CycloneDX 1.5 JSON formatted SBOM."""

    @classmethod
    def generate(cls, inventory: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = get_deterministic_timestamp()
        serial = get_deterministic_serial(inventory)

        components: List[Dict[str, Any]] = []
        dependencies: List[Dict[str, Any]] = []

        # Sort packages strictly by name
        sorted_packages = sorted(inventory["packages"], key=lambda p: p["name"])

        for pkg in sorted_packages:
            name = pkg["name"]
            version = pkg["installed_version"] or pkg["pinned_version"] or "unknown"
            purl = pkg["package_url"]

            # Construct component
            comp_entry: Dict[str, Any] = {
                "type": "library",
                "bom-ref": purl,
                "name": name,
                "version": version,
                "purl": purl,
                "scope": "required" if pkg["is_runtime_critical"] else "optional",
                "properties": [
                    {"name": "aegistrace:dependency_type", "value": pkg["dependency_type"]},
                    {"name": "aegistrace:is_crypto_sensitive", "value": str(pkg["is_crypto_sensitive"]).lower()},
                    {"name": "aegistrace:is_runtime_critical", "value": str(pkg["is_runtime_critical"]).lower()},
                ],
            }

            lic = pkg.get("license")
            if lic and lic != "UNKNOWN":
                comp_entry["licenses"] = [{"license": {"name": lic}}]

            components.append(comp_entry)

            # Dependencies
            direct_deps = pkg.get("direct_dependencies", [])
            dep_refs = [
                f"pkg:pypi/{d}" for d in sorted(direct_deps)
            ]
            dependencies.append({
                "ref": purl,
                "dependsOn": dep_refs,
            })

        bom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": serial,
            "version": 1,
            "metadata": {
                "timestamp": timestamp,
                "tools": [
                    {
                        "vendor": "AegisTrace",
                        "name": "aegistrace-sbom-engine",
                        "version": "1.0.0",
                    }
                ],
                "component": {
                    "bom-ref": "pkg:generic/aegistrace@1.0.0",
                    "type": "application",
                    "name": "AegisTrace",
                    "version": "1.0.0",
                    "description": "Forensic Security & Post-Quantum Watermarking Platform",
                },
            },
            "components": components,
            "dependencies": dependencies,
        }
        return bom


class SPDXGenerator:
    """Generates SPDX 2.3 JSON formatted SBOM."""

    @classmethod
    def generate(cls, inventory: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = get_deterministic_timestamp()
        spdx_packages: List[Dict[str, Any]] = []
        relationships: List[Dict[str, Any]] = []

        # Root AegisTrace application package
        root_spdx_id = "SPDXRef-Application-AegisTrace"
        spdx_packages.append({
            "SPDXID": root_spdx_id,
            "name": "AegisTrace",
            "versionInfo": "1.0.0",
            "downloadLocation": "NONE",
            "filesAnalyzed": False,
            "supplier": "Organization: AegisTrace Defense Security",
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "Apache-2.0",
            "copyrightText": "Copyright (c) 2026 AegisTrace Team",
            "description": "Forensic Security & Post-Quantum Watermarking Platform",
        })

        sorted_packages = sorted(inventory["packages"], key=lambda p: p["name"])

        for pkg in sorted_packages:
            name = pkg["name"]
            version = pkg["installed_version"] or pkg["pinned_version"] or "unknown"
            spdx_id = f"SPDXRef-Package-{name.replace('_', '-').replace('.', '-')}"

            lic = pkg.get("license") or "NOASSERTION"
            if lic == "UNKNOWN":
                lic = "NOASSERTION"

            spdx_packages.append({
                "SPDXID": spdx_id,
                "name": name,
                "versionInfo": version,
                "downloadLocation": f"https://pypi.org/project/{name}/{version}/",
                "filesAnalyzed": False,
                "supplier": "NOASSERTION",
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": lic,
                "copyrightText": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": pkg["package_url"],
                    }
                ],
            })

            # Relationship: AegisTrace DEPENDS_ON Package
            relationships.append({
                "spdxElementId": root_spdx_id,
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": spdx_id,
            })

        doc = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": "AegisTrace-SupplyChain-SBOM",
            "documentNamespace": f"https://aegistrace.local/spdxdocs/aegistrace-1.0.0-{hashlib.sha256(timestamp.encode()).hexdigest()[:8]}",
            "creationInfo": {
                "created": timestamp,
                "creators": ["Tool: AegisTrace-SBOM-Generator-1.0.0"],
            },
            "packages": spdx_packages,
            "relationships": relationships,
        }
        return doc


class SBOMManager:
    """Manages generation, storage, and deterministic validation of SBOMs."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent
        self.sbom_dir = self.repo_root / "artifacts" / "sbom"
        self.inventory_resolver = DependencyInventoryResolver(self.repo_root)

    def generate_all(self) -> Dict[str, Path]:
        """Generate both CycloneDX and SPDX SBOM artifacts deterministically."""
        self.sbom_dir.mkdir(parents=True, exist_ok=True)
        inventory = self.inventory_resolver.resolve_inventory()

        cyclonedx_doc = CycloneDXGenerator.generate(inventory)
        spdx_doc = SPDXGenerator.generate(inventory)

        cdx_path = self.sbom_dir / "aegistrace-cyclonedx.json"
        spdx_path = self.sbom_dir / "aegistrace-spdx.json"

        with open(cdx_path, "w", encoding="utf-8") as f:
            json.dump(cyclonedx_doc, f, indent=2, sort_keys=True)

        with open(spdx_path, "w", encoding="utf-8") as f:
            json.dump(spdx_doc, f, indent=2, sort_keys=True)

        return {
            "cyclonedx": cdx_path,
            "spdx": spdx_path,
        }
