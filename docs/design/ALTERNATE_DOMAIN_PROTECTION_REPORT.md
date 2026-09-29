# Alternate Domain Protection Report
**Project**: AegisTrace (SIH26237 — Black Amber)  
**Protected Alternate Domain**: `https://aegistrace.vercel.app`  
**Status**: 100% Unchanged, Fully Protected & Verified  

---

## 1. Compliance Guarantee

Per the explicit specification:
> **"THE ALTERNATE DOMAIN UI MUST NOT BE CHANGED. The Alternate Domain's layout, navigation, typography, colors, component styling, and behavior must remain 100% untouched."**

Strict architectural and runtime isolation has been enforced and verified across all code layers.

---

## 2. Technical Domain Isolation Architecture

The experience variant router in [`apps/web/src/variant.ts`](file:///c:/Projects/SIH26237/apps/web/src/variant.ts) executes hostname discrimination prior to component mounting:

```typescript
export function getExperienceVariant(): ExperienceVariant {
  if (typeof window === 'undefined') return 'main';
  
  // 1. Explicit query parameter override (audit & testing)
  const params = new URLSearchParams(window.location.search);
  const qVariant = params.get('variant');
  if (qVariant === 'alternate') return 'alternate';
  if (qVariant === 'main') return 'main';

  // 2. Strict Hostname Matching
  const host = window.location.hostname.toLowerCase();
  if (host === 'aegistrace.vercel.app') {
    return 'alternate';
  }

  // 3. Main Experience Default
  return 'main';
}
```

In [`apps/web/src/App.tsx`](file:///c:/Projects/SIH26237/apps/web/src/App.tsx), when `variant === 'alternate'`, the original unaltered component `<AppContent />` is rendered directly with its original styles, original navigation, original colors, and original layout:

```typescript
export function App() {
  const variant = getExperienceVariant();

  if (variant === 'main') {
    return <MainApp />;
  }

  // Alternate Domain Protected Path — completely untouched
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
```

---

## 3. Live Browser Verification

Using Playwright browser automation, `https://aegistrace.vercel.app` was navigated and audited post-deployment.

- **Title**: `AegisTrace`
- **Heading**: `AegisTrace` — "Sigma-powered analysis for your event logs"
- **Surface**: Center card with "Load Event Logs", "Browse file", "Use sample data", "Drop a log file here or browse."
- **Integrity**: Pixel-for-pixel match against the baseline screenshot captured prior to the overhaul. Zero style contamination from the Main domain CSS.
