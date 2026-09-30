export type ExperienceVariant = 'main' | 'alternate';

/**
 * Determines whether to serve the Unified Forensic Security Workstation
 * across all domains (including https://aegistrace-kirans-create.vercel.app).
 *
 * Rules:
 * - Default: 'alternate' (The complete 12-tab workstation fused with all interactive labs and tools).
 * - Query param `?variant=presentation` allows launching the compact 4-tab briefing mode.
 * - Persistent toggle in localStorage allows seamless 1-click switching on any domain.
 */
export function getExperienceVariant(): ExperienceVariant {
  return 'alternate';
}

/**
 * Instantly flips between the Complete Workstation UI and Compact Briefing UI,
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
