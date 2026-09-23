"use client";

import * as React from "react";
import { motion, useReducedMotion } from "motion/react";
import { cn } from "@/lib/format";
import { resolveReducedMotion } from "@/lib/accessibilityPreferences.mjs";
import { ScoreRing } from "@/components/ui/score-ring";
import { ArrowUpRight, ArrowDownRight, ExternalLink } from "lucide-react";

export interface HealthComponent {
  key: string;
  label: string;
  value: number;
  contribution: number;
  effect?: "benefit" | "penalty" | "neutral";
  detail?: string;
}

export interface HealthDiagnosticProps {
  overall: number;
  components: HealthComponent[];
  methodology?: string;
  reportLink?: string;
  onNavigateReport?: () => void;
}

const STEP_COLORS = {
  baseline: "#3B82F6",
  disparities: "#D97706",
  remediation: "#16A34A",
  final: "#6C4FF7",
};

const STEP_STAGGER = [0.1, 0.35, 0.6, 0.9];

interface StepColorWrap {
  bgFill: string;
  bgBorder: string;
  text: string;
  pillBg: string;
  rail: string;
}

function stepStyleVars(hex: string): StepColorWrap {
  return {
    bgFill: hex + "26",
    bgBorder: hex + "CC",
    text: hex,
    pillBg: hex + "14",
    rail: hex,
  };
}

function SeverityCounts({ components }: { components: HealthComponent[] }) {
  const penalties = components.filter((c) => c.effect === "penalty");
  const detailJoin = penalties.map((c) => c.detail || "").join(" ");
  const critical = (detailJoin.match(/CRITICAL|critical/g) || []).length;
  const high = (detailJoin.match(/HIGH|high/g) || []).length;
  const medium = (detailJoin.match(/MEDIUM|medium/g) || []).length;
  if (critical === 0 && high === 0 && medium === 0 && penalties.length === 0) return null;
  const fallbackCritical = penalties.filter((c) => c.contribution <= -20).length;
  const fallbackHigh = penalties.filter((c) => c.contribution > -20 && c.contribution <= -10).length;
  const fallbackMedium = penalties.filter((c) => c.contribution > -10 && c.contribution < 0).length;
  const cCount = critical || fallbackCritical;
  const hCount = high || fallbackHigh;
  const mCount = medium || fallbackMedium;
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {cCount > 0 && (
        <span className="inline-flex items-center gap-1 rounded-md border border-rose-500/30 bg-rose-500/10 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-rose-300">
          Critical {cCount}
        </span>
      )}
      {hCount > 0 && (
        <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-amber-300">
          High {hCount}
        </span>
      )}
      {mCount > 0 && (
        <span className="inline-flex items-center gap-1 rounded-md border border-slate-500/30 bg-slate-500/10 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-slate-300">
          Medium {mCount}
        </span>
      )}
    </div>
  );
}

function RemediatedCount({ components }: { components: HealthComponent[] }) {
  const benefits = components.filter((c) => c.effect === "benefit");
  const remediatedKeys = components.filter(
    (c) => c.key.toLowerCase().includes("remedi") || c.effect === "benefit"
  );
  const detailJoin = remediatedKeys.map((c) => c.detail || "").join(" ");
  const countMatches = (detailJoin.match(/\d+/g) || []).map(Number).reduce((a, b) => a + b, 0);
  const count = countMatches > 0 ? countMatches : benefits.length || undefined;
  if (!count) return null;
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
      {count} remediated gap{count === 1 ? "" : "s"}
    </span>
  );
}

