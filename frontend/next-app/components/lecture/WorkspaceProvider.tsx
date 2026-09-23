"use client";

import * as React from "react";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { listLectures, getResult } from "@/lib/api";
import type { LectureRecord } from "@/types/backend";

interface WorkspaceValue {
  lectures: LectureRecord[];
  loading: boolean;
  error: string | null;
  selectedId: string | null;
  setSelectedId: (id: string | null) => void;
  selected?: LectureRecord;
  result?: Record<string, unknown>;
  refresh: () => Promise<void>;
}

const Ctx = createContext<WorkspaceValue | null>(null);

export function useWorkspace(): WorkspaceValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return v;
}

export function WorkspaceProvider({
  children,
  initialJobId,
}: {
  children: React.ReactNode;
  initialJobId?: string;
}) {
  const searchParams = useSearchParams();
  const [lectures, setLectures] = useState<LectureRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedIdState] = useState<string | null>(initialJobId ?? null);
  const [result, setResult] = useState<Record<string, unknown>>();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listLectures();
      setLectures(data.lectures);
      const param = searchParams.get("job");
      const isAvailable = (id: string | null) => Boolean(id && data.lectures.some((l) => l.job_id === id));

      if (initialJobId) {
        setSelectedIdState(initialJobId);
      } else if (isAvailable(param)) {
        setSelectedIdState(param);
      }
      // Never auto-select default demo lecture on general pages
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load lectures");
    } finally {
      setLoading(false);
    }
  }, [searchParams, initialJobId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const param = searchParams.get("job");
    if (param) setSelectedIdState(param);
  }, [searchParams]);

  const setSelectedId = useCallback((id: string | null) => {
    setSelectedIdState(id);
    if (typeof window !== "undefined" && id) {
      window.dispatchEvent(
        new CustomEvent("eduaccess:lecture-change", { detail: { jobId: id } })
      );
    }
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setResult(undefined);
      return;
    }
    let cancelled = false;
    getResult(selectedId)
      .then((r) => {
        if (!cancelled) setResult(r);
      })
      .catch(() => {
        if (!cancelled) setResult(undefined);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const selected =
    lectures.find((l) => l.job_id === selectedId || l.job_id.toLowerCase() === selectedId?.toLowerCase()) ??
    (selectedId
      ? {
          job_id: selectedId,
          filename: selectedId.endsWith(".mp4") ? selectedId : `${selectedId}.mp4`,
          status: "done",
          assets: {},
          has_result: true,
          cached: true,
        }
      : undefined);

  return (
    <Ctx.Provider
      value={{
        lectures,
        loading,
        error,
        selectedId,
        setSelectedId,
        selected,
        result,
        refresh: load,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
