"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import {
  Video,
  Mic,
  Eye,
  ScanText,
  GitCompareArrows,
  AlertTriangle,
  Volume2,
  BrainCircuit,
  ShieldCheck,
  Cpu,
  Activity,
  Layers,
  Sparkles,
  Play,
  RotateCw,
  Sliders,
  CheckCircle2,
} from "lucide-react";
import { cn, formatClock } from "@/lib/format";

export interface CompilerPipelineStage {
  id: string;
  step: string;
  label: string;
  subtitle: string;
  category: "input" | "decompile" | "alignment" | "reasoning" | "remediation" | "twin";
  icon: typeof Video;
  color: string;
  glow: string;
  ring: string;
  textColor: string;
  pulseClass: string;
  telemetry: {
    title: string;
    timestamp: string;
    metrics: string;
    detail: string;
    code?: string;
    spoken?: string;
    action?: string;
  };
}

export const COMPILER_STAGES: CompilerPipelineStage[] = [
  {
    id: "video",
    step: "01",
    label: "Raw Educational Video",
    subtitle: "MP4 Ingestion & Frame Demuxing",
    category: "input",
    icon: Video,
    color: "from-[#B94A48]/20 to-[#9F4F32]/20 border-[#B94A48]/40 text-[#E8C2B2]",
    glow: "rgba(185, 74, 72, 0.2)",
    ring: "ring-[#B94A48]/30",
    textColor: "text-[#E8C2B2]",
    pulseClass: "pulse-critical",
    telemetry: {
      title: "Input Stream: DEMO_python_loops.mp4",
      timestamp: "00:00.0 → 00:28.0",
      metrics: "1080p · 30 FPS · Stereo 44.1kHz",
      detail: "Demuxed 28.0s Python Loops lecture with synchronized stereo audio & 30fps frames.",
    },
  },
  {
    id: "speech",
    step: "02",
    label: "Whisper STT Transcription",
    subtitle: "Timestamped Speech Tokens",
    category: "decompile",
    icon: Mic,
    color: "from-[#5B82A6]/20 to-[#466B8A]/20 border-[#5B82A6]/40 text-[#8DB4D6]",
    glow: "rgba(91, 130, 166, 0.2)",
    ring: "ring-[#5B82A6]/30",
    textColor: "text-[#8DB4D6]",
    pulseClass: "pulse-speech",
    telemetry: {
      title: "Whisper STT Acoustic Model",
      timestamp: "00:26.4 → 00:34.1",
      metrics: "24 segments · Word-level stamps",
      spoken: "“...as we move through the loop, each item is printed in turn.”",
      detail: "Deterministic word-level transcription with confidence scoring (avg 0.96).",
    },
  },
  {
    id: "vision",
    step: "03",
    label: "Visual Understanding",
    subtitle: "Keyframe Detection & Slide Segments",
    category: "decompile",
    icon: Eye,
    color: "from-[#5F9A9A]/20 to-[#46716F]/20 border-[#5F9A9A]/40 text-[#8EC5C5]",
    glow: "rgba(95, 154, 154, 0.2)",
    ring: "ring-[#5F9A9A]/30",
    textColor: "text-[#8EC5C5]",
    pulseClass: "pulse-vision",
    telemetry: {
      title: "Keyframe Segmentation Engine",
      timestamp: "00:26.0s (Keyframe #04)",
      metrics: "14 Keyframes · 0.98 Visual Confidence",
      detail: "Slide transition detected with code terminal layout and syntax highlight regions.",
    },
  },
  {
    id: "ocr",
    step: "04",
    label: "OCR Syntax Extraction",
    subtitle: "Tesseract Code & Diagram OCR",
    category: "decompile",
    icon: ScanText,
    color: "from-[#5F9A9A]/20 to-[#5B82A6]/20 border-[#5F9A9A]/40 text-[#8EC5C5]",
    glow: "rgba(95, 154, 154, 0.25)",
    ring: "ring-[#5F9A9A]/30",
    textColor: "text-[#8EC5C5]",
    pulseClass: "pulse-vision",
    telemetry: {
      title: "Extracted Code Syntax Block",
      timestamp: "00:26.0s",
      metrics: "98.4% OCR Confidence",
      code: 'fruits = ["apple", "banana", "cherry"]\nfor fruit in fruits:\n    print(fruit)',
      detail: "Identified list variable assignment, for-in loop header, and indented body print statement.",
    },
  },
  {
    id: "align",
    step: "05",
    label: "Cross-Modal Alignment",
    subtitle: "Temporal Synchronization Matrix",
    category: "alignment",
    icon: GitCompareArrows,
    color: "from-[#B85C38]/20 to-[#9F4F32]/20 border-[#B85C38]/40 text-[#E8C2B2]",
    glow: "rgba(184, 92, 56, 0.25)",
    ring: "ring-[#B85C38]/30",
    textColor: "text-[#E8C2B2]",
    pulseClass: "pulse-ai",
    telemetry: {
      title: "Temporal Sync Matrix",
      timestamp: "Δt = 0.4s sync window",
      metrics: "±0.1s Cross-Modal Alignment",
      detail: "Synchronized speech token stream [00:26–00:34] with visual code keyframe [00:26].",
    },
  },
  {
    id: "reason",
    step: "06",
    label: "AI Reasoning Engine",
    subtitle: "Shown vs Spoken Comparison",
    category: "reasoning",
    icon: Cpu,
    color: "from-[#6C63A8]/20 to-[#554F86]/20 border-[#6C63A8]/40 text-[#AAA4D1]",
    glow: "rgba(108, 99, 168, 0.25)",
    ring: "ring-[#6C63A8]/30",
    textColor: "text-[#AAA4D1]",
    pulseClass: "pulse-ai",
    telemetry: {
      title: "Cross-Modal Disparity Analysis",
      timestamp: "00:26.0s",
      metrics: "Shown vs Said Mismatch: 0.88",
      detail: "Speaker describes high-level loop execution without reading syntax `for fruit in fruits:` verbally.",
    },
  },
  {
    id: "gap",
    step: "07",
    label: "Disparity Engine (Gap)",
    subtitle: "Critical Accessibility Gap Flagged",
    category: "reasoning",
    icon: AlertTriangle,
    color: "from-[#B77932]/20 to-[#8A5A25]/20 border-[#B77932]/40 text-[#E6AA68]",
    glow: "rgba(183, 121, 50, 0.25)",
    ring: "ring-[#B77932]/30",
    textColor: "text-[#E6AA68]",
    pulseClass: "pulse-gap",
    telemetry: {
      title: "Accessibility Gap #03 Flagged",
      timestamp: "00:26.0s",
      metrics: "Severity: HIGH (Visual Syntax Omission)",
      detail: "Blind / visually impaired student lacks critical loop syntax required for comprehension.",
    },
  },
  {
    id: "remediation",
    step: "08",
    label: "Audio Description Studio",
    subtitle: "Non-Destructive Dual Audio",
    category: "remediation",
    icon: Volume2,
    color: "from-[#5F8A62]/20 to-[#416A47]/20 border-[#5F8A62]/40 text-[#8FC493]",
    glow: "rgba(95, 138, 98, 0.25)",
    ring: "ring-[#5F8A62]/30",
    textColor: "text-[#8FC493]",
    pulseClass: "pulse-verified",
    telemetry: {
      title: "Synthesized Audio Description Cue #03",
      timestamp: "00:26.2 → 00:30.5",
      metrics: "6 Real AD Cues · Layered Track",
      action: "“On screen: for fruit in fruits colon, indent print fruit.” (Preserving original speaker audio)",
      detail: "Injected synchronized AD narration without altering original lecture audio track.",
    },
  },
  {
    id: "twin",
    step: "09",
    label: "Accessibility Twin",
    subtitle: "Compiled Structured Representation",
    category: "twin",
    icon: BrainCircuit,
    color: "from-[#B85C38]/25 to-[#6C63A8]/25 border-[#B85C38]/50 text-[#E8C2B2]",
    glow: "rgba(184, 92, 56, 0.3)",
    ring: "ring-[#B85C38]/40",
    textColor: "text-[#E8C2B2]",
    pulseClass: "pulse-ai",
    telemetry: {
      title: "Compiled Accessibility Twin Model",
      timestamp: "Full Lecture Graph Ready",
      metrics: "100% Health Potential · 10 Connected Nodes",
      detail: "Deterministic multi-layered model uniting Video, Speech, Vision, OCR, Gaps, AD, Concepts, & Quiz.",
    },
  },
];

