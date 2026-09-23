"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import {
  Accessibility,
  Eye,
  Volume2,
  Tv,
  SunMoon,
  Type,
  Activity,
  Keyboard,
  X,
  Check,
} from "lucide-react";
import { cn } from "@/lib/format";
import {
  applyAccessibilityPreferences,
  DEFAULT_ACCESSIBILITY_PREFERENCES,
  loadAccessibilityPreferences,
} from "@/lib/accessibilityPreferences.mjs";
import type { AccessibilityPreferences } from "@/lib/accessibilityPreferences.mjs";

function safeLocalStorage(): Storage | null {
  try { return window.localStorage; } catch { return null; }
}

export default function AccessibilityToolbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [settings, setSettings] = useState<AccessibilityPreferences>({ ...DEFAULT_ACCESSIBILITY_PREFERENCES });

  // Load from localStorage on mount
  useEffect(() => {
    setSettings(loadAccessibilityPreferences(
      safeLocalStorage(),
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ));
  }, []);

  // Persist and apply every preference consistently for the app and lecture consumers.
  useEffect(() => {
    applyAccessibilityPreferences(settings, {
      root: document.documentElement,
      storage: safeLocalStorage(),
      target: window,
    });
  }, [settings]);

  const toggleSetting = (key: keyof AccessibilityPreferences) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <>
      {/* Floating Toolbar Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Accessibility Settings Toolbar"
        aria-expanded={isOpen}
        aria-controls="eduaccess-accessibility-panel"
        className="eduaccess-accessibility-trigger fixed bottom-6 left-6 z-40 flex size-12 items-center justify-center rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] text-[#51483F] shadow-sm transition-all hover:border-[#B85C38]/60 hover:text-[#B85C38] hover:shadow-md focus:outline-none focus:ring-4 focus:ring-[#B85C38]/20 cursor-pointer"
      >
        <Accessibility className="size-5" />
      </button>

      {/* Accessibility Settings Popover */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="Accessibility Preferences"
          aria-modal="false"
          id="eduaccess-accessibility-panel"
          className="eduaccess-accessibility-panel fixed bottom-20 left-6 z-40 w-72 sm:w-80 rounded-3xl border border-[#E4D9CC] bg-[#FFFDFC]/95 p-4 shadow-xl backdrop-blur-xl transition-all text-[#2F2924]"
        >
          <div className="flex items-center justify-between border-b border-[#E7DED2] pb-3">
            <div>
              <div className="flex items-center gap-2">
                <Accessibility className="size-4 text-[#B85C38]" />
                <h3 className="text-sm font-bold text-[#2F2924]">Accessibility Preferences</h3>
              </div>
              <p className="text-[10.5px] text-[#7A7067] mt-0.5">WCAG-informed accessibility features</p>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label="Close Accessibility toolbar"
              className="rounded-lg p-1 text-[#7A7067] hover:text-[#2F2924] hover:bg-[#F1E8DC] transition-colors cursor-pointer"
            >
              <X className="size-4" />
            </button>
          </div>

          <div className="mt-3 space-y-1.5">
            <label title="Show synchronized transcript text while a lecture plays, when transcript data is available." className="flex items-center justify-between p-2 rounded-xl hover:bg-[#F1E8DC]/60 cursor-pointer transition">
              <div className="flex items-center gap-2.5 text-xs font-semibold text-[#51483F]">
                <Eye className="size-4 text-[#5F9A9A]" />
                Captions
              </div>
              <input
                type="checkbox"
                checked={settings.captions}
                onChange={() => toggleSetting("captions")}
                className="size-4 rounded border-[#DDD0C0] text-[#B85C38] focus:ring-[#B85C38] accent-[#B85C38] cursor-pointer"
              />
            </label>

            <label title="Play available synchronized visual narration during the lecture." className="flex items-center justify-between p-2 rounded-xl hover:bg-[#F1E8DC]/60 cursor-pointer transition">
              <div className="flex items-center gap-2.5 text-xs font-semibold text-[#51483F]">
                <Volume2 className="size-4 text-[#5F8A62]" />
                Audio Description
              </div>
              <input
                type="checkbox"
                checked={settings.audioDescription}
                onChange={() => toggleSetting("audioDescription")}
                className="size-4 rounded border-[#DDD0C0] text-[#B85C38] focus:ring-[#B85C38] accent-[#B85C38] cursor-pointer"
              />
            </label>

            <label title="Show grounded descriptions and OCR from the current lecture visuals." className="flex items-center justify-between p-2 rounded-xl hover:bg-[#F1E8DC]/60 cursor-pointer transition">
              <div className="flex items-center gap-2.5 text-xs font-semibold text-[#51483F]">
                <Tv className="size-4 text-[#6C63A8]" />
                Visual Companion
              </div>
              <input
                type="checkbox"
                checked={settings.visualCompanion}
                onChange={() => toggleSetting("visualCompanion")}
                className="size-4 rounded border-[#DDD0C0] text-[#B85C38] focus:ring-[#B85C38] accent-[#B85C38] cursor-pointer"
              />
            </label>

            <div className="border-t border-[#E7DED2] my-1.5" />

            <label className="flex items-center justify-between p-2 rounded-xl hover:bg-[#F1E8DC]/60 cursor-pointer transition">
              <div className="flex items-center gap-2.5 text-xs font-semibold text-[#51483F]">
                <SunMoon className="size-4 text-[#C49A5A]" />
                High Contrast
              </div>
              <input
                type="checkbox"
                checked={settings.highContrast}
                onChange={() => toggleSetting("highContrast")}
                className="size-4 rounded border-[#DDD0C0] text-[#B85C38] focus:ring-[#B85C38] accent-[#B85C38] cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between p-2 rounded-xl hover:bg-[#F1E8DC]/60 cursor-pointer transition">
              <div className="flex items-center gap-2.5 text-xs font-semibold text-[#51483F]">
                <Type className="size-4 text-[#5B82A6]" />
                Large Text
              </div>
              <input
                type="checkbox"
                checked={settings.largeText}
                onChange={() => toggleSetting("largeText")}
                className="size-4 rounded border-[#DDD0C0] text-[#B85C38] focus:ring-[#B85C38] accent-[#B85C38] cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between p-2 rounded-xl hover:bg-[#F1E8DC]/60 cursor-pointer transition">
              <div className="flex items-center gap-2.5 text-xs font-semibold text-[#51483F]">
                <Activity className="size-4 text-[#B94A48]" />
                Reduced Motion
              </div>
              <input
                type="checkbox"
                checked={settings.reducedMotion}
                onChange={() => toggleSetting("reducedMotion")}
                className="size-4 rounded border-[#DDD0C0] text-[#B85C38] focus:ring-[#B85C38] accent-[#B85C38] cursor-pointer"
              />
            </label>

            <p className="px-2 py-1 text-[11px] leading-relaxed text-[#7A7067]" role="note">
              Screen readers use your browser and device settings. EduAccess controls work with standard assistive technology.
            </p>

            <button
              type="button"
              onClick={() => setShowShortcuts(true)}
              className="w-full mt-2 flex items-center justify-center gap-2 rounded-xl border border-[#DDD0C0] bg-[#FBF8F2] py-2 text-xs font-bold text-[#51483F] hover:bg-[#F1E8DC] transition cursor-pointer"
            >
              <Keyboard className="size-3.5 text-[#B85C38]" /> Keyboard Shortcuts (?)
            </button>
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts Dialog */}
      {showShortcuts && (
        <div
          role="dialog"
          aria-label="Keyboard Shortcuts"
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#2F2924]/40 backdrop-blur-xs p-4"
        >
          <div className="relative w-full max-w-md rounded-3xl border border-[#E4D9CC] bg-[#FFFDFC] p-6 shadow-2xl text-[#2F2924]">
            <div className="flex items-center justify-between border-b border-[#E7DED2] pb-3">
              <div className="flex items-center gap-2">
                <Keyboard className="size-5 text-[#B85C38]" />
                <h3 className="text-base font-bold text-[#2F2924]">Accessible Shortcuts</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowShortcuts(false)}
                aria-label="Close shortcuts"
                className="rounded-lg p-1 text-[#7A7067] hover:text-[#2F2924] hover:bg-[#F1E8DC] cursor-pointer"
              >
                <X className="size-5" />
              </button>
            </div>

            <div className="mt-4 space-y-2.5 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-[#E7DED2]">
                <span className="text-[#51483F]">Play / Pause Video</span>
                <kbd className="rounded-md bg-[#F1E8DC] border border-[#DDD0C0] px-2 py-0.5 font-mono font-bold text-[#2F2924]">Space</kbd>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-[#E7DED2]">
                <span className="text-[#51483F]">Seek 5s Forward / Backward</span>
                <kbd className="rounded-md bg-[#F1E8DC] border border-[#DDD0C0] px-2 py-0.5 font-mono font-bold text-[#2F2924]">← / →</kbd>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-[#E7DED2]">
                <span className="text-[#51483F]">Toggle Captions</span>
                <kbd className="rounded-md bg-[#F1E8DC] border border-[#DDD0C0] px-2 py-0.5 font-mono font-bold text-[#2F2924]">C</kbd>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-[#E7DED2]">
                <span className="text-[#51483F]">Toggle Audio Description</span>
                <kbd className="rounded-md bg-[#F1E8DC] border border-[#DDD0C0] px-2 py-0.5 font-mono font-bold text-[#2F2924]">A</kbd>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-[#E7DED2]">
                <span className="text-[#51483F]">Toggle Visual Companion</span>
                <kbd className="rounded-md bg-[#F1E8DC] border border-[#DDD0C0] px-2 py-0.5 font-mono font-bold text-[#2F2924]">V</kbd>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-[#51483F]">Open this Shortcuts Dialog</span>
                <kbd className="rounded-md bg-[#F1E8DC] border border-[#DDD0C0] px-2 py-0.5 font-mono font-bold text-[#2F2924]">?</kbd>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
