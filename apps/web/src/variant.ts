export type ExperienceVariant = 'main' | 'alternate';

/**
 * Determines whether to serve the Unified Forensic Security Workstation
 * or the Executive Presentation / Briefing mode.
 *
 * Switching Logic:
 * - https://aegistrace.vercel.app -> 'alternate' (Executive Presentation / Briefing mode)
 * - https://aegistrace-kirans-create.vercel.app -> 'main' (Main Workstation)
 * - Explicit ?variant=main or ?variant=alternate overrides hostname for testing
 * - Localhost / default defaults to 'main'
 */
export function getExperienceVariant(): ExperienceVariant {
  if (typeof window === 'undefined') return 'main';

  // 1. Explicit query parameter override (audit & testing)
  try {
    const params = new URLSearchParams(window.location.search);
    const qVariant = params.get('variant');
    if (qVariant === 'main') return 'main';
    if (qVariant === 'alternate') return 'alternate';

    // 2. Saved user preference in localStorage
    const saved = localStorage.getItem('aegistrace_active_variant') as ExperienceVariant;
    if (saved === 'main' || saved === 'alternate') {
      return saved;
    }
  } catch {
    // ignore
  }

  // 3. Hostname Switching
  const host = window.location.hostname.toLowerCase();
  if (host === 'aegistrace-kirans-create.vercel.app') {
    return 'main';
  }
  if (host === 'aegistrace.vercel.app') {
    return 'alternate';
  }

  return 'main';
}

/**
 * Instantly flips between the Workstation UI and Briefing UI,
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