export default function HeroCompilerVisual() {
  const [activeIdx, setActiveIdx] = useState<number>(0);
  const [isAutoCycling, setIsAutoCycling] = useState<boolean>(true);

  useEffect(() => {
    if (!isAutoCycling) return;
    const interval = setInterval(() => {
      setActiveIdx((prev) => (prev + 1) % COMPILER_STAGES.length);
    }, 3200);
    return () => clearInterval(interval);
  }, [isAutoCycling]);

  const active = COMPILER_STAGES[activeIdx];
  const ActiveIcon = active.icon;

  return (
    <div
      onMouseEnter={() => setIsAutoCycling(false)}
      onMouseLeave={() => setIsAutoCycling(true)}
      className="scientific-lens relative w-full overflow-hidden p-4 sm:p-6 text-[#FFF8F0] select-none transition-all duration-500"
      style={{
        boxShadow: `0 20px 45px rgba(63, 53, 46, 0.22), 0 0 30px ${active.glow}`,
      }}
    >
      {/* Background Matrix Grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-15"
        aria-hidden
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(232,194,178,0.15) 1px, transparent 1px), linear-gradient(to bottom, rgba(232,194,178,0.15) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* Radial soft illumination */}
      <div
        className="pointer-events-none absolute -top-20 -right-20 size-80 rounded-full blur-3xl transition-all duration-700 opacity-20"
        style={{ background: active.glow }}
        aria-hidden
      />

      {/* Top Header: System Instrument Bar */}
      <div className="relative flex flex-wrap items-center justify-between gap-3 border-b border-[#6F4E37] pb-3.5">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#B85C38] to-[#6C63A8] text-white shadow-sm shadow-[#B85C38]/40">
            <Cpu className="size-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h3 className="font-display text-[14.5px] font-bold tracking-tight text-[#FFF8F0]">
                EDUACCESS COMPILER CORE
              </h3>
              <span className="rounded-full bg-[#5F8A62]/20 border border-[#5F8A62]/40 px-2.5 py-0.5 text-[10px] font-mono font-bold text-[#8FC493] uppercase tracking-wider">
                LIVE COMPILING
              </span>
            </div>
            <p className="text-[11px] font-mono text-[#E8DCD1]">
              Deterministic Video Ingestion → Multimodal Reasoning → Accessible Twin
            </p>
          </div>
        </div>

        {/* Telemetry controls */}
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setIsAutoCycling(!isAutoCycling)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-mono font-bold border transition cursor-pointer",
              isAutoCycling
                ? "border-[#5F8A62]/40 bg-[#5F8A62]/20 text-[#8FC493]"
                : "border-[#6F4E37] bg-[#3F352E] text-[#E8DCD1]"
            )}
            title="Toggle automatic stage progression"
          >
            <RotateCw className={cn("size-3.5", isAutoCycling && "animate-spin-slow")} />
            <span>{isAutoCycling ? "AUTO" : "PAUSED"}</span>
          </button>

          <span className="font-mono text-xs text-[#E8DCD1] font-semibold">
            <span className="text-[#B85C38] font-bold text-sm">{active.step}</span>
            <span className="text-[#8B6B52] mx-1">/</span>
            <span>09</span>
          </span>
        </div>
      </div>

      {/* Interactive Horizontal Pipeline Stage Selector (9 Stages) */}
      <div className="relative mt-3.5 grid grid-cols-9 gap-1.5 p-1.5 rounded-xl bg-[#2E2620] border border-[#6F4E37]">
        {COMPILER_STAGES.map((st, i) => {
          const Icon = st.icon;
          const isCurrent = i === activeIdx;
          const isPassed = i < activeIdx;

          return (
            <button
              key={st.id}
              type="button"
              onClick={() => {
                setActiveIdx(i);
                setIsAutoCycling(false);
              }}
              className={cn(
                "relative flex flex-col items-center justify-center py-2 px-1 rounded-lg transition-all duration-300 group cursor-pointer",
                isCurrent
                  ? "bg-[#B85C38] text-white shadow-sm scale-[1.04] z-10 font-bold"
                  : isPassed
                  ? "bg-[#3F352E] text-[#8FC493] hover:bg-[#51483F]"
                  : "bg-transparent text-[#AAB09A] hover:text-[#FFF8F0] hover:bg-[#3F352E]"
              )}
              title={`${st.step}. ${st.label}`}
            >
              <Icon className="size-3.5 sm:size-4" />
              <span className="mt-1 font-mono text-[9px] sm:text-[10px] font-bold leading-none">
                {st.step}
              </span>
            </button>
          );
        })}
      </div>

      {/* Central Interactive Laboratory Workbench */}
      <div className="relative mt-4 grid gap-4 lg:grid-cols-12 items-stretch">
        {/* Left: Video / Modality Frame Simulation (5 cols) */}
        <div className="lg:col-span-5 flex flex-col rounded-2xl border border-[#6F4E37] bg-[#2E2620] p-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-[#E8DCD1]">
            <span className="flex items-center gap-1.5 text-[#FFF8F0] font-semibold">
              <span className="size-2 rounded-full bg-[#B94A48] animate-ping" />
              DEMO_python_loops.mp4
            </span>
            <span className="text-[#8DB4D6] font-bold">00:26.0s</span>
          </div>

          {/* Simulated Video Slide Canvas with OCR Overlay */}
          <div className="relative aspect-video w-full overflow-hidden rounded-xl border border-[#51483F] bg-[#241E1A] flex flex-col justify-between p-3.5 font-mono">
            {/* Slide title */}
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-[#E8DCD1] font-bold tracking-wider uppercase">
                PYTHON 3.10 · FOR LOOPS
              </span>
              <span className="rounded bg-[#6C63A8]/30 border border-[#6C63A8]/50 px-2 py-0.5 text-[9.5px] font-bold text-[#AAA4D1]">
                KEYFRAME #04
              </span>
            </div>

            {/* Code Block in Slide */}
            <div className="rounded-lg bg-[#1A1512] border border-[#51483F] p-2.5 text-[11px] sm:text-xs text-[#A7D8A9] leading-relaxed font-mono">
              <div className="text-[#AAB09A]"># Iterating over sequence</div>
              <div>fruits = [&quot;apple&quot;, &quot;banana&quot;, &quot;cherry&quot;]</div>
              <div className="text-[#E6AA68] font-bold">for fruit in fruits:</div>
              <div className="pl-3 text-[#8DB4D6] font-semibold">print(fruit)</div>
            </div>

            {/* Bottom active audio description overlay strip */}
            <div className="rounded-lg bg-[#5F8A62]/25 border border-[#5F8A62]/40 px-2.5 py-1.5 text-[10px] text-[#8FC493] flex items-center justify-between font-semibold">
              <span className="flex items-center gap-1.5 truncate">
                <Volume2 className="size-3 shrink-0 text-[#8FC493]" />
                AD #03: &ldquo;for fruit in fruits colon, print fruit&rdquo;
              </span>
              <span className="font-bold text-[9px] text-[#8FC493] shrink-0 bg-[#5F8A62]/30 px-1.5 py-0.5 rounded">
                ACTIVE
              </span>
            </div>
          </div>

          {/* Modality Stream Waveform Indicator */}
          <div className="flex items-center justify-between px-1 text-[11px] font-mono text-[#E8DCD1]">
            <span className="flex items-center gap-1.5 font-semibold text-[#FFF8F0]">
              <Mic className="size-3.5 text-[#8DB4D6]" /> Speech Stream
            </span>
            <div className="flex items-center gap-1">
              {[35, 60, 20, 85, 45, 95, 30, 70, 40, 80, 50, 90, 25, 65].map((h, idx) => (
                <span
                  key={idx}
                  className="inline-block w-1 rounded-full bg-[#5B82A6] transition-all duration-300"
                  style={{ height: `${(h / 100) * 16}px` }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right: Active Stage Telemetry & Deep Grounding (7 cols) */}
        <div className="lg:col-span-7 flex flex-col justify-between rounded-2xl border border-[#6F4E37] bg-[#2E2620] p-4 space-y-3.5">
          {/* Active Stage Header */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#6F4E37] pb-3">
            <div className="flex items-center gap-3">
              <span
                className={cn(
                  "flex size-9 items-center justify-center rounded-xl border bg-gradient-to-br text-white shadow-xs",
                  active.color
                )}
              >
                <ActiveIcon className="size-4.5" />
              </span>
              <div>
                <p className="text-sm font-bold text-[#FFF8F0] leading-tight">
                  {active.label}
                </p>
                <p className="text-[11px] text-[#E8DCD1] font-mono mt-0.5">{active.subtitle}</p>
              </div>
            </div>

            <span className={cn("rounded-full border px-3 py-1 font-mono text-[10.5px] font-bold uppercase tracking-wider", active.color)}>
              {active.category}
            </span>
          </div>

          {/* Telemetry Live Feed Block */}
          <div className="rounded-xl border border-[#6F4E37] bg-[#241E1A] p-3.5 font-mono text-xs space-y-2.5 flex-1 flex flex-col justify-center">
            <div className="flex items-center justify-between text-[11px]">
              <span className="flex items-center gap-2 text-[#8EC5C5] font-bold">
                <Activity className="size-3.5 text-[#8EC5C5] animate-pulse" />
                {active.telemetry.title}
              </span>
              <span className="text-[#8FC493] font-bold">
                {active.telemetry.metrics}
              </span>
            </div>

            {/* Dynamic Content: Spoken Transcript, Extracted Code, or Narration Action */}
            {active.telemetry.spoken && (
              <div className="rounded-lg bg-[#5B82A6]/15 border border-[#5B82A6]/30 p-2.5 text-[#8DB4D6] text-xs leading-relaxed italic">
                {active.telemetry.spoken}
              </div>
            )}

            {active.telemetry.code && (
              <div className="rounded-lg bg-[#1A1512] border border-[#51483F] p-3 text-[#A7D8A9] text-[11.5px] leading-relaxed whitespace-pre font-mono font-semibold">
                {active.telemetry.code}
              </div>
            )}

            {active.telemetry.action && (
              <div className="rounded-lg bg-[#5F8A62]/20 border border-[#5F8A62]/40 p-2.5 text-[#8FC493] text-xs leading-relaxed font-semibold">
                {active.telemetry.action}
              </div>
            )}

            <p className="text-[#E8DCD1] text-xs leading-relaxed font-sans">
              {active.telemetry.detail}
            </p>
          </div>

          {/* Grounding & Causality Footer */}
          <div className="flex items-center justify-between pt-2.5 border-t border-[#6F4E37] text-[11px] text-[#E8DCD1] font-mono">
            <span className="flex items-center gap-1.5 text-[#8FC493] font-bold">
              <ShieldCheck className="size-4" />
              Verified in Ground Truth Media
            </span>
            <span className="text-[#AAB09A] font-semibold">{active.telemetry.timestamp}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
