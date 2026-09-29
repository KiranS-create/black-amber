export type ExperienceVariant = 'main' | 'alternate';

/**
 * Determines whether to serve the New Premium Minimal Main UI
 * or the Alternate Baseline UI based on current hostname, user preference, or query param.
 *
 * Rules:
 * - https://aegistrace.vercel.app -> 'main' (Main software user interface)
 * - https://aegistrace-kirans-create.vercel.app -> 'alternate' (Alternate domain)
 * - Query param `?variant=alternate` or `?variant=main` allows instant audit & testing.
 * - Persistent toggle in localStorage allows seamless 1-click switching on any domain.
 * - All other hosts (localhost, Vercel preview URLs) default to 'main'.
 */
export function getExperienceVariant(): ExperienceVariant {
  if (typeof window === 'undefined') {
    return 'main';
  }

  // 1. Explicit query parameter override (for testing & auditor side-by-side verification)
  try {
    const params = new URLSearchParams(window.location.search);
    const override = params.get('variant');
    if (override === 'alternate') return 'alternate';
    if (override === 'main') return 'main';
  } catch {
    // ignore search param parsing failure
  }

  // 2. Persistent user choice in localStorage
  try {
    const saved = localStorage.getItem('aegistrace_active_variant');
    if (saved === 'alternate' || saved === 'main') {
      return saved as ExperienceVariant;
    }
  } catch {
    // ignore localStorage access issues
  }

  // 3. Strict Hostname Matching
  const hostname = window.location.hostname.toLowerCase();

  // The Alternate Baseline Domain (kiran-vercel URL)
  if (hostname.includes('aegistrace-kirans-create.vercel.app')) {
    return 'alternate';
  }

  // The Main Workstation Domain
  if (hostname.includes('aegistrace.vercel.app')) {
    return 'main';
  }

  // Default to Main Domain Experience (localhost, preview URLs)
  return 'main';
}

/**
 * Instantly flips between the Main Software UI and Alternate UI,
 * persisting the choice in localStorage and updating URL state.
 */
export function setExperienceVariant(variant: ExperienceVariant): void {
  try {
    localStorage.setItem('aegistrace_active_variant', variant);
    const url = new URL(window.location.href);
    url.searchParams.set('variant', variant);
    window.location.href = url.toString();
  } catch {
    window.location.reload();
  }
}
