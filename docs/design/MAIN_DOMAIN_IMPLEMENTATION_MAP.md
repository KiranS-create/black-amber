# AegisTrace Main Domain Implementation Map

This document maps the architectural code modifications, file paths, and component boundaries implementing the Main Domain UI overhaul while preserving the protected Alternate Domain baseline.

---

## 1. Domain Separation Architecture

| File Path | Role | Description |
| :--- | :--- | :--- |
| `apps/web/src/variant.ts` | Host Detection | Inspects `window.location.hostname` and query params to switch between `'main'` and `'alternate'`. |
| `apps/web/src/App.tsx` | Root Component | Renders `<MainApp />` when variant is `'main'`, or `<AlternateApp />` when variant is `'alternate'`. |
| `apps/web/src/components/alternate/AlternateApp.tsx` | Protected Baseline | Existing implementation with 12 sidebar tabs, 100% preserved. |
| `apps/web/src/components/main/*` | New Main UI | Premium, minimal, authored forensic experience. |
| `apps/web/src/styles/main-experience.css` | Scoped Styling | Clean tokens, restrained typography, zero neon. |

---

## 2. Main Domain Component Inventory

```
apps/web/src/components/main/
├── MainApp.tsx                      # Root shell for Main experience; manages state & data fetching
├── MainSidebar.tsx                  # 4-item slim sidebar (Overview, Documents, Investigations, Evidence) + Settings trigger
├── MainHeader.tsx                   # Minimal header with breadcrumb, DEMO DATA pill, user avatar & sign out
├── MainOverview.tsx                 # Command center view: workspace health, quick stats, active cases
├── MainDocuments.tsx                # Content-addressed registry, file dropzone, native Browse Files input
├── MainDocumentDrawer.tsx           # Contextual drawer for document inspection, Protect, Release, & technical details
├── MainInvestigations.tsx           # Forensic workstation: leak intake, Bayesian suspect attribution finding card
├── MainEvidence.tsx                 # Evidence examination, signed ZIP export, and built-in offline verifier
├── MainSettingsModal.tsx            # Contextual modal for Enrolled Principals, Directory, Ledger, and System
└── MainLogin.tsx                    # Minimal authored login screen with discreet demo autofill
```

---

## 3. Data & API Service Continuity

All components in `apps/web/src/components/main/` interface directly with the existing `apiService` in [`apps/web/src/services/api.ts`](file:///c:/Projects/SIH26237/apps/web/src/services/api.ts):
- `apiService.login(username, password)`
- `apiService.getDocuments()`, `apiService.uploadDocument(file, name)`
- `apiService.getRecipients()`, `apiService.createRelease(req)`
- `apiService.ingestLeak(file)`, `apiService.analyzeLeak(req)`
- `apiService.getLedgerEvents()`, `apiService.verifyLedger()`
- `apiService.verifyEvidencePackage(bytes)`

Zero backend APIs are altered. Zero cryptographic protocols are duplicated.
