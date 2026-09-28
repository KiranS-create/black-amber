# AegisTrace Web Functionality & Multi-Format Audit Report

**Product:** AegisTrace (SIH26237)  
**Code Name:** Black Amber  
**Scope:** Complete Web Functionality Repair (File Upload, Multi-Format Ingestion, Backend Orchestration, Browser QA)  
**Status:** **AUDITED, REPAIRED, AND VERIFIED**

---

## 1. Executive Summary

A comprehensive architectural and functional audit of the AegisTrace web workstation revealed five core failure modes that prevented reliable file selection, document upload, and multi-format forensic processing:

1. **Native File Picker Inaccessibility:** The "Browse Files" buttons were rendered inside styled `<label>` elements without explicit IDs or with nested interactive SVG tags, causing click events to be intercepted or dropped across modern browser engines. Additionally, fallback button handlers attempted to use `document.getElementById(...)` on unmounted DOM nodes.
2. **Silent Re-Upload Suppression:** HTML file inputs did not reset their `input.value` upon change. Once a file was selected, selecting the same file a second time (or retrying after a failed upload) resulted in a silent no-op because the browser's native `onChange` event only fires when the file path string mutates.
3. **Frontend/Backend Port Misrouting & Permanent Offline Lockout:** Vite dev server is configured for port `3000`, while the backend FastAPI runs on port `8000`. The frontend API client previously checked `origin.includes(':5173')` to detect local dev mode, causing requests on port 3000 to default to `http://localhost:3000`, which returned Vite's HTML template instead of JSON. The resulting parse failure triggered `forceOffline(true)` in `App.tsx`, permanently locking the entire application into offline simulation mode.
4. **Leak Analysis Benchmark Interception:** In `apiService.analyzeLeak`, strings shorter than 50 characters were assumed to be mock benchmark IDs. Real uploaded leak IDs (e.g. `leak_82fa19_c40b`) were consequently intercepted and redirected to static demo mocks instead of hitting `POST /analyze`.
5. **Backend MIME Whitelist & Role Restrictions:** The backend security policy previously rejected non-PDF/image formats and lacked `operator` permissions on the `GET /leaks/{leak_id}/download` endpoint.

All five failure modes have been rigorously corrected with production-grade engineering (no demo hacks or mock workarounds).

---

## 2. Component-by-Component Audit & Fix Inventory

### 2.1. DocumentsTab (`apps/web/src/components/DocumentsTab.tsx`)
- **Issue:** Clicking "Browse Files" failed if outer label did not trigger input; selecting same file after error did nothing; limited to PDF/PNG/JPEG.
- **Remediation:**
  - Bound explicit `fileInputRef = useRef<HTMLInputElement>(null)`.
  - Added native `<button type="button" onClick={() => fileInputRef.current?.click()}>Browse Files</button>`.
  - Cleared `input.value = ''` immediately following file processing in `processSelectedFile`.
  - Expanded `SUPPORTED_FORMATS` and file `accept` attribute to canonical extensions: `.pdf,.docx,.pptx,.xlsx,.png,.jpg,.jpeg,.txt,.csv,.rtf,.odt,.ods,.odp,.zip,.json`.
  - Integrated live API upload with progress spinner, error banner, and automatic table re-fetch.

### 2.2. ReleaseTab (`apps/web/src/components/ReleaseTab.tsx`)
- **Issue:** In the release builder drawer, "Upload file" button was an unlinked label; uploaded file did not automatically populate the document selection dropdown.
- **Remediation:**
  - Added dedicated `releaseFileInputRef = useRef<HTMLInputElement>(null)`.
  - Replaced label with explicit button triggering `releaseFileInputRef.current?.click()`.
  - Reset `input.value = ''` upon selection.
  - Upon successful `apiService.uploadDocument` response, new `document_id` is automatically set in state, selected in the dropdown, and added to the documents list.

