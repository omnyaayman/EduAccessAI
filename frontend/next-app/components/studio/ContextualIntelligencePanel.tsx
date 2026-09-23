"use client";

import * as React from "react";
import {
  Eye,
  Mic,
  ScanText,
  AlertTriangle,
  Sparkles,
  ShieldCheck,
  Volume2,
  ChevronDown,
  ChevronRight,
  Clock,
  Play,
  BrainCircuit,
  Gauge,
} from "lucide-react";
import { cn, formatClock } from "@/lib/format";
import {
  TrustPill,
  EvidenceTimestamp,
  EvidenceSnippet,
  SectionRail,
} from "@/components/ui/evidence-primitives";
import type {
  TranscriptSegment,
  VisualEventItem,
  AnalysisItem,
  MissingItem,
  AccessibilityEvent,
  TrustLevel,
} from "@/types/backend";

interface SectionDef {
  id: "shown" | "said" | "ocr" | "missing" | "generated" | "evidence";
  label: string;
  Icon: typeof Eye;
  colorCls: string;
  bgCls: string;
}

const SECTIONS: SectionDef[] = [
  {
    id: "shown",
    label: "WHAT WAS SHOWN",
    Icon: Eye,
    colorCls: "text-[#5F9A9A]",
    bgCls: "bg-[#F2F7F7]",
  },
  {
    id: "said",
    label: "WHAT WAS SAID",
    Icon: Mic,
    colorCls: "text-[#5B82A6]",
    bgCls: "bg-[#F4F7FA]",
  },
  {
    id: "ocr",
    label: "OCR FOUND",
    Icon: ScanText,
    colorCls: "text-[#6C63A8]",
    bgCls: "bg-[#F6F5FB]",
  },
  {
    id: "missing",
    label: "WHAT IS MISSING",
    Icon: AlertTriangle,
    colorCls: "text-[#B77932]",
    bgCls: "bg-[#FEF6EC]",
  },
  {
    id: "generated",
    label: "EDUACCESS GENERATED",
    Icon: Sparkles,
    colorCls: "text-[#5F8A62]",
    bgCls: "bg-[#EBF5EC]",
  },
  {
    id: "evidence",
    label: "EVIDENCE & TRUST",
    Icon: ShieldCheck,
    colorCls: "text-[#B85C38]",
    bgCls: "bg-[#FFF8F4]",
  },
];

interface ContextualIntelligencePanelProps {
  currentTime: number;
  duration?: number;
  segments: TranscriptSegment[];
  visuals: VisualEventItem[];
  analysis: AnalysisItem[];
  missing: MissingItem[];
  adCues: AccessibilityEvent[];
  jumpTo: (s: number) => void;
  mode?: "default" | "blind" | "lv" | "deaf" | "cognitive";
  className?: string;
  captionsEnabled?: boolean;
  visualCompanionEnabled?: boolean;
}