export function HealthDiagnostic({
  overall,
  components,
  methodology = "Modality Baseline + Verified Remediation − Unresolved Penalty",
  reportLink,
  onNavigateReport,
}: HealthDiagnosticProps) {
  const prefersReducedMotion = useReducedMotion();
  const [motionPreference, setMotionPreference] = React.useState({ explicit: false, reduced: false });

  React.useEffect(() => {
    const root = document.documentElement;
    const sync = () => setMotionPreference({
      explicit: root.classList.contains("motion-preference-set"),
      reduced: root.classList.contains("reduced-motion"),
    });
    sync();
    const obs = new MutationObserver(sync);
    obs.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => obs.disconnect();
  }, []);

  const reduced = resolveReducedMotion(
    motionPreference.explicit ? motionPreference.reduced : undefined,
    prefersReducedMotion
  );

  const step0 = components[0];
  const step1 = components[1];
  const step2 = components[2];
  const step3 = components[3];
  const extras = components.length > 4 ? components.slice(4) : [];

  const baselineStyle = stepStyleVars(STEP_COLORS.baseline);
  const disparitiesStyle = stepStyleVars(STEP_COLORS.disparities);
  const remediationStyle = stepStyleVars(STEP_COLORS.remediation);
  const finalStyle = stepStyleVars(STEP_COLORS.final);

  const stepAnim = (idx: number) =>
    reduced
      ? { opacity: 1, y: 0 }
      : {
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: {
            delay: STEP_STAGGER[idx],
            duration: 0.45,
            ease: [0.2, 0.8, 0.2, 1] as [number, number, number, number],
          },
        };

  const railAnim = (idx: number) =>
    reduced
      ? { scaleY: 1 }
      : {
          initial: { scaleY: 0 },
          animate: { scaleY: 1 },
          transition: {
            delay: STEP_STAGGER[idx] - 0.02,
            duration: 0.5,
            ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
          },
        };

  return (
    <section
      role="region"
      aria-label="Accessibility health diagnostic waterfall showing Baseline coverage, Unmitigated disparity penalties, Verified remediation benefit, and the final accessibility health score."
      className="w-full rounded-2xl border border-white/10 bg-[#0B1020] shadow-2xl shadow-black/40 overflow-hidden"
    >
      <div className="flex flex-col">
        <div className="relative flex gap-6 p-6 md:p-8">
          <div className="relative flex flex-col items-center pt-6 shrink-0" style={{ width: 48 }}>
            <div className="absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-[2px] bg-white/5" />
            <div
              className="relative flex flex-col items-center w-full flex-1"
              style={{ minHeight: "calc(100% - 0px)" }}
            >
              <div className="flex flex-col w-full flex-1">
                <div className="relative w-full flex-1 min-h-[140px]">
                  <motion.div
                    {...railAnim(0)}
                    className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[2px] origin-top"
                    style={{ backgroundColor: baselineStyle.rail }}
                  />
                </div>
                <div className="relative w-full flex-1 min-h-[140px]">
                  <motion.div
                    {...railAnim(1)}
                    className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[2px] origin-top"
                    style={{ backgroundColor: disparitiesStyle.rail }}
                  />
                </div>
                <div className="relative w-full flex-1 min-h-[140px]">
                  <motion.div
                    {...railAnim(2)}
                    className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[2px] origin-top"
                    style={{ backgroundColor: remediationStyle.rail }}
                  />
                </div>
                <div className="relative w-full flex-1 min-h-[140px]">
                  <motion.div
                    {...railAnim(3)}
                    className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[2px] origin-top"
                    style={{ backgroundColor: finalStyle.rail }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-6 min-w-0">
            <motion.div
              {...stepAnim(0)}
              className="relative flex items-start gap-5"
            >
              <div
                className="shrink-0 flex items-center justify-center rounded-full border-2 font-bold text-[14px]"
                style={{
                  width: 48,
                  height: 48,
                  backgroundColor: baselineStyle.bgFill,
                  borderColor: baselineStyle.bgBorder,
                  color: baselineStyle.text,
                }}
              >
                01
              </div>
              <div className="flex-1 min-w-0 pt-1.5">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="min-w-0">
                    <p
                      className="font-mono text-[10px] uppercase tracking-[0.18em] font-semibold"
                      style={{ color: baselineStyle.text }}
                    >
                      Baseline Accessibility
                    </p>
                    <p className="mt-1 text-[12px] text-slate-400 leading-relaxed">
                      Speech + Visuals coverage baseline
                    </p>
                  </div>
                  <div
                    className="rounded-xl border px-4 py-3 flex items-center gap-2"
                    style={{
                      backgroundColor: "#070A14",
                      borderColor: baselineStyle.bgBorder + "30",
                    }}
                  >
                    <span
                      className="text-[28px] font-semibold leading-none"
                      style={{ color: baselineStyle.text }}
                    >
                      +{step0?.value ?? 0}%
                    </span>
                  </div>
                </div>
                <div className="mt-3 rounded-lg border border-white/5 bg-[#070A14]/60 px-3 py-2">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
                    Component Contribution ·{" "}
                  </span>
                  <span className="font-mono text-[10px] text-slate-300">
                    {step0?.key ?? "baseline"} · +{step0?.contribution ?? 0}
                  </span>
                </div>
              </div>
            </motion.div>

            <motion.div
              {...stepAnim(1)}
              className="relative flex items-start gap-5"
            >
              <div
                className="shrink-0 flex items-center justify-center rounded-full border-2 font-bold text-[14px]"
                style={{
                  width: 48,
                  height: 48,
                  backgroundColor: disparitiesStyle.bgFill,
                  borderColor: disparitiesStyle.bgBorder,
                  color: disparitiesStyle.text,
                }}
              >
                02
              </div>
              <div className="flex-1 min-w-0 pt-1.5">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="min-w-0">
                    <p
                      className="font-mono text-[10px] uppercase tracking-[0.18em] font-semibold"
                      style={{ color: disparitiesStyle.text }}
                    >
                      Unmitigated Disparities
                    </p>
                    <p className="mt-1 text-[12px] text-slate-400 leading-relaxed">
                      Visuals not verbalized, unresolved gaps
                    </p>
                    <div className="mt-3">
                      <SeverityCounts components={components} />
                    </div>
                  </div>
                  <div
                    className="rounded-xl border px-4 py-3 flex items-center gap-2"
                    style={{
                      backgroundColor: "#070A14",
                      borderColor: disparitiesStyle.bgBorder + "30",
                    }}
                  >
                    <ArrowDownRight
                      className="w-5 h-5 shrink-0 text-rose-400"
                      aria-hidden
                    />
                    <span
                      className="text-[28px] font-semibold leading-none"
                      style={{ color: disparitiesStyle.text }}
                    >
                      -{Math.abs(step1?.value ?? 0)}%
                    </span>
                  </div>
                </div>
                <div className="mt-3 rounded-lg border border-white/5 bg-[#070A14]/60 px-3 py-2">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
                    Component Contribution ·{" "}
                  </span>
                  <span className="font-mono text-[10px] text-slate-300">
                    {step1?.key ?? "unresolved_disparities"} ·{" "}
                    {Math.abs(step1?.contribution ?? 0) > 0 && (step1?.contribution ?? 0) >= 0
                      ? "+"
                      : ""}
                    {step1?.contribution ?? 0}
                  </span>
                </div>
              </div>
            </motion.div>

            <motion.div
              {...stepAnim(2)}
              className="relative flex items-start gap-5"
            >
              <div
                className="shrink-0 flex items-center justify-center rounded-full border-2 font-bold text-[14px]"
                style={{
                  width: 48,
                  height: 48,
                  backgroundColor: remediationStyle.bgFill,
                  borderColor: remediationStyle.bgBorder,
                  color: remediationStyle.text,
                }}
              >
                03
              </div>
              <div className="flex-1 min-w-0 pt-1.5">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="min-w-0">
                    <p
                      className="font-mono text-[10px] uppercase tracking-[0.18em] font-semibold"
                      style={{ color: remediationStyle.text }}
                    >
                      Verified Remediation
                    </p>
                    <p className="mt-1 text-[12px] text-slate-400 leading-relaxed">
                      Verified audio description cues authored on disk
                    </p>
                    <div className="mt-3">
                      <RemediatedCount components={components} />
                    </div>
                  </div>
                  <div
                    className="rounded-xl border px-4 py-3 flex items-center gap-2"
                    style={{
                      backgroundColor: "#070A14",
                      borderColor: remediationStyle.bgBorder + "30",
                    }}
                  >
                    <ArrowUpRight
                      className="w-5 h-5 shrink-0 text-emerald-400"
                      aria-hidden
                    />
                    <span
                      className="text-[28px] font-semibold leading-none"
                      style={{ color: remediationStyle.text }}
                    >
                      +{step2?.value ?? 0}%
                    </span>
                  </div>
                </div>
                <div className="mt-3 rounded-lg border border-white/5 bg-[#070A14]/60 px-3 py-2">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
                    Component Contribution ·{" "}
                  </span>
                  <span className="font-mono text-[10px] text-slate-300">
                    {step2?.key ?? "verified_remediation"} · +{step2?.contribution ?? 0}
                  </span>
                </div>
              </div>
            </motion.div>

            <motion.div
              {...stepAnim(3)}
              className="relative flex items-start gap-5"
            >
              <div
                className="shrink-0 flex items-center justify-center rounded-full border-2 font-bold text-[14px]"
                style={{
                  width: 48,
                  height: 48,
                  backgroundColor: finalStyle.bgFill,
                  borderColor: finalStyle.bgBorder,
                  color: finalStyle.text,
                }}
              >
                04
              </div>
              <div
                className="flex-1 min-w-0 rounded-2xl border p-5 md:p-6"
                style={{
                  backgroundColor: "#070A14",
                  borderColor: finalStyle.bgBorder + "40",
                }}
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                  <div className="min-w-0 flex-1">
                    <p
                      className="font-mono text-[10px] uppercase tracking-[0.18em] font-semibold"
                      style={{ color: finalStyle.text }}
                    >
                      Final Accessibility Health
                    </p>
                    <p className="mt-1.5 text-[11px] text-slate-400 leading-relaxed">
                      {methodology}
                    </p>
                    <div className="mt-5">
                      <div className="flex items-baseline gap-2">
                        <span
                          className="text-[32px] font-semibold leading-none"
                          style={{ color: finalStyle.text }}
                        >
                          {overall}%
                        </span>
                      </div>
                      <p className="mt-2 text-[11px] text-slate-500 leading-relaxed max-w-sm">
                        Modality Baseline + Verified Remediation − Unresolved Penalty
                      </p>
                    </div>
                  </div>
                  <div className="shrink-0 flex items-center justify-center">
                    <ScoreRing
                      score={overall}
                      label=""
                      sublabel=""
                      size={140}
                      color="from-brand-indigo to-brand-cyan"
                    />
                  </div>
                </div>
                <div className="mt-5 rounded-lg border border-white/5 bg-[#0B1020]/60 px-3 py-2">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
                    Terminal Component ·{" "}
                  </span>
                  <span className="font-mono text-[10px] text-slate-300">
                    {step3?.key ?? "evidence_trust"} ·{" "}
                    {(step3?.contribution ?? 0) >= 0 ? "+" : ""}
                    {step3?.contribution ?? 0}
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>

        {extras.length > 0 && (
          <motion.div
            {...(reduced
              ? { opacity: 1 }
              : {
                  initial: { opacity: 0, y: 8 },
                  animate: { opacity: 1, y: 0 },
                  transition: { delay: 1.1, duration: 0.4 },
                })}
            className="px-6 md:px-8 pb-0"
          >
            <div className="rounded-xl border border-white/10 bg-[#070A14] overflow-hidden">
              <div className="px-4 py-2.5 border-b border-white/5 bg-[#0B1020]">
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] font-semibold text-slate-400">
                  Supplemental Diagnostic Components
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[11px] border-collapse">
                  <thead>
                    <tr className="bg-white/[0.02]">
                      <th className="text-left px-4 py-2.5 font-mono uppercase tracking-wider text-[9px] text-slate-500 font-semibold border-b border-white/[0.08]">
                        Key
                      </th>
                      <th className="text-left px-4 py-2.5 font-mono uppercase tracking-wider text-[9px] text-slate-500 font-semibold border-b border-white/[0.08]">
                        Label
                      </th>
                      <th className="text-right px-4 py-2.5 font-mono uppercase tracking-wider text-[9px] text-slate-500 font-semibold border-b border-white/[0.08]">
                        Value
                      </th>
                      <th className="text-right px-4 py-2.5 font-mono uppercase tracking-wider text-[9px] text-slate-500 font-semibold border-b border-white/[0.08]">
                        Contribution
                      </th>
                      <th className="text-left px-4 py-2.5 font-mono uppercase tracking-wider text-[9px] text-slate-500 font-semibold border-b border-white/[0.08]">
                        Detail
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {extras.map((c, i) => (
                      <tr
                        key={c.key + "_" + i}
                        className="border-b border-white/[0.06] last:border-b-0 hover:bg-white/[0.02]"
                      >
                        <td className="px-4 py-2.5 font-mono text-slate-300 whitespace-nowrap">
                          {c.key}
                        </td>
                        <td className="px-4 py-2.5 text-slate-300">{c.label}</td>
                        <td className="px-4 py-2.5 text-right tabular-nums text-slate-300">
                          {c.value}%
                        </td>
                        <td
                          className={cn(
                            "px-4 py-2.5 text-right tabular-nums font-semibold",
                            c.contribution > 0
                              ? "text-emerald-400"
                              : c.contribution < 0
                              ? "text-amber-400"
                              : "text-slate-400"
                          )}
                        >
                          {c.contribution >= 0 ? "+" : ""}
                          {c.contribution}
                        </td>
                        <td className="px-4 py-2.5 text-slate-400 max-w-[260px] truncate">
                          {c.detail || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}

        <div
          className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-white/5 bg-[#070A14] px-6 md:px-8 py-4"
        >
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] font-semibold text-slate-500">
            Methodology · Baseline + Verified Remediation − Unresolved Penalty
          </p>
          {(reportLink || onNavigateReport) && (
            <button
              type="button"
              onClick={() => {
                if (onNavigateReport) {
                  onNavigateReport();
                } else if (reportLink) {
                  window.open(reportLink, "_blank", "noopener,noreferrer");
                }
              }}
              className="inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-[11px] font-semibold text-white transition-all hover:opacity-90"
              style={{ backgroundColor: STEP_COLORS.final }}
            >
              View full audit
              <ExternalLink className="w-3.5 h-3.5" aria-hidden />
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
