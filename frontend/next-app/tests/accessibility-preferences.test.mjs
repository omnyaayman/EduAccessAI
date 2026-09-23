import assert from "node:assert/strict";
import test from "node:test";
import {
  ACCESSIBILITY_STORAGE_KEY,
  applyAccessibilityPreferences,
  DEFAULT_ACCESSIBILITY_PREFERENCES,
  loadAccessibilityPreferences,
  resolveReducedMotion,
} from "../lib/accessibilityPreferences.mjs";

function mockClassList() {
  const classes = new Set();
  return {
    add: (name) => classes.add(name),
    toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name),
    contains: (name) => classes.has(name),
  };
}

test("defaults keep captions and visual support on, with narration and visual overrides off", () => {
  assert.deepEqual({ ...DEFAULT_ACCESSIBILITY_PREFERENCES }, {
    captions: true,
    audioDescription: false,
    visualCompanion: true,
    highContrast: false,
    largeText: false,
    reducedMotion: false,
  });
});

test("preferences persist, reload, and ignore obsolete or malformed fields", () => {
  const values = new Map();
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
  const settings = { ...DEFAULT_ACCESSIBILITY_PREFERENCES, captions: false, highContrast: true, reducedMotion: true };
  applyAccessibilityPreferences(settings, { root: { classList: mockClassList() }, storage, target: new EventTarget() });
  assert.deepEqual(loadAccessibilityPreferences(storage), settings);
  assert.equal(JSON.parse(values.get(ACCESSIBILITY_STORAGE_KEY)).screenReaderMode, undefined);

  values.set(ACCESSIBILITY_STORAGE_KEY, "{bad json");
  assert.deepEqual(loadAccessibilityPreferences(storage), DEFAULT_ACCESSIBILITY_PREFERENCES);
});

test("large text, contrast and reduced motion apply globally and clear when switched off", () => {
  const classList = mockClassList();
  const root = { classList };
  const target = new EventTarget();
  const settings = { ...DEFAULT_ACCESSIBILITY_PREFERENCES, highContrast: true, largeText: true, reducedMotion: true };
  applyAccessibilityPreferences(settings, { root, storage: null, target });
  for (const name of ["high-contrast", "text-large", "reduced-motion", "motion-preference-set"]) {
    assert.equal(classList.contains(name), true, `${name} should be applied`);
  }

  applyAccessibilityPreferences(DEFAULT_ACCESSIBILITY_PREFERENCES, { root, storage: null, target });
  for (const name of ["high-contrast", "text-large", "reduced-motion"]) {
    assert.equal(classList.contains(name), false, `${name} should clear when disabled`);
  }
});

test("captions, audio description, and visual companion changes reach lecture consumers", () => {
  const target = new EventTarget();
  let emitted;
  target.addEventListener("eduaccess:accessibility_update", (event) => { emitted = event.detail; });
  const settings = { ...DEFAULT_ACCESSIBILITY_PREFERENCES, captions: false, audioDescription: true, visualCompanion: false };
  applyAccessibilityPreferences(settings, { root: { classList: mockClassList() }, storage: null, target });
  assert.deepEqual(emitted, settings);
});

test("OS reduced-motion preference is used only as the initial fallback", () => {
  assert.equal(loadAccessibilityPreferences(null, true).reducedMotion, true);
  const storage = { getItem: () => JSON.stringify({ ...DEFAULT_ACCESSIBILITY_PREFERENCES, reducedMotion: false }) };
  assert.equal(loadAccessibilityPreferences(storage, true).reducedMotion, false);
});

test("explicit in-app motion preference overrides the operating-system setting", () => {
  assert.equal(resolveReducedMotion(true, false), true);
  assert.equal(resolveReducedMotion(false, true), false);
  assert.equal(resolveReducedMotion(undefined, true), true);
  assert.equal(resolveReducedMotion(undefined, false), false);
});