export function ContextualIntelligencePanel({
  currentTime,
  segments,
  visuals,
  analysis,
  missing,
  adCues,
  jumpTo,
  className,
  captionsEnabled = true,
  visualCompanionEnabled = true,
}: ContextualIntelligencePanelProps) {
  const [collapsed, setCollapsed] = React.useState<Record<string, boolean>>({});
  const toggle = (id: string) =>
    setCollapsed((c) => ({ ...c, [id]: !c[id] }));

  // Find active content around currentTime
  const range = 2.5;
  const activeSegment = segments.find(
    (s) => currentTime >= s.start - range * 0.5 && currentTime <= (s.end ?? s.start) + range
  ) ?? [...segments].reverse().find((s) => s.start <= currentTime);

  const activeVisual = visuals.find(
    (v) => currentTime >= v.start - 0.5 && currentTime <= (v.end ?? v.start) + range
  ) ?? [...visuals].reverse().find((v) => v.start <= currentTime);

  const activeAnalysis = analysis.find(
    (a) =>
      (a.start ?? 0) - 0.5 <= currentTime &&
      ((a.end ?? a.start ?? 0) + range) >= currentTime
  ) ?? [...analysis].reverse().find((a) => (a.start ?? 0) <= currentTime);

  const activeGap = missing.find(
    (m) => {
      const s = m.timestamp_start ?? m.timestamp;
      const e = m.timestamp_end ?? s + 3;
      return s - 0.5 <= currentTime && e + 1 >= currentTime;
    }
  ) ?? [...missing].reverse().find((m) => (m.timestamp_start ?? m.timestamp) <= currentTime);

  const activeAd = adCues.find(
    (c) => c.start - 0.5 <= currentTime && (c.end ?? c.start + 2) + 1 >= currentTime
  ) ?? [...adCues].reverse().find((c) => c.start <= currentTime);

  const renderCollapsible = (
    section: SectionDef,
    content: React.ReactNode,
    defaultOpen = true
  ) => {
    const isCollapsed = collapsed[section.id] ?? !defaultOpen;
    const Icon = section.Icon;
    return (
      <div
        className="rounded-xl border border-[#DDD0C0] bg-[#FFFDFC] shadow-xs overflow-hidden"
        key={section.id}
      >
        <button
          type="button"
          onClick={() => toggle(section.id)}
          className="w-full flex items-center gap-2.5 px-3.5 py-2.5 hover:bg-[#FBF8F2] transition text-left"
        >
          <div className={cn("shrink-0 size-7 rounded-lg flex items-center justify-center", section.bgCls, section.colorCls)}>
            <Icon className="size-3.5" aria-hidden />
          </div>
          <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#51483F]">{section.label}</span>
          <div className="ml-auto flex items-center gap-1.5">
            {isCollapsed ? (
              <ChevronRight className="size-3.5 text-[#7A7067]" aria-hidden />
            ) : (
              <ChevronDown className="size-3.5 text-[#7A7067]" aria-hidden />
            )}
          </div>
        </button>
        {!isCollapsed && (
          <div className="px-3.5 pb-3.5 pt-0.5 space-y-2 border-t border-[#EDE2D3]">
            {content}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside
      className={cn(
        "flex h-full flex-col gap-3 bg-transparent p-0 overflow-y-auto scrollbar-thin text-[#2F2924]",
        className
      )}
    >
      {/* Panel Identity */}
      <div className="rounded-2xl border border-[#DDD0C0] bg-[#FFFDFC] shadow-xs p-3.5">
        <div className="flex items-center gap-2.5 mb-2.5">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#FFF8F4] border border-[#E8C2B2] text-[#B85C38] shadow-xs">
            <BrainCircuit className="size-4.5" aria-hidden />
          </div>
          <div className="min-w-0">
            <p className="text-[13px] font-bold tracking-tight text-[#2F2924] leading-none">
              Contextual Intelligence
            </p>
            <p className="font-mono text-[10.5px] text-[#7A7067] mt-1 flex items-center gap-1">
              <Clock className="size-2.5 text-[#8B6B52]" aria-hidden />
              Synced to {formatClock(currentTime)}
            </p>
          </div>
        </div>
        <div className="flex items-center justify-between rounded-lg bg-[#FBF8F2] border border-[#EDE2D3] px-2.5 py-1.5">
          <div className="flex items-center gap-2">
            <Gauge className="size-3 text-[#B85C38]" aria-hidden />
            <span className="text-[11px] font-semibold text-[#51483F]">
              Active inference window
            </span>
          </div>
          <span className="font-mono text-[10px] text-[#7A7067] tabular-nums font-bold">
            ±{range}s
          </span>
        </div>
      </div>

      {/* 6 Sections */}
      {visualCompanionEnabled && renderCollapsible(
        SECTIONS[0],
        activeVisual ? (
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[10.5px] font-mono font-bold bg-[#F2F7F7] text-[#5F9A9A] border border-[#D2E4E4]">{activeVisual.type || "VISUAL"}</span>
              {activeVisual.importance !== undefined && (
                <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10.5px] font-mono text-[#7A7067] bg-[#F1E8DC]">
                  importance {activeVisual.importance}
                </span>
              )}
              <EvidenceTimestamp
                seconds={activeVisual.start}
                onSeek={jumpTo}
                source="KEYFRAME"
                tone="cyan"
              />
            </div>
            <EvidenceSnippet
              variant="visual"
              text={activeVisual.description || activeVisual.ocr_text || "Visual content frame detected."}
            />
            {activeVisual.ocr_text && (
              <div className="rounded-lg border border-[#DDD8EE] bg-[#F6F5FB] p-2.5 space-y-1">
                <span className="font-mono text-[10px] font-bold text-[#6C63A8] inline-flex items-center gap-1 uppercase tracking-wider">
                  <ScanText className="size-2.5" aria-hidden />
                  INLINE OCR
                </span>
                <p className="text-[11.5px] font-mono text-[#2F2924] leading-relaxed whitespace-pre-wrap">
                  {activeVisual.ocr_text}
                </p>
              </div>
            )}
          </div>
        ) : (
          <EmptyState label="No visual event at this timestamp" hint="Seek to a moment with visual content." />
        ),
        true
      )}

      {captionsEnabled && renderCollapsible(
        SECTIONS[1],
        activeSegment ? (
          <div className="space-y-2">
            <EvidenceTimestamp
              seconds={activeSegment.start}
              onSeek={jumpTo}
              source="WHISPER TRANSCRIPT"
              tone="blue"
            />
            <EvidenceSnippet variant="speech" text={activeSegment.text} />
          </div>
        ) : (
          <EmptyState label="No speech segment at this moment" hint="Seek to a moment when the instructor is speaking." />
        ),
        true
      )}

      {visualCompanionEnabled && renderCollapsible(
        SECTIONS[2],
        activeAnalysis?.ocr_text ? (
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[10.5px] font-mono font-bold bg-[#F6F5FB] text-[#6C63A8] border border-[#DDD8EE]">OCR EXTRACTED</span>
              {activeAnalysis.trust && (
                <TrustPill
                  trust={
                    (typeof activeAnalysis.trust === "string"
                      ? activeAnalysis.trust
                      : activeAnalysis.trust?.trust) as TrustLevel
                  }
                  compact
                />
              )}
              {activeAnalysis.start !== undefined && (
                <EvidenceTimestamp seconds={activeAnalysis.start} onSeek={jumpTo} source="FRAME" tone="indigo" />
              )}
            </div>
            <div className="rounded-lg border border-[#DDD8EE] bg-[#F6F5FB] p-2.5">
              <p className="text-[11.5px] font-mono text-[#2F2924] leading-relaxed whitespace-pre-wrap">
                {activeAnalysis.ocr_text}
              </p>
            </div>
          </div>
        ) : (
          <EmptyState label="No OCR text aligned to this moment" hint="OCR extraction is performed on detected keyframes with written content." />
        ),
        false
      )}

      {renderCollapsible(
        SECTIONS[3],
        activeGap ? (
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[10.5px] font-mono font-bold bg-[#FEF6EC] text-[#B77932] border border-[#F3CE9D]">ACCESSIBILITY GAP</span>
              {activeGap.severity && (
                <span
                  className={cn(
                    "inline-flex items-center rounded-full px-2 py-0.5 text-[10.5px] font-mono font-semibold border",
                    activeGap.severity === "high"
                      ? "bg-[#FDF2F2] text-[#B94A48] border-[#B94A48]/30"
                      : activeGap.severity === "low"
                      ? "bg-[#F2F7F7] text-[#5F9A9A] border-[#D2E4E4]"
                      : "bg-[#FEF6EC] text-[#B77932] border-[#F3CE9D]"
                  )}
                >
                  {String(activeGap.severity).toUpperCase()} SEVERITY
                </span>
              )}
              <EvidenceTimestamp
                seconds={activeGap.timestamp_start ?? activeGap.timestamp}
                onSeek={jumpTo}
                source="DISPARITY"
                tone="amber"
              />
            </div>
            <EvidenceSnippet
              variant="gap"
              text={activeGap.missing_information || "Visual content is not explained in spoken audio."}
              timestamp={activeGap.timestamp_start ?? activeGap.timestamp}
              onSeek={jumpTo}
              trust={
                (typeof activeGap.trust === "string"
                  ? activeGap.trust
                  : activeGap.trust?.trust) as TrustLevel
              }
            />
            {activeGap.why_it_matters && (
              <p className="text-[11.5px] leading-relaxed text-[#51483F] px-1">
                <span className="font-semibold text-[#2F2924]">Why it matters: </span>
                {activeGap.why_it_matters}
              </p>
            )}
            <button
              onClick={() =>
                jumpTo(activeGap.timestamp_start ?? activeGap.timestamp ?? 0)
              }
              className="inline-flex items-center gap-1.5 rounded-lg bg-[#B85C38] text-white px-2.5 py-1.5 text-[11px] font-bold hover:bg-[#9F4F32] transition shadow-xs"
            >
              <Play className="size-3 fill-current" aria-hidden />
              Jump to gap moment
            </button>
          </div>
        ) : (
          <div className="rounded-xl border border-[#C5E3C7] bg-[#EBF5EC] p-2.5 flex items-start gap-2">
            <ShieldCheck className="size-4 text-[#5F8A62] shrink-0 mt-0.5" aria-hidden />
            <div>
              <p className="text-[11.5px] font-bold text-[#2D5A30]">
                No accessibility gap at this timestamp.
              </p>
              <p className="text-[10.5px] text-[#3D6B40]">
                Spoken and visual modalities appear aligned.
              </p>
            </div>
          </div>
        ),
        true
      )}

      {renderCollapsible(
        SECTIONS[4],
        activeAd ? (
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10.5px] font-mono font-bold bg-[#EBF5EC] text-[#3D6B40] border border-[#C5E3C7]">
                <Volume2 className="size-2.5" aria-hidden />
                AUDIO DESCRIPTION CUE
              </span>
              <EvidenceTimestamp seconds={activeAd.start} onSeek={jumpTo} source="AD LAYER" tone="emerald" />
              {activeAd.confidence !== undefined && (
                <TrustPill
                  trust={activeAd.confidence > 0.75 ? "VERIFIED" : "UNCERTAIN"}
                  compact
                />
              )}
            </div>
            <EvidenceSnippet
              variant="ad"
              text={activeAd.description || activeAd.transcript || "[Non-destructive audio description narration]"}
            />
            {activeAd.should_describe && (
              <p className="text-[11px] text-[#3D6B40] px-1 font-medium">
                EduAccess layered this cue non-destructively over the original lecture audio.
              </p>
            )}
          </div>
        ) : (
          <EmptyState label="No AD cue active at this moment" hint="The system inserts cues only where a visual gap requires remediation." />
        ),
        false
      )}

      {renderCollapsible(
        SECTIONS[5],
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-1.5">
            <div className="rounded-lg bg-[#FBF8F2] border border-[#EDE2D3] p-2">
              <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-[#7A7067] block">MODALITIES</span>
              <div className="mt-1 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10.5px] text-[#51483F]">Speech</span>
                  <span className={cn("size-1.5 rounded-full", activeSegment ? "bg-[#5B82A6]" : "bg-[#DDD0C0]")} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10.5px] text-[#51483F]">Vision</span>
                  <span className={cn("size-1.5 rounded-full", activeVisual ? "bg-[#5F9A9A]" : "bg-[#DDD0C0]")} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10.5px] text-[#51483F]">OCR</span>
                  <span className={cn("size-1.5 rounded-full", activeAnalysis?.ocr_text ? "bg-[#6C63A8]" : "bg-[#DDD0C0]")} />
                </div>
              </div>
            </div>
            <div className="rounded-lg bg-[#FBF8F2] border border-[#EDE2D3] p-2">
              <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-[#7A7067] block">ACCESSIBILITY</span>
              <div className="mt-1 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10.5px] text-[#51483F]">Gap</span>
                  <span className={cn("size-1.5 rounded-full", activeGap ? "bg-[#B77932]" : "bg-[#DDD0C0]")} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10.5px] text-[#51483F]">AD</span>
                  <span className={cn("size-1.5 rounded-full", activeAd ? "bg-[#5F8A62]" : "bg-[#DDD0C0]")} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10.5px] text-[#51483F]">Events</span>
                  <span className="size-1.5 rounded-full bg-[#B85C38]" />
                </div>
              </div>
            </div>
          </div>

          <SectionRail
            label={<span className="font-mono text-[9px] font-bold uppercase tracking-wider text-[#7A7067]">TIMESTAMPED EVIDENCE</span>}
          />
          <div className="flex flex-wrap items-center gap-1.5">
            <EvidenceTimestamp seconds={Math.max(0, currentTime - 2)} onSeek={jumpTo} source="-2s" tone="slate" />
            <EvidenceTimestamp seconds={currentTime} onSeek={jumpTo} source="NOW" trust="VERIFIED" tone="terracotta" />
            <EvidenceTimestamp seconds={currentTime + 2} onSeek={jumpTo} source="+2s" tone="slate" />
          </div>

          <p className="text-[10.5px] leading-relaxed text-[#7A7067] px-1">
            All EduAccess outputs are grounded in the source lecture material and marked with
            a trust level. Use <span className="font-semibold text-[#2F2924]">Jump to moment</span> to
            verify any AI claim against the original video.
          </p>
        </div>,
        false
      )}
    </aside>
  );
}

function EmptyState({ label, hint }: { label: string; hint: string }) {
  return (
    <div className="rounded-xl border border-[#EDE2D3] bg-[#FBF8F2] p-3 text-center">
      <p className="text-[11.5px] font-medium text-[#51483F]">{label}</p>
      <p className="text-[10px] text-[#7A7067] mt-0.5">{hint}</p>
    </div>
  );
}
