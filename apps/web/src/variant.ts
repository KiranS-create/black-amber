export type ExperienceVariant = 'main' | 'alternate';

/**
 * Determines whether to serve the New Premium Minimal Main UI
 * or the Protected Baseline Alternate UI based on current hostname or query param.
 *
 * Rules:
 * - https://aegistrace.vercel.app -> 'alternate' (100% protected baseline)
 * - https://aegistrace-kirans-create.vercel.app -> 'main' (New minimal authored experience)
 * - Query param `?variant=alternate` or `?variant=main` allows instant local and staging testing.
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

  // 2. Strict Hostname Matching
  const hostname = window.location.hostname.toLowerCase();

  // The Protected Alternate Baseline Domain
  if (hostname === 'aegistrace.vercel.app') {
    return 'alternate';
  }

  // Default to Main Domain Experience
  return 'main';
}
