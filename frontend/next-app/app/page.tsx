"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Upload,
  ShieldCheck,
  Video,
  Sparkles,
  Clock,
  CheckCircle2,
  CircleX,
  Eye,
  ScanText,
  Mic,
  GitCompareArrows,
  BrainCircuit,
  Play,
  Check,
  ChevronRight,
  HelpCircle,
  FileCode,
  Sliders,
  Cpu,
  Workflow,
  Volume2,
  AlertTriangle,
  Accessibility,
  GraduationCap,
  PlayCircle,
  Crosshair,
  ExternalLink,
  Layers,
  Activity,
  Terminal,
  Compass,
} from "lucide-react";
import { useWorkspace } from "@/components/lecture/WorkspaceProvider";
import { WorkspaceProvider } from "@/components/lecture/WorkspaceProvider";
import { isDemo } from "@/components/lecture/LecturePicker";
import { getAccessibilityScore, getNextAction } from "@/lib/api";
import { cn, formatSeconds, formatClock } from "@/lib/format";
import type { NextActionResponse } from "@/types/backend";
import { useRtl } from "@/components/layout/AppShell";
import {
  SectionRail,
  TrustPill,
  EvidenceTimestamp,
  DataStrip,
  ConceptBadge,
  EvidenceSnippet,
} from "@/components/ui/evidence-primitives";
import HeroCompilerVisual from "@/components/ui/HeroCompilerVisual";
import { AccessibilityTwin } from "@/components/twin/AccessibilityTwin";
import { EvidenceLens } from "@/components/ui/EvidenceLens";

export default function HomePage() {
  return (
    <WorkspaceProvider>
      <HomeContent />
    </WorkspaceProvider>
  );
}

const CHAPTERS = [
  { num: "01", title: "THE VIDEO", label: "Raw Lecture Demuxing" },
  { num: "02", title: "MULTIMODAL UNDERSTANDING", label: "Speech + Vision + OCR" },
  { num: "03", title: "CROSS-MODAL ALIGNMENT", label: "Temporal Sync Matrix" },
  { num: "04", title: "THE INVISIBLE GAP", label: "Shown vs Spoken Reasoning" },
  { num: "05", title: "ACCESSIBILITY REMEDIATION", label: "Dual-Audio AD Studio" },
  { num: "06", title: "ACCESSIBILITY TWIN", label: "10-Node Nervous System" },
  { num: "07", title: "PERSONALIZED LEARNING", label: "Adaptive Quiz & Next Action" },
];

