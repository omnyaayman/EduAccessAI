export const ACCESSIBILITY_STORAGE_KEY = "eduaccess_accessibility_settings";

export const DEFAULT_ACCESSIBILITY_PREFERENCES = Object.freeze({
  captions: true,
  audioDescription: false,
  visualCompanion: true,
  highContrast: false,
  largeText: false,
  reducedMotion: false,
});

const preferenceKeys = Object.keys(DEFAULT_ACCESSIBILITY_PREFERENCES);

export function loadAccessibilityPreferences(storage, prefersReducedMotion = false) {
  const defaults = {
    ...DEFAULT_ACCESSIBILITY_PREFERENCES,
    reducedMotion: Boolean(prefersReducedMotion),
  };
  try {
    const stored = storage?.getItem(ACCESSIBILITY_STORAGE_KEY);
    if (!stored) return defaults;
    const parsed = JSON.parse(stored);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return defaults;
    return Object.fromEntries(preferenceKeys.map((key) => [
      key,
      typeof parsed[key] === "boolean" ? parsed[key] : defaults[key],
    ]));
  } catch {
    return defaults;
  }
}

export function resolveReducedMotion(userPreference, systemPreference) {
  return userPreference == null ? Boolean(systemPreference) : Boolean(userPreference);
}

export function applyAccessibilityPreferences(settings, { root, storage, target }) {
  try {
    storage?.setItem(ACCESSIBILITY_STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Preferences still apply for this session if storage is unavailable.
  }

  root.classList.toggle("high-contrast", settings.highContrast);
  root.classList.toggle("text-large", settings.largeText);
  root.classList.toggle("reduced-motion", settings.reducedMotion);
  root.classList.add("motion-preference-set");
  target.dispatchEvent(new CustomEvent("eduaccess:accessibility_update", { detail: settings }));
}
