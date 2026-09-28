# AegisTrace Design Implementation Mapping

This document provides the technical bridge between Google Stitch screen specifications and the production React application code, detailing components, state stores, and backend endpoints.

---

## Screen to Implementation Matrix

| Stitch Screen | React Component | API Endpoint / Service | Backend Semantic Service |
| :--- | :--- | :--- | :--- |
| **1. Workstation Sign-In** | `LoginScreen.tsx` | `POST /auth/login` | `apiService.login()` |
| **2. Workspace Registration** | `SignUpScreen.tsx` | `POST /auth/register` | `apiService.register()` |
| **3. Operational Overview** | `OverviewTab.tsx` | `GET /health`, `GET /documents` | `apiService.checkHealth()` |
| **4. Document Registry** | `DocumentsTab.tsx` | `GET /documents` | `apiService.getDocuments()` |
| **5. Document Import** | `DocumentsTab.tsx` | `POST /documents/upload` | `apiService.uploadDocument()` |
| **6. Document Inspector** | `Drawer.tsx` | Local State + `GET /documents/{id}` | `DocumentMetadata` |
| **7. Protection Pipeline** | `ReleaseTab.tsx` | `POST /releases/create` | `apiService.createRelease()` |
| **8. Releases & Distribution** | `ReleaseTab.tsx` | `GET /releases` | `apiService.getReleases()` |
| **9. Recipient Identity** | `RecipientsTab.tsx` | `GET /recipients` | `apiService.getRecipients()` |
| **10. Directory** | `DirectoryTab.tsx` | `GET /directory` | `apiService.getDirectoryIdentities()` |
| **11. Investigation Workstation** | `InvestigationsTab.tsx` | `POST /leaks/analyze` | `apiService.analyzeLeak()` |
| **12. Investigation LLR Inspector**| `Drawer.tsx` | `GET /leaks/{id}/llr` | `AttributionResult` |
| **13. Evidence Examination** | `EvidenceTab.tsx` | `GET /evidence` | `apiService.getEvidenceRecords()` |
| **14. AegisTrace Verify** | `VerifyTab.tsx` | `POST /verify/package` | `VerificationService.verifyPackage()` |
| **15. Provenance DAG** | `ProvenanceTab.tsx` | Local Lineage Model | `core/lineage/` |
| **16. Audit Ledger** | `LedgerTab.tsx` | `GET /ledger/events` | `apiService.getLedgerEvents()` |
| **17. System Health** | `SystemHealthTab.tsx` | `GET /health/capabilities` | `apiService.getCapabilities()` |

---

## State Isolation & Epistemic Boundaries
* **Production vs Demo Mode:** Production mode starts completely clean (0 pre-populated fake documents or simulated leaks). When `DEMO_AUTH_ENABLED=true` is activated, synthetic demonstration cases are clearly watermarked as `DEMO DATA` with an explicit reset option calling the real backend purge endpoint.
* **Tier-1 Format Acceptance:** Native file pickers in `DocumentsTab.tsx`, `InvestigationsTab.tsx`, and `VerifyTab.tsx` accept `.pdf, .docx, .pptx, .xlsx, .png, .jpg, .jpeg` and route to `MultiFormatForensicOrchestrator` on the server.
