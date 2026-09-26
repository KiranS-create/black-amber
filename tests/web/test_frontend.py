import os
import json
import re
import pytest

WEB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "web"))
DOCS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
RESEARCH_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "research", "frontend"))
ARTIFACTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "frontend"))

def test_web_package_json():
    pkg_path = os.path.join(WEB_ROOT, "package.json")
    assert os.path.exists(pkg_path), "apps/web/package.json must exist"
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    assert pkg.get("name") == "sih26237-web"
    assert "react" in pkg.get("dependencies", {})
    assert "lucide-react" in pkg.get("dependencies", {})
    assert "vite" in pkg.get("devDependencies", {})

def test_web_components_exist():
    components_dir = os.path.join(WEB_ROOT, "src", "components")
    expected_components = [
        "Header.tsx",
        "DashboardTab.tsx",
        "RecipientsTab.tsx",
        "ReleaseTab.tsx",
        "DecryptionTab.tsx",
        "LedgerTab.tsx",
        "LeakAnalysisTab.tsx",
        "AttackLabTab.tsx",
        "TardosVisualizer.tsx",
        "JudgeWalkthroughModal.tsx",
        "ForensicReportModal.tsx"
    ]
    for comp in expected_components:
        comp_path = os.path.join(components_dir, comp)
        assert os.path.exists(comp_path), f"Component {comp} must exist in apps/web/src/components"

def test_web_services_exist():
    services_dir = os.path.join(WEB_ROOT, "src", "services")
    assert os.path.exists(os.path.join(services_dir, "api.ts")), "api.ts must exist"
    assert os.path.exists(os.path.join(services_dir, "mockData.ts")), "mockData.ts must exist"

def test_frontend_documentation_files():
    assert os.path.exists(os.path.join(DOCS_ROOT, "FRONTEND_DESIGN.md")), "docs/FRONTEND_DESIGN.md must exist"
    assert os.path.exists(os.path.join(RESEARCH_ROOT, "JUDGE_EXPERIENCE_ANALYSIS.md")), "research/frontend/JUDGE_EXPERIENCE_ANALYSIS.md must exist"
    assert os.path.exists(os.path.join(ARTIFACTS_ROOT, "DEMO_SCRIPT.md")), "artifacts/frontend/DEMO_SCRIPT.md must exist"
    assert os.path.exists(os.path.join(ARTIFACTS_ROOT, "E2E_DEMO_RUNBOOK.md")), "artifacts/frontend/E2E_DEMO_RUNBOOK.md must exist"

def test_mock_data_scenarios():
    mock_data_path = os.path.join(WEB_ROOT, "src", "services", "mockData.ts")
    with open(mock_data_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify core post-quantum algorithms referenced
    assert "ML-KEM-768" in content
    assert "ML-DSA-65" in content
    assert "AES-256-GCM" in content
    assert "Tardos" in content
    assert "clean_bob" in content
    assert "forged_hmac" in content
    assert "framed_identity" in content
    assert "print_scan_camera" in content
    assert "evidence_conflict_bob_charlie" in content
    assert "review_required_anomaly" in content

def test_hash_isolation_types():
    types_path = os.path.join(WEB_ROOT, "src", "types.ts")
    with open(types_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify isolated hashes exist and are not collapsed
    assert "original_document_hash" in content
    assert "traceable_artifact_hash" in content
    assert "leak_artifact_hash" in content

def test_data_source_origins():
    types_path = os.path.join(WEB_ROOT, "src", "types.ts")
    with open(types_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "DataSourceOrigin" in content
    assert "REAL_BACKEND_RESULT" in content
    assert "REAL_LOCAL_COMPUTATION" in content
    assert "SIMULATED_DEMO_SCENARIO" in content
    assert "PLACEHOLDER_UNAVAILABLE" in content

def test_fail_closed_states():
    types_path = os.path.join(WEB_ROOT, "src", "types.ts")
    with open(types_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "ATTRIBUTED" in content
    assert "NO_SIGNAL" in content
    assert "INSUFFICIENT_EVIDENCE" in content
    assert "CONFLICT" in content
    assert "REVIEW_REQUIRED" in content
    assert "ABSTAINED" in content
    assert "FAILED" in content

def test_watermark_states_and_modes():
    types_path = os.path.join(WEB_ROOT, "src", "types.ts")
    with open(types_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "WatermarkStatusType" in content
    assert "RECOVERED" in content
    assert "PARTIAL" in content
    assert "NO_SIGNAL" in content
    assert "INVALID" in content
    assert "UNAVAILABLE" in content
    assert "'PHYSICAL' | 'SIMULATED'" in content

def test_provenance_verification_states():
    types_path = os.path.join(WEB_ROOT, "src", "types.ts")
    with open(types_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "ProvenanceVerificationStatusType" in content
    assert "RECIPIENT_SIGNED_VERIFIED" in content
    assert "SIMULATED_RECIPIENT_ACTION" in content

def test_api_contract_methods():
    api_path = os.path.join(WEB_ROOT, "src", "services", "api.ts")
    with open(api_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify all REST API endpoints from docs/INTEGRATION_DESIGN.md are mapped
    assert "POST /documents" in content or "/documents" in content
    assert "POST /recipients" in content or "/recipients" in content
    assert "POST /releases" in content or "/releases" in content
    assert "POST /leaks" in content or "/leaks" in content
    assert "POST /analyze" in content or "/analyze" in content
    assert "GET /ledger/verify" in content or "/ledger/verify" in content
    assert "submitReleaseProvenance" in content
    assert "submitDecryptionEvent" in content

def test_no_overclaiming_in_frontend():
    src_dir = os.path.join(WEB_ROOT, "src")
    forbidden_patterns = [
        re.compile(r"NIST\s+certified", re.IGNORECASE),
        re.compile(r"ENFSI\s+certified", re.IGNORECASE),
        re.compile(r"zero\s+false\s+accusations", re.IGNORECASE),
        re.compile(r"legally\s+admissible", re.IGNORECASE),
        re.compile(r"100%\s+security", re.IGNORECASE),
    ]
    
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".ts", ".tsx")):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                for pattern in forbidden_patterns:
                    matches = pattern.findall(content)
                    assert len(matches) == 0, f"Found forbidden overclaim '{matches}' in {file_path}"