function HomeContent() {
  const { lectures, loading, selectedId } = useWorkspace();
  const { language, dir } = useRtl();
  const [scores, setScores] = useState<Record<string, { score: number; level: string; trust: string }>>({});
  const [nextAction, setNextAction] = useState<NextActionResponse | null>(null);

  const t = (english: string, arabic: string) => (language === "ar" ? arabic : english);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      for (const sid of ["001", "default"]) {
        try {
          const r = await getNextAction(sid);
          if (!cancelled && !r.insufficient_history) {
            setNextAction(r);
            return;
          }
        } catch {
          /* try next student */
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!lectures.length) return;
    let cancelled = false;
    lectures.slice(0, 6).forEach((l) => {
      getAccessibilityScore(l.job_id)
        .then((r) => {
          if (!cancelled)
            setScores((s) => ({ ...s, [l.job_id]: { score: r.score, level: r.level, trust: r.trust?.trust ?? "UNAVAILABLE" } }));
        })
        .catch(() => {});
    });
    return () => {
      cancelled = true;
    };
  }, [lectures, selectedId]);

  const demoLecture = lectures.find(isDemo) ?? (lectures.length > 0 ? lectures[0] : null);

  return (
    <div className="relative w-full flex flex-col pb-24 bg-[#F7F1E8] text-[#2F2924] selection:bg-[#B85C38]/20 selection:text-[#2F2924]">
      {/* ============================================================
         HERO SECTION · CINEMATIC FIRST VIEWPORT (85–100vh)
         ============================================================ */}
      <section className="relative w-full min-h-[90vh] flex flex-col justify-center px-4 sm:px-8 lg:px-14 py-12 lg:py-20 border-b border-[#DDD0C0] bg-gradient-to-b from-[#FBF8F2] via-[#F7F1E8] to-[#F1E8DC] overflow-hidden">
        {/* Subtle Ambient Brand Glows */}
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-[#B85C38]/8 blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 -right-32 w-96 h-96 rounded-full bg-[#6C63A8]/7 blur-3xl pointer-events-none" />

        <div className="max-w-[1440px] mx-auto w-full grid gap-12 lg:grid-cols-12 items-center relative z-10">
          {/* LEFT: Monumental Editorial Typography & Actions */}
          <div className="lg:col-span-6 min-w-0 flex flex-col justify-center gap-6 lg:gap-8">
            {/* System Status Pill */}
            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center gap-2 rounded-full bg-[#FFF8F4] text-[#B85C38] border border-[#E8C2B2] px-4 py-1.5 text-xs font-mono font-bold uppercase tracking-[0.16em] shadow-xs">
                <Sparkles className="size-3.5 text-[#B85C38] animate-pulse" aria-hidden />
                {t("EDUACCESS AI · COMPILER CORE", "مُجَمِّع إمكانية الوصول للتعليم")}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-[#EBF5EC] text-[#3D6B40] border border-[#C5E3C7] px-3.5 py-1.5 text-xs font-mono font-bold">
                <PlayCircle className="size-3.5 text-[#5F8A62]" aria-hidden />
                PRODUCTION ENGINE ACTIVE
              </span>
            </div>

            {/* Monumental Editorial Headline */}
            <div className="space-y-4">
              <div className="font-mono text-xs sm:text-sm font-bold uppercase tracking-[0.25em] text-[#8B6B52]">
                AI ACCESSIBILITY LABORATORY
              </div>
              <h1 className="hero-monumental text-[#2F2924]">
                THE ACCESSIBILITY
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#B85C38] via-[#9F4F32] to-[#6F4E37]">
                  COMPILER
                </span>
                <br />
                FOR EDUCATION
              </h1>
              <p className="max-w-2xl text-base sm:text-lg lg:text-xl text-[#51483F] font-sans leading-relaxed">
                {t(
                  "Transforms educational video into fully accessible, grounded, dual-audio learning experiences through multimodal speech, vision, OCR, and cross-modal disparity reasoning.",
                  "يُحوّل الفيديوهات التعليمية إلى تجارب تعلّم موثّقة ومتاحة للجميع بالصوت المزدوج والرؤية والتعرف البصري واستنتاج الفجوات."
                )}
              </p>
            </div>

            {/* Direct Action Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-1">
              <Link
                href="/upload"
                className="inline-flex items-center gap-3 rounded-xl bg-[#B85C38] text-white font-bold px-7 py-4 text-base shadow-lg shadow-[#B85C38]/25 hover:bg-[#9F4F32] hover:scale-[1.01] active:scale-[0.99] transition duration-150"
              >
                <Upload className="size-4.5" />
                <span>{t("Upload & Compile Lecture", "رفع ومعالجة المحاضرة")}</span>
                <ArrowRight className="size-4.5 opacity-90" />
              </Link>

              <Link
                href="/lectures"
                className="inline-flex items-center gap-2.5 rounded-xl bg-[#FFFDFC] text-[#2F2924] border border-[#DDD0C0] hover:border-[#B85C38] hover:bg-[#F1E8DC] font-bold px-6 py-4 text-base transition duration-150 shadow-xs"
              >
                <Play className="size-4.5 text-[#B85C38]" />
                <span>{t("Explore Lecture Library", "استعراض مكتبة المحاضرات")}</span>
              </Link>
            </div>
          </div>

          {/* RIGHT: Signature Centerpiece (EDUACCESS COMPILER CORE) */}
          <div className="lg:col-span-6 min-w-0">
            <HeroCompilerVisual />
          </div>
        </div>
      </section>

      {/* ============================================================
         CHAPTER NAVIGATION RAIL
         ============================================================ */}
      <div className="sticky top-0 z-30 w-full border-y border-[#DDD0C0] bg-[#FBF8F2]/95 backdrop-blur-md px-4 py-3 shadow-xs">
        <div className="max-w-[1440px] mx-auto flex items-center justify-between overflow-x-auto gap-4 scrollbar-none font-mono text-xs">
          <span className="text-[#B85C38] font-bold shrink-0 flex items-center gap-2 text-xs uppercase tracking-wider">
            <Compass className="size-4 text-[#B85C38]" />
            ARCHITECTURE STORY:
          </span>
          <div className="flex items-center gap-1.5 shrink-0">
            {CHAPTERS.map((ch) => (
              <a
                key={ch.num}
                href={`#chapter-${ch.num}`}
                className="px-3 py-1.5 rounded-lg text-[#51483F] hover:text-[#2F2924] hover:bg-[#F1E8DC] transition flex items-center gap-2 font-semibold"
              >
                <span className="text-[#B85C38] font-bold">{ch.num}</span>
                <span className="hidden md:inline">{ch.title}</span>
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* ============================================================
         CHAPTER 01 · THE VIDEO (WARM SECONDARY #F1E8DC)
         ============================================================ */}
      <section id="chapter-01" className="py-20 px-4 sm:px-8 lg:px-14 bg-[#F1E8DC] border-b border-[#DDD0C0]">
        <div className="max-w-[1440px] mx-auto space-y-10">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-[#B85C38] font-bold uppercase tracking-wider">
              <span className="size-2 rounded-full bg-[#B85C38] animate-pulse" />
              CHAPTER 01 · SOURCE INGESTION
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-bold text-[#2F2924] tracking-tight">
              Raw Educational Video Ingestion
            </h2>
            <p className="max-w-3xl text-[#51483F] text-base sm:text-lg leading-relaxed">
              Educational videos contain high-density multimodal knowledge: spoken lecturer explanation, on-screen slides, dynamic diagrams, and code demonstrations. EduAccess AI demuxes the container into synchronized media streams.
            </p>
          </div>

          {/* Visual Presentation */}
          <div className="grid gap-6 lg:grid-cols-12 items-center">
            <div className="lg:col-span-7 rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-5 sm:p-6 space-y-4 shadow-sm">
              <div className="flex items-center justify-between text-xs font-mono text-[#7A7067]">
                <span className="text-[#2F2924] font-bold text-sm">DEMO_python_loops.mp4</span>
                <span className="text-[#B85C38] font-bold">1080p @ 30fps · H.264 / AAC</span>
              </div>

              <div className="aspect-video w-full rounded-xl border border-[#DDD0C0] bg-[#EDE2D3] flex flex-col justify-center items-center p-6 text-center space-y-3.5 relative overflow-hidden">
                <div className="size-16 rounded-2xl bg-[#FFF8F4] border border-[#E8C2B2] flex items-center justify-center text-[#B85C38] shadow-sm">
                  <Video className="size-8" />
                </div>
                <div>
                  <h4 className="text-[#2F2924] font-bold text-lg">Python 3.10: For Loop Iteration Lecture</h4>
                  <p className="text-[#7A7067] text-sm font-mono mt-1">Duration: 28.0s · Stereo Audio Channel · 840 Discrete Frames</p>
                </div>
                <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
                  <span className="rounded-lg bg-[#FFFDFC] border border-[#DDD0C0] px-3 py-1.5 text-xs font-mono text-[#51483F] font-semibold shadow-xs">Audio Extracted: 44.1kHz WAV</span>
                  <span className="rounded-lg bg-[#FFFDFC] border border-[#DDD0C0] px-3 py-1.5 text-xs font-mono text-[#51483F] font-semibold shadow-xs">Frame Demux: 14 Keyframes</span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-5 space-y-4">
              <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 space-y-4 font-mono text-xs shadow-sm">
                <div className="text-[#B85C38] font-bold text-sm flex items-center gap-2.5">
                  <Terminal className="size-4.5" /> INGESTION TELEMETRY
                </div>
                <div className="space-y-3 text-[#51483F] text-xs sm:text-[13px]">
                  <div className="flex justify-between border-b border-[#EDE2D3] pb-2">
                    <span className="text-[#7A7067] font-semibold">Acoustic Demux:</span>
                    <span className="text-[#5F8A62] font-bold">PASSED (0.21s)</span>
                  </div>
                  <div className="flex justify-between border-b border-[#EDE2D3] pb-2">
                    <span className="text-[#7A7067] font-semibold">Keyframe Detection:</span>
                    <span className="text-[#5F8A62] font-bold">14 Keyframes</span>
                  </div>
                  <div className="flex justify-between border-b border-[#EDE2D3] pb-2">
                    <span className="text-[#7A7067] font-semibold">Temporal Resolution:</span>
                    <span className="text-[#5B82A6] font-bold">±0.033s (1 frame)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
         CHAPTER 02 · MULTIMODAL UNDERSTANDING (CREAM #FBF8F2)
         ============================================================ */}
      <section id="chapter-02" className="py-20 px-4 sm:px-8 lg:px-14 bg-[#FBF8F2] border-b border-[#DDD0C0]">
        <div className="max-w-[1440px] mx-auto space-y-10">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-[#6C63A8] font-bold uppercase tracking-wider">
              <span className="size-2 rounded-full bg-[#6C63A8]" />
              CHAPTER 02 · MULTIMODAL DECOMPILATION
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-bold text-[#2F2924] tracking-tight">
              Parallel Speech, Vision & OCR Understanding
            </h2>
            <p className="max-w-3xl text-[#51483F] text-base sm:text-lg leading-relaxed font-sans">
              The AI compiler simultaneously runs Whisper speech-to-text, computer vision keyframe feature extraction, and OCR text extraction to decompile what was said vs what was visually presented.
            </p>
          </div>

          {/* 3-Column Parallel Extraction Cards */}
          <div className="grid gap-6 md:grid-cols-3">
            {/* SPEECH COLUMN */}
            <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 shadow-sm space-y-3.5">
              <div className="flex items-center gap-2 text-[#5B82A6] font-mono font-bold text-sm">
                <Mic className="size-5" />
                <span>SPEECH: WHISPER STT</span>
              </div>
              <p className="text-xs sm:text-sm text-[#7A7067] font-medium">Timestamped spoken word stream:</p>
              <div className="rounded-xl bg-[#F4F7FA] border border-[#D5E1EC] p-4 font-mono text-xs sm:text-sm text-[#2F2924] space-y-2">
                <div className="text-xs text-[#5B82A6] font-bold">[00:26.4 → 00:34.1]</div>
                <p className="italic leading-relaxed font-sans font-medium text-[#51483F]">
                  &ldquo;...as we move through the loop, each item is printed in turn.&rdquo;
                </p>
              </div>
              <div className="text-xs font-mono font-semibold text-[#7A7067]">24 segments mapped · Avg Confidence: 0.96</div>
            </div>

            {/* VISION COLUMN */}
            <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 shadow-sm space-y-3.5">
              <div className="flex items-center gap-2 text-[#5F9A9A] font-mono font-bold text-sm">
                <Eye className="size-5" />
                <span>VISION: KEYFRAME OCR</span>
              </div>
              <p className="text-xs sm:text-sm text-[#7A7067] font-medium">Slide visual keyframe at 00:26.0s:</p>
              <div className="rounded-xl bg-[#3F352E] border border-[#52463D] p-4 font-mono text-xs sm:text-sm text-[#E8C2B2] space-y-1.5 shadow-inner">
                <div className="text-xs text-[#5F9A9A] font-bold">KEYFRAME #04 @ 00:26.0</div>
                <div className="text-[#EDE2D3]">fruits = [&quot;apple&quot;, &quot;banana&quot;, &quot;cherry&quot;]</div>
                <div className="text-[#C49A5A] font-bold">for fruit in fruits:</div>
                <div className="pl-3 text-[#AAB09A] font-semibold">print(fruit)</div>
              </div>
              <div className="text-xs font-mono font-semibold text-[#7A7067]">14 Keyframes · 0.98 Visual Confidence</div>
            </div>

            {/* OCR COLUMN */}
            <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 shadow-sm space-y-3.5">
              <div className="flex items-center gap-2 text-[#6C63A8] font-mono font-bold text-sm">
                <ScanText className="size-5" />
                <span>OCR: SYNTAX ANALYSIS</span>
              </div>
              <p className="text-xs sm:text-sm text-[#7A7067] font-medium">Parsed programming language constructs:</p>
              <div className="rounded-xl bg-[#F6F5FB] border border-[#DDD8EE] p-4 font-mono text-xs sm:text-sm text-[#2F2924] space-y-1.5">
                <div><span className="text-[#7A7067] font-semibold">Type:</span> <span className="font-bold text-[#2F2924]">Python for-loop</span></div>
                <div><span className="text-[#7A7067] font-semibold">Iterable:</span> <span className="text-[#5B82A6] font-bold">fruits (list[str])</span></div>
                <div><span className="text-[#7A7067] font-semibold">Target Var:</span> <span className="text-[#6C63A8] font-bold">fruit</span></div>
                <div><span className="text-[#7A7067] font-semibold">Body:</span> <span className="text-[#5F8A62] font-bold">print(fruit)</span></div>
              </div>
              <div className="text-xs font-mono font-semibold text-[#7A7067]">Deterministic code AST parsing</div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
         CHAPTER 03 · CROSS-MODAL ALIGNMENT (WARM SECONDARY #F1E8DC)
         ============================================================ */}
      <section id="chapter-03" className="py-20 px-4 sm:px-8 lg:px-14 bg-[#F1E8DC] border-b border-[#DDD0C0]">
        <div className="max-w-[1440px] mx-auto space-y-10">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-[#5B82A6] font-bold uppercase tracking-wider">
              <span className="size-2 rounded-full bg-[#5B82A6] animate-pulse" />
              CHAPTER 03 · TEMPORAL MATRIX SYNCHRONIZATION
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-bold text-[#2F2924] tracking-tight">
              Cross-Modal Temporal Alignment
            </h2>
            <p className="max-w-3xl text-[#51483F] text-base sm:text-lg leading-relaxed font-sans">
              EduAccess AI establishes temporal co-occurrence between what appears on screen and what is spoken by the instructor at every millisecond of the lecture.
            </p>
          </div>

          <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 sm:p-8 space-y-5 font-mono text-xs sm:text-sm shadow-sm">
            <div className="flex flex-wrap items-center justify-between border-b border-[#EDE2D3] pb-3.5 gap-2">
              <span className="text-[#B85C38] font-bold text-sm">TEMPORAL CO-OCCURRENCE MATRIX</span>
              <span className="text-[#7A7067] font-semibold">Time Window: 00:20 → 00:36</span>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-[#D5E1EC] bg-[#F4F7FA] p-5 space-y-2.5">
                <span className="text-[#5B82A6] font-bold text-sm flex items-center gap-2">
                  <Mic className="size-4" /> Spoken Audio Timeline
                </span>
                <p className="text-[#51483F] text-xs sm:text-sm font-sans leading-relaxed">
                  [00:26.4] &ldquo;...as we move through the loop...&rdquo; (Mentions high-level concept, omits syntax structure)
                </p>
              </div>

              <div className="rounded-xl border border-[#D2E4E4] bg-[#F2F7F7] p-5 space-y-2.5">
                <span className="text-[#5F9A9A] font-bold text-sm flex items-center gap-2">
                  <ScanText className="size-4" /> Visual Slide Timeline
                </span>
                <p className="text-[#51483F] text-xs sm:text-sm font-sans leading-relaxed">
                  [00:26.0] Slide Keyframe #04 displays Python loop syntax: <code className="font-mono bg-[#E4ECEC] px-1.5 py-0.5 rounded text-[#2F2924] border border-[#CBDDDD]">for fruit in fruits:</code>
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-[#DDD8EE] bg-[#F6F5FB] p-4 text-[#6C63A8] text-center font-bold text-xs sm:text-sm">
              Δt Synchronization Precision: ±0.1s · Correlation Coefficient: 0.94
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
         CHAPTER 04 · THE INVISIBLE GAP (CREAM #FBF8F2)
         ============================================================ */}
      <section id="chapter-04" className="py-20 px-4 sm:px-8 lg:px-14 bg-[#FBF8F2] border-b border-[#DDD0C0]">
        <div className="max-w-[1440px] mx-auto space-y-10">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-[#B77932] font-bold uppercase tracking-wider">
              <span className="size-2 rounded-full bg-[#B77932]" />
              CHAPTER 04 · DISPARITY ENGINE (WHAT AM I MISSING?)
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-bold text-[#2F2924] tracking-tight">
              Detecting the Invisible Accessibility Gap
            </h2>
            <p className="max-w-3xl text-[#51483F] text-base sm:text-lg leading-relaxed font-sans">
              Standard accessibility tools (captions, generic screen readers) fail when educational information is shown visually but never spoken aloud. Our Disparity Engine highlights the exact gap.
            </p>
          </div>

          {/* Reasoning Chain Comparison */}
          <div className="grid gap-6 lg:grid-cols-12 items-stretch">
            {/* SHOWN VS SAID CHAIN (7 cols) */}
            <div className="lg:col-span-7 rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 sm:p-7 shadow-sm space-y-4">
              <h3 className="font-bold text-[#2F2924] text-base font-mono flex items-center gap-2.5">
                <GitCompareArrows className="size-5 text-[#B85C38]" />
                CAUSAL REASONING CHAIN @ 00:26.0s
              </h3>

              <div className="space-y-3.5 font-mono text-xs sm:text-sm">
                <div className="rounded-xl bg-[#F4F7FA] border border-[#D5E1EC] p-4 space-y-1">
                  <span className="text-[#5B82A6] font-bold text-xs uppercase tracking-wider">1. SHOWN ON SCREEN:</span>
                  <p className="text-[#2F2924] font-sans text-xs sm:text-sm leading-relaxed">
                    Code syntax block: <code className="bg-[#FFFDFC] px-2 py-0.5 rounded border border-[#DDD0C0] text-[#6C63A8] font-mono font-bold">for fruit in fruits: print(fruit)</code>
                  </p>
                </div>

                <div className="rounded-xl bg-[#F2F7F7] border border-[#D2E4E4] p-4 space-y-1">
                  <span className="text-[#5F9A9A] font-bold text-xs uppercase tracking-wider">2. SPOKEN IN AUDIO:</span>
                  <p className="text-[#51483F] font-sans text-xs sm:text-sm italic leading-relaxed">
                    &ldquo;...as we move through the loop, each item is printed in turn.&rdquo;
                  </p>
                </div>

                <div className="rounded-xl bg-[#FFF8F4] border border-[#F3CE9D] p-4 space-y-1">
                  <span className="text-[#B77932] font-bold text-xs uppercase tracking-wider">3. DISPARITY IDENTIFIED (THE GAP):</span>
                  <p className="text-[#51483F] font-sans text-xs sm:text-sm leading-relaxed font-medium">
                    The instructor does NOT read the code syntax aloud. A blind or visually impaired student misses the loop variable name and indentation syntax!
                  </p>
                </div>
              </div>
            </div>

            {/* EVIDENCE INSPECTOR CARD (5 cols) */}
            <div className="lg:col-span-5">
              <EvidenceLens
                data={{
                  timestamp: 26.0,
                  modality: "GAP",
                  source: "Cross-Modal Disparity Engine",
                  evidence: "Visual syntax shown on slide without explicit verbal description in audio channel.",
                  codeSnippet: 'for fruit in fruits:\n    print(fruit)',
                  confidence: 0.94,
                  status: "GAP_DETECTED",
                  remediation: "AD Cue #03 synthesized to describe syntax verbatim.",
                }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
         CHAPTER 05 · ACCESSIBILITY REMEDIATION (WARM SECONDARY #F1E8DC)
         ============================================================ */}
      <section id="chapter-05" className="py-20 px-4 sm:px-8 lg:px-14 bg-[#F1E8DC] border-b border-[#DDD0C0]">
        <div className="max-w-[1440px] mx-auto space-y-10">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-[#5F8A62] font-bold uppercase tracking-wider">
              <span className="size-2 rounded-full bg-[#5F8A62] animate-pulse" />
              CHAPTER 05 · SYNTHESIZED DUAL-AUDIO REMEDIATION
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-bold text-[#2F2924] tracking-tight">
              Non-Destructive Audio Description Studio
            </h2>
            <p className="max-w-3xl text-[#51483F] text-base sm:text-lg leading-relaxed font-sans">
              EduAccess AI generates precision Audio Description (AD) cues inserted into natural pauses or layered over the lecture without modifying or destroying the original teacher&rsquo;s voice.
            </p>
          </div>

          <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 sm:p-8 space-y-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between border-b border-[#EDE2D3] pb-3.5 font-mono text-xs sm:text-sm gap-2">
              <span className="text-[#5F8A62] font-bold flex items-center gap-2">
                <Volume2 className="size-4.5" />
                SYNCHRONIZED AD STUDIO TRACK
              </span>
              <span className="text-[#7A7067] font-semibold">6 Real Cues Injected · Dual Audio</span>
            </div>

            <div className="grid gap-4 md:grid-cols-3 font-mono text-xs sm:text-sm">
              <div className="rounded-xl border border-[#DDD0C0] bg-[#FBF8F2] p-4 space-y-1.5">
                <span className="text-[#5B82A6] font-bold text-xs">[00:03.0 → 00:06.5]</span>
                <p className="text-[#51483F] text-xs sm:text-sm font-sans leading-relaxed">AD #01: &ldquo;Title slide: Python Loops and Iteration.&rdquo;</p>
              </div>
              <div className="rounded-xl border border-[#E8C2B2] bg-[#FFF8F4] p-4 space-y-1.5 ring-1 ring-[#B85C38]/40">
                <span className="text-[#B85C38] font-bold text-xs">[00:26.2 → 00:30.5] (CRITICAL)</span>
                <p className="text-[#2F2924] text-xs sm:text-sm font-sans leading-relaxed font-medium">AD #03: &ldquo;On screen: for fruit in fruits colon, indent print fruit.&rdquo;</p>
              </div>
              <div className="rounded-xl border border-[#DDD0C0] bg-[#FBF8F2] p-4 space-y-1.5">
                <span className="text-[#5B82A6] font-bold text-xs">[00:48.0 → 00:52.0]</span>
                <p className="text-[#51483F] text-xs sm:text-sm font-sans leading-relaxed">AD #06: &ldquo;Terminal output displays apple, banana, cherry on new lines.&rdquo;</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
         CHAPTER 06 · ACCESSIBILITY TWIN (CREAM #FBF8F2)
         ============================================================ */}
      <section id="chapter-06" className="py-20 px-4 sm:px-8 lg:px-14 bg-[#FBF8F2] border-b border-[#DDD0C0]">
        <div className="max-w-[1440px] mx-auto space-y-10">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-[#B85C38] font-bold uppercase tracking-wider">
              <span className="size-2 rounded-full bg-[#B85C38] animate-pulse" />
              CHAPTER 06 · STRUCTURED LECTURE GRAPH
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-bold text-[#2F2924] tracking-tight">
              The Accessibility Twin: Digital Nervous System
            </h2>
            <p className="max-w-3xl text-[#51483F] text-base sm:text-lg leading-relaxed font-sans">
              Every lecture compiles into an Accessibility Twin—a unified 10-node knowledge representation linking Video, Speech, Vision, OCR, Concepts, Gaps, Evidence, AD, Quizzes, and Personalized Learning.
            </p>
          </div>

          {/* Full Interactive 10-Node Accessibility Twin */}
          <AccessibilityTwin score={100} />
        </div>
      </section>

      {/* ============================================================
         CHAPTER 07 · PERSONALIZED LEARNING (WARM SECONDARY #F1E8DC)
         ============================================================ */}
      <section id="chapter-07" className="py-20 px-4 sm:px-8 lg:px-14 bg-[#F1E8DC] border-b border-[#DDD0C0]">
        <div className="max-w-[1440px] mx-auto space-y-10">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-[#6C63A8] font-bold uppercase tracking-wider">
              <span className="size-2 rounded-full bg-[#6C63A8]" />
              CHAPTER 07 · ADAPTIVE INTELLIGENCE
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-bold text-[#2F2924] tracking-tight">
              Personalized Learning Agent & Next Best Action
            </h2>
            <p className="max-w-3xl text-[#51483F] text-base sm:text-lg leading-relaxed font-sans">
              Grounding allows the AI tutor to generate adaptive quizzes directly from extracted evidence and recommend the optimal Next Best Action for the student.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 sm:p-7 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-[#6C63A8] flex items-center gap-2">
                  <GraduationCap className="size-4.5" /> ADAPTIVE QUIZ
                </span>
                <span className="font-mono text-xs bg-[#F6F5FB] text-[#6C63A8] border border-[#DDD8EE] px-2.5 py-1 rounded font-bold">
                  Grounded in Slide #04
                </span>
              </div>
              <h4 className="font-bold text-[#2F2924] text-base leading-snug">
                &ldquo;What is the loop variable in the statement <code className="font-mono bg-[#F1E8DC] px-1.5 py-0.5 rounded border border-[#DDD0C0] font-bold">for fruit in fruits:</code>?&rdquo;
              </h4>
              <div className="space-y-2 font-mono text-xs sm:text-sm pt-2">
                <div className="p-3 rounded-xl border border-[#C5E3C7] bg-[#EBF5EC] text-[#2D5A30] font-bold flex items-center justify-between shadow-xs">
                  <span>A) fruit</span>
                  <CheckCircle2 className="size-5 text-[#5F8A62]" />
                </div>
                <div className="p-3 rounded-xl border border-[#DDD0C0] bg-[#FBF8F2] text-[#51483F] font-semibold">
                  B) fruits
                </div>
                <div className="p-3 rounded-xl border border-[#DDD0C0] bg-[#FBF8F2] text-[#51483F] font-semibold">
                  C) print
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] p-6 sm:p-7 shadow-sm space-y-4 flex flex-col justify-between">
              <div className="space-y-3.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[#5F8A62] flex items-center gap-2">
                    <Sparkles className="size-4.5 text-[#5F8A62]" /> NEXT BEST ACTION (NBA)
                  </span>
                  <span className="font-mono text-xs bg-[#EBF5EC] text-[#3D6B40] border border-[#C5E3C7] px-2.5 py-1 rounded font-bold">
                    Student Mastery: 88%
                  </span>
                </div>
                <h4 className="font-bold text-[#2F2924] text-base leading-snug">
                  Recommended Action: Practice Nested Loop Syntax
                </h4>
                <p className="text-[#51483F] text-sm leading-relaxed font-sans font-normal">
                  The student has mastered 1D list iteration. The Personal Learning Agent suggests exploring nested loops and dictionary keys next.
                </p>
              </div>

              <div className="pt-4 border-t border-[#EDE2D3] flex items-center justify-between">
                <Link
                  href="/learning"
                  className="inline-flex items-center gap-2 text-[#B85C38] font-bold text-sm hover:underline"
                >
                  <span>Open Learning Intelligence Center</span>
                  <ArrowRight className="size-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
         FINAL CALL TO ACTION SECTION (CREAM #FBF8F2)
         ============================================================ */}
      <section className="py-20 px-4 sm:px-8 lg:px-14 text-center bg-[#FBF8F2]">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full bg-[#FFF8F4] border border-[#E8C2B2] px-4 py-1.5 text-xs font-mono font-bold text-[#B85C38]">
            <Sparkles className="size-4 text-[#B85C38]" /> COMPETITION-READY AI ACCESSIBILITY
          </div>
          <h2 className="text-3xl sm:text-5xl font-display font-bold text-[#2F2924] tracking-tight">
            Experience EduAccess AI Live
          </h2>
          <p className="text-[#51483F] text-base sm:text-lg leading-relaxed">
            Inspect the benchmark Python Loops lecture with synchronized speech, visual understanding, OCR evidence, disparity detection, real audio descriptions, and interactive twin.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              href="/lectures/DEMO_python_loops"
              className="inline-flex items-center gap-2.5 rounded-xl bg-[#B85C38] text-white font-bold px-8 py-4 text-base shadow-lg shadow-[#B85C38]/25 hover:bg-[#9F4F32] hover:scale-[1.01] active:scale-[0.99] transition duration-150"
            >
              <Play className="size-4.5 fill-white" />
              <span>Launch Accessibility Studio (DEMO)</span>
            </Link>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2.5 rounded-xl bg-[#FFFDFC] text-[#2F2924] border border-[#DDD0C0] hover:border-[#B85C38] hover:bg-[#F1E8DC] font-bold px-7 py-4 text-base transition duration-150 shadow-xs"
            >
              <Upload className="size-4.5 text-[#B85C38]" />
              <span>Compile New Lecture</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
