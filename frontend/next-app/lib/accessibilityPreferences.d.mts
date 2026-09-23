export interface AccessibilityPreferences {
  captions: boolean;
  audioDescription: boolean;
  visualCompanion: boolean;
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
}

export const ACCESSIBILITY_STORAGE_KEY: string;
export const DEFAULT_ACCESSIBILITY_PREFERENCES: Readonly<AccessibilityPreferences>;
export function loadAccessibilityPreferences(
  storage: Pick<Storage, "getItem"> | null,
  prefersReducedMotion?: boolean
): AccessibilityPreferences;
export function resolveReducedMotion(userPreference: boolean | null | undefined, systemPreference: boolean | null): boolean;
export function applyAccessibilityPreferences(
  settings: AccessibilityPreferences,
  options: { root: HTMLElement; storage: Pick<Storage, "setItem"> | null; target: Window }
): void;