### 2.3. InvestigationsTab (`apps/web/src/components/InvestigationsTab.tsx`)
- **Issue:** Leaked artifact file picker only accepted images/PDFs; re-selecting file did not fire event.
- **Remediation:**
  - Expanded `accept` attribute to include canonical document and container formats.
  - Reset `fileInputRef.current.value = ''` in upload handler.

### 2.4. LeakAnalysisTab (`apps/web/src/components/LeakAnalysisTab.tsx`)
- **Issue:** Browse button was a styled label that failed to open the file dialog on several browsers; mock routing intercepted uploaded leak IDs.
- **Remediation:**
  - Bound `leakFileInputRef = useRef<HTMLInputElement>(null)` to hidden input.
  - Replaced label with native button calling `leakFileInputRef.current?.click()`.
  - Cleared `input.value = ''` after selection.
  - Updated API routing in `apiService.analyzeLeak` to route real `leak_` IDs directly to `POST /analyze`.

### 2.5. VerifyTab (`apps/web/src/components/VerifyTab.tsx`)
- **Issue:** Re-auditing an updated package did not re-trigger verification if the file name was unchanged.
- **Remediation:**
  - Added `e.target.value = ''` to `handleInputChange`.
  - Retained offline independent package auditing for signed `.zip` archives and `.json` manifests.

---

## 3. Backend & Security Remediation

### 3.1. Expanded Allowed MIME Types (`apps/api/config.py`)
Configured `allowed_mime_types` to recognize all Tier 1, Tier 2, and container formats:
- `application/pdf`, `image/png`, `image/jpeg`
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
- `application/vnd.openxmlformats-officedocument.presentationml.presentation` (PPTX)
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX)
- `text/plain` (TXT), `text/csv` (CSV), `application/rtf` (RTF)
- `application/vnd.oasis.opendocument.text` (ODT), `application/vnd.oasis.opendocument.spreadsheet` (ODS), `application/vnd.oasis.opendocument.presentation` (ODP)
- `application/zip`, `application/json`

### 3.2. Polyglot & MIME Sniffing (`security/defense.py` & `apps/api/security.py`)
- Updated `safe_mime_check` and `sniff_mime_type` to invoke `FormatDetector.identify_format(payload, filename=filename)`.
- Enforced strict fail-closed rejection of PE executables (`MZ`), Linux ELF binaries (`\x7fELF`), and active web scripts (`<script>`).

### 3.3. New Leak Listing Endpoint (`apps/api/routers/leaks.py`)
- Added `GET /leaks` endpoint returning `List[LeakMetadata]` scoped to the caller's tenant.
- Added `operator` role to `GET /leaks/{leak_id}/download` permissions.

### 3.4. Orchestrator Auto-Registration (`apps/api/orchestrator.py`)
- In `create_release`, when receiving `document_base64`, the orchestrator sniffs the payload format using `FormatDetector` and registers the document with the detected MIME type and caller tenant ID.

---

## 4. Verification & Automated Test Results

### 4.1. TypeScript Compilation & Frontend Bundle
- Command: `npm run build` in `apps/web`
- Result: **0 errors, 1969 modules transformed, dist/index.html & assets successfully generated.**

### 4.2. Multi-Format E2E Test Suite (`tests/e2e/test_web_upload_all_formats.py`)
- Command: `python -m pytest tests/e2e/test_web_upload_all_formats.py -v`
- Result: **29/29 PASSED (100% GREEN)**
  - All 12 formats tested for upload (`POST /documents`), metadata verification, byte-for-byte download, leak ingestion (`POST /leaks`), listing (`GET /leaks`), and download.
  - Multi-format release creation from uploaded document and inline base64 verified.
  - Malicious PE executable, Linux ELF binary, and active HTML script strictly rejected with 415/400.

### 4.3. API Regression Test Suite (`tests/api/` & `tests/test_api.py`)
- Results: **30/30 PASSED (100% GREEN)**
