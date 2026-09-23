import type { AskResponse, LectureRecord, LearningProgress, MetricsResponse } from "@/types/backend";
import { fileBaseName } from "@/lib/format";
import * as demoStore from "./demoStore";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export type BackendState = "CONFIGURED_OK" | "UNCONFIGURED" | "UNAVAILABLE";

export function isDemoModeEnabled(): boolean {
  const envGate = process.env.NEXT_PUBLIC_ENABLE_DEMO_MODE === "1";
  if (envGate) return true;
  if (typeof window !== "undefined") {
    try {
      return window.localStorage.getItem("eduaccess:dev:demo-mode") === "1";
    } catch {
      return false;
    }
  }
  return false;
}

export function resolveBackendState(): { state: BackendState; url: string | null } {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  let url: string | null = null;
  if (envUrl && envUrl.trim()) {
    url = envUrl.trim().replace(/\/$/, "");
  }
  if (!url && typeof window !== "undefined") {
    const win = (window as unknown as { __API_BASE_URL__?: string });
    if (win.__API_BASE_URL__ && win.__API_BASE_URL__.trim()) {
      url = win.__API_BASE_URL__.trim().replace(/\/$/, "");
    }
  }
  if (!url) {
    return { state: "UNCONFIGURED", url: null };
  }
  return { state: "CONFIGURED_OK", url };
}

export const apiBase = (): string => {
  return resolveBackendState().url ?? "";
};

function readableFetchError(path: string, err: unknown): ApiError {
  if (err instanceof ApiError) return err;
  const msg = err instanceof Error ? err.message : String(err);
  return new ApiError(503, `Backend unavailable. Please try again later. (${path} — ${msg})`);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const { state, url } = resolveBackendState();

  if (state === "UNCONFIGURED") {
    if (isDemoModeEnabled()) {
      return dispatchDemoRequest_INTERNAL<T>(path, init);
    }
    throw new ApiError(500, "EduAccess AI processing service is not configured.");
  }

  try {
    const res = await fetch(`${url}${path}`, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });

    if (res.ok) {
      return (await res.json()) as T;
    }

    let detail = res.statusText;
    try {
      const errBody = await res.json();
      if (errBody && typeof errBody.detail === "string") detail = errBody.detail;
      else if (errBody && typeof errBody === "string") detail = errBody;
    } catch {
      // ignore
    }

    if (res.status === 413) throw new ApiError(413, detail || "File too large (max 512 MB).");
    if (res.status === 415) throw new ApiError(415, detail || "Unsupported video format.");
    if (res.status === 400) throw new ApiError(400, detail || "Invalid request.");
    if (res.status === 404) throw new ApiError(404, detail || "Resource not found.");
    if (res.status >= 500) throw new ApiError(res.status, detail || "Backend server error. Please try again later.");
    throw new ApiError(res.status, detail || `Request failed (${res.status}).`);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (isDemoModeEnabled()) {
      return dispatchDemoRequest_INTERNAL<T>(path, init);
    }
    throw readableFetchError(path, err);
  }
}

export function __dispatchDemoRequest_INTERNAL<T>(path: string, init?: RequestInit): T {
  if (!isDemoModeEnabled()) {
    throw new ApiError(403, "Demo mode is disabled.");
  }
  return dispatchDemoRequest_INTERNAL<T>(path, init);
}

function dispatchDemoRequest_INTERNAL<T>(path: string, init?: RequestInit): T {
  const cleanPath = path.split("?")[0];
  const search = path.includes("?") ? new URLSearchParams(path.split("?")[1]) : new URLSearchParams();

  // /health
  if (cleanPath === "/health") {
    return { status: "ok", service: "EduAccess AI", version: "2.0.0-demo" } as T;
  }

  // /system/status
  if (cleanPath === "/system/status") {
    return {
      status: "demo_mode",
      model: "offline_demo_fixtures",
      gemini_api_key_configured: false,
      tts_engine: "offline_cached_wav",
      stt_engine: "offline_cached_segments",
      offline_mode: true,
      total_lectures: 2,
      total_quizzes: 2,
      total_students: 3,
    } as T;
  }

  // /lectures
  if (cleanPath === "/lectures") {
    return { lectures: demoStore.getDemoLectures() } as T;
  }

  // /result/:jobId
  if (cleanPath.startsWith("/result/")) {
    const jobId = decodeURIComponent(cleanPath.replace("/result/", ""));
    const job = demoStore.getDemoJob(jobId);
    if (!job) throw new ApiError(404, `Job ${jobId} not found`);
    return job as unknown as T;
  }

  // /lectures/:jobId/pipeline-status
  if (cleanPath.includes("/pipeline-status")) {
    const jobId = cleanPath.split("/")[2];
    const job = demoStore.getDemoJob(jobId);
    return {
      job_id: job?.job_id || jobId,
      status: job?.status || "done",
      progress: job?.progress ?? 100,
      current_stage: job?.current_stage || "completed",
      error: job?.error || null,
      logs: job?.logs || [],
    } as T;
  }

  // /lectures/:jobId/timeline
  if (cleanPath.includes("/timeline")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoTimeline(jobId) as T;
  }

  // /lectures/:jobId/missing
  if (cleanPath.includes("/missing")) {
    const jobId = cleanPath.split("/")[2];
    const mode = search.get("mode") || "blind";
    return demoStore.getDemoMissing(jobId, mode) as T;
  }

  // /lectures/:jobId/visual-events
  if (cleanPath.includes("/visual-events")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoVisualEvents(jobId) as T;
  }

  // /lectures/:jobId/visual-understanding
  if (cleanPath.includes("/visual-understanding")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoVisualUnderstanding(jobId) as T;
  }

  // /lectures/:jobId/audio-description
  if (cleanPath.includes("/audio-description")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoAudioDescription(jobId) as T;
  }

  // /lectures/:jobId/transcript
  if (cleanPath.includes("/transcript")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoTranscript(jobId) as T;
  }

  // /lectures/:jobId/accessibility-score
  if (cleanPath.includes("/accessibility-score")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoAccessibilityScore(jobId) as T;
  }

  // /lectures/:jobId/report
  if (cleanPath.includes("/report")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoAccessibilityReport(jobId) as T;
  }

  // /lectures/:jobId/accessibility
  if (cleanPath.includes("/accessibility")) {
    const jobId = cleanPath.split("/")[2];
    const mode = search.get("mode") || "blind";
    return demoStore.getDemoAccessibility(jobId, mode) as T;
  }

  // /lectures/:jobId/metrics
  if (cleanPath.includes("/metrics")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoMetrics(jobId) as T;
  }

  // /lectures/:jobId/presentation
  if (cleanPath.includes("/presentation")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoPresentation(jobId) as T;
  }

  // /lectures/:jobId/replay
  if (cleanPath.includes("/replay")) {
    const jobId = cleanPath.split("/")[2];
    const ts = Number(search.get("timestamp") || 0);
    return demoStore.getDemoReplay(jobId, ts) as T;
  }

  // /lectures/:jobId/knowledge-graph
  if (cleanPath.includes("/knowledge-graph")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoKnowledgeGraph(jobId) as T;
  }

  // /lectures/:jobId/concepts/:concept/explain
  if (cleanPath.includes("/concepts/") && cleanPath.endsWith("/explain")) {
    const parts = cleanPath.split("/");
    const jobId = parts[2];
    const concept = decodeURIComponent(parts[4]);
    return demoStore.getDemoConceptExplanation(jobId, concept) as T;
  }

  // /lectures/:jobId/concepts
  if (cleanPath.includes("/concepts")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoConcepts(jobId) as T;
  }

  // /lectures/:jobId/learning-gaps
  if (cleanPath.includes("/learning-gaps") && !cleanPath.includes("/students/")) {
    const jobId = cleanPath.split("/")[2];
    return demoStore.getDemoLectureGaps(jobId) as T;
  }

  // /lectures/:jobId/students/:studentId/learning-gaps
  if (cleanPath.includes("/students/") && cleanPath.endsWith("/learning-gaps")) {
    const parts = cleanPath.split("/");
    const jobId = parts[2];
    const studentId = parts[4];
    return demoStore.getDemoStudentGaps(jobId, studentId) as T;
  }

  // /quizzes/submit
  if (cleanPath === "/quizzes/submit") {
    const body = init?.body ? JSON.parse(init.body as string) : {};
    return demoStore.submitDemoQuiz(body) as T;
  }

  // /quizzes/:quizId
  if (cleanPath.startsWith("/quizzes/")) {
    const quizId = decodeURIComponent(cleanPath.replace("/quizzes/", ""));
    return demoStore.getDemoQuiz(quizId) as T;
  }

  // /quizzes
  if (cleanPath === "/quizzes") {
    return demoStore.getDemoQuizzes() as T;
  }

  // /students/:studentId/progress
  if (cleanPath.startsWith("/students/") && cleanPath.endsWith("/progress")) {
    const studentId = cleanPath.split("/")[2];
    return demoStore.getDemoStudentProgress(studentId) as T;
  }

  // /students/:studentId/learning-agent
  if (cleanPath.startsWith("/students/") && cleanPath.endsWith("/learning-agent")) {
    const studentId = cleanPath.split("/")[2];
    return demoStore.getDemoLearningAgent(studentId) as T;
  }

  // /students/:studentId/next-action
  if (cleanPath.startsWith("/students/") && cleanPath.endsWith("/next-action")) {
    const studentId = cleanPath.split("/")[2];
    return demoStore.getDemoNextAction(studentId) as T;
  }

  // /students/:studentId/learning-insights
  if (cleanPath.startsWith("/students/") && cleanPath.endsWith("/learning-insights")) {
    const studentId = cleanPath.split("/")[2];
    return demoStore.getDemoLearningInsights(studentId) as T;
  }

  // /students/:studentId/profile
  if (cleanPath.startsWith("/students/") && cleanPath.endsWith("/profile")) {
    const body = init?.body ? JSON.parse(init.body as string) : {};
    return demoStore.saveDemoProfile(body) as T;
  }

  // /students/:studentId
  if (cleanPath.startsWith("/students/") && cleanPath.split("/").length === 3) {
    const studentId = cleanPath.split("/")[2];
    return demoStore.getDemoStudentDetail(studentId) as T;
  }

  // /students
  if (cleanPath === "/students") {
    return demoStore.getDemoStudents() as T;
  }

  // /ask
  if (cleanPath === "/ask") {
    const body = init?.body ? JSON.parse(init.body as string) : {};
    if (!body.job_id) {
      throw new ApiError(400, "job_id is required.");
    }
    return demoStore.askDemoQuestion(body.job_id, body.question || "") as T;
  }

  // /api/v1/assistant/chat or /assistant/chat
  if (cleanPath.includes("/assistant/chat")) {
    const body = init?.body ? JSON.parse(init.body as string) : {};
    return demoStore.chatDemoAssistant(body) as T;
  }

  // /upload
  if (cleanPath === "/upload") {
    return {
      job_id: "DEMO_python_loops",
      filename: "DEMO_python_loops.mp4",
      size_bytes: 444583,
      content_hash: "demo_mode",
      reused_from: null,
    } as T;
  }

  // /process
  if (cleanPath === "/process") {
    return {
      job_id: "DEMO_python_loops",
      status: "queued",
    } as T;
  }

  throw new ApiError(404, `Endpoint ${cleanPath} not found`);
}

export function apiBaseOrThrow(): string {
  const { state, url } = resolveBackendState();
  if (state === "UNCONFIGURED") {
    throw new ApiError(500, "EduAccess AI processing service is not configured.");
  }
  if (!url) {
    throw new ApiError(503, "Backend unavailable. Please try again later.");
  }
  return url;
}

export async function getHealth() {
  return request<{ status: string; service: string; version: string }>("/health");
}

export async function getSystemStatus() {
  return request<import("@/types/backend").SystemStatus>("/system/status");
}

export async function listLectures() {
  return request<{ lectures: LectureRecord[] }>("/lectures");
}

export async function getResult(jobId: string) {
  return request<Record<string, unknown>>(`/result/${encodeURIComponent(jobId)}`);
}

export async function getPipelineStatus(jobId: string) {
  return request<import("@/types/backend").PipelineStatus>(
    `/lectures/${encodeURIComponent(jobId)}/pipeline-status`
  );
}

export async function getTimeline(jobId: string) {
  return request<import("@/types/backend").TimelineResponse>(
    `/lectures/${encodeURIComponent(jobId)}/timeline`
  );
}

export async function getMissing(jobId: string, mode = "blind") {
  return request<import("@/types/backend").MissingResponse>(
    `/lectures/${encodeURIComponent(jobId)}/missing?mode=${encodeURIComponent(mode)}`
  );
}

export async function getVisualEvents(jobId: string) {
  return request<import("@/types/backend").VisualEventsResponse>(
    `/lectures/${encodeURIComponent(jobId)}/visual-events`
  );
}

export async function getVisualUnderstanding(jobId: string) {
  return request<import("@/types/backend").VisualUnderstandingResponse>(
    `/lectures/${encodeURIComponent(jobId)}/visual-understanding`
  );
}

export async function getAudioDescription(jobId: string) {
  return request<import("@/types/backend").AudioDescriptionResponse>(
    `/lectures/${encodeURIComponent(jobId)}/audio-description`
  );
}

export async function getTranscript(jobId: string) {
  return request<{ transcript_text: string; segments: import("@/types/backend").TranscriptSegment[] }>(
    `/lectures/${encodeURIComponent(jobId)}/transcript`
  );
}

export async function getAccessibility(jobId: string, mode = "blind") {
  return request<import("@/types/backend").AccessibilityResult>(
    `/lectures/${encodeURIComponent(jobId)}/accessibility?mode=${encodeURIComponent(mode)}`
  );
}

export async function getAccessibilityScore(jobId: string) {
  return request<import("@/types/backend").AccessibilityScore>(
    `/lectures/${encodeURIComponent(jobId)}/accessibility-score`
  );
}

export async function getAccessibilityReport(jobId: string) {
  return request<import("@/types/backend").AccessibilityReport>(
    `/lectures/${encodeURIComponent(jobId)}/report`
  );
}

export async function getMetrics(jobId: string) {
  return request<MetricsResponse>(`/lectures/${encodeURIComponent(jobId)}/metrics`);
}

export async function getPresentation(jobId: string) {
  return request<Record<string, unknown>>(`/lectures/${encodeURIComponent(jobId)}/presentation`);
}

export async function getReplay(jobId: string, timestamp: number) {
  return request<import("@/types/backend").ReplayResponse>(
    `/lectures/${encodeURIComponent(jobId)}/replay?timestamp=${encodeURIComponent(String(timestamp))}`
  );
}

export async function askQuestion(jobId: string, question: string): Promise<AskResponse> {
  return request<AskResponse>("/ask", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId, question }),
  });
}

export async function listQuizzes() {
  return request<{ quizzes: string[] }>("/quizzes");
}

export async function getQuiz(quizId: string) {
  return request<import("@/types/backend").Quiz>(`/quizzes/${encodeURIComponent(quizId)}`);
}

export async function submitQuiz(payload: {
  quiz_id: string;
  answers: Record<string, string>;
  lesson_title?: string;
  student_id?: string;
}) {
  return request<import("@/types/backend").QuizSubmissionResponse>("/quizzes/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listStudents() {
  return request<{ students: import("@/types/backend").StudentRecord[] }>("/students");
}

export async function getStudent(studentId: string) {
  return request<import("@/types/backend").StudentDetail>(`/students/${encodeURIComponent(studentId)}`);
}

export async function getStudentProgress(studentId: string): Promise<LearningProgress> {
  return request<LearningProgress>(
    `/students/${encodeURIComponent(studentId)}/progress`
  );
}

export async function getKnowledgeGraph(jobId: string) {
  return request<import("@/types/backend").KnowledgeGraphResponse>(
    `/lectures/${encodeURIComponent(jobId)}/knowledge-graph`
  );
}

export async function getConcepts(jobId: string) {
  return request<import("@/types/backend").ConceptsResponse>(
    `/lectures/${encodeURIComponent(jobId)}/concepts`
  );
}

export async function getLectureGaps(jobId: string) {
  return request<import("@/types/backend").LearningGapsResponse>(
    `/lectures/${encodeURIComponent(jobId)}/learning-gaps`
  );
}

export async function explainConcept(jobId: string, concept: string) {
  return request<import("@/types/backend").ConceptExplanation>(
    `/lectures/${encodeURIComponent(jobId)}/concepts/${encodeURIComponent(concept)}/explain`
  );
}

export async function getStudentLectureGaps(jobId: string, studentId: string) {
  return request<import("@/types/backend").StudentGapsResponse>(
    `/lectures/${encodeURIComponent(jobId)}/students/${encodeURIComponent(studentId)}/learning-gaps`
  );
}

export async function getLearningAgent(studentId: string) {
  return request<import("@/types/backend").LearningAgentView>(
    `/students/${encodeURIComponent(studentId)}/learning-agent`
  );
}

export async function getNextAction(studentId: string) {
  return request<import("@/types/backend").NextActionResponse>(
    `/students/${encodeURIComponent(studentId)}/next-action`
  );
}

export async function getLearningInsights(studentId: string) {
  return request<import("@/types/backend").LearningInsightsResponse>(
    `/students/${encodeURIComponent(studentId)}/learning-insights`
  );
}

export async function saveProfile(payload: import("@/types/backend").ProfileUpdatePayload) {
  return request<{ status: string; profile: import("@/types/backend").StudentProfile }>(
    `/students/${encodeURIComponent(payload.student_id)}/profile`,
    { method: "POST", body: JSON.stringify(payload) }
  );
}

export async function uploadVideo(file: File) {
  if (!isDemoModeEnabled()) {
    apiBaseOrThrow();
  }
  const form = new FormData();
  form.append("file", file);
  return request<{ job_id: string; filename: string; size_bytes: number; content_hash?: string; reused_from?: string | null }>("/upload", {
    method: "POST",
    body: form,
  });
}

export async function startProcessing(payload: {
  job_id: string;
  mode?: string;
  student_id?: string;
  accessibility_mode?: string;
}) {
  if (!isDemoModeEnabled()) {
    apiBaseOrThrow();
  }
  return request<{ job_id: string; status: string }>("/process", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function videoUrl(job: Record<string, unknown>): string | null {
  const result = (job?.result as Record<string, unknown> | undefined) ?? {};
  const videoPath =
    (result.video_path as string | undefined) ??
    (job?.video_path as string | undefined);
  if (!videoPath) return null;
  const base = apiBase();
  const filename = fileBaseName(videoPath);
  return base ? `${base}/files/videos/${filename}` : `/files/videos/${filename}`;
}

export function narrationUrl(result: { narration_audio_path?: string } | undefined): string | null {
  if (!result?.narration_audio_path) return null;
  const base = apiBase();
  const filename = fileBaseName(result.narration_audio_path);
  return base ? `${base}/files/outputs/${filename}` : `/files/outputs/${filename}`;
}

export function eventAudioUrl(
  result: { accessibility_events?: Array<{ start: number; narration_audio_path?: string }> },
  start: number | null | undefined
): string | null {
  if (!result || start == null) return null;
  const ev = (result.accessibility_events ?? []).find(
    (e) => Math.abs(Number(e.start) - Number(start)) < 0.01
  );
  if (!ev?.narration_audio_path) return null;
  const base = apiBase();
  const filename = fileBaseName(ev.narration_audio_path);
  return base ? `${base}/files/outputs/${filename}` : `/files/outputs/${filename}`;
}

/**
 * Resolve a backend file URL to an absolute or relative browser-fetchable URL.
 */
export function resolveFileUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;
  const base = apiBase();
  const path = url.startsWith("/") ? url : `/${url}`;
  return base ? `${base}${path}` : path;
}

export async function checkBackend(): Promise<boolean> {
  try {
    await getHealth();
    return true;
  } catch {
    return false;
  }
}

export interface AssistantChatPayload {
  message: string;
  context?: {
    page?: string;
    lecture_id?: string;
    job_id?: string;
    timestamp?: number;
    current_segment?: string;
    current_concept?: string;
    accessibility_mode?: string;
  };
  history?: Array<{ role: string; content: string }>;
}

export interface AssistantChatResponse {
  reply: string;
  action?: string | null;
  action_payload?: Record<string, unknown>;
  evidence?: Array<{ time?: string; type?: string; snippet?: string }>;
}

export async function assistantChat(payload: AssistantChatPayload): Promise<AssistantChatResponse> {
  return request<AssistantChatResponse>("/api/v1/assistant/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function* assistantStream(payload: AssistantChatPayload): AsyncGenerator<{ token: string; done: boolean; action?: string; action_payload?: Record<string, unknown>; evidence?: AssistantChatResponse["evidence"] }, void, unknown> {
  const { state, url } = resolveBackendState();

  if (state === "CONFIGURED_OK" && url) {
    try {
      const res = await fetch(`${url}/api/v1/assistant/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok && res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("data:")) {
              const jsonStr = trimmed.slice(5).trim();
              if (!jsonStr) continue;
              try {
                const parsed = JSON.parse(jsonStr);
                yield parsed;
              } catch {
                // ignore
              }
            }
          }
        }
        return;
      }
      if (res.status >= 400 && !isDemoModeEnabled()) {
        const errText = await res.text().catch(() => "stream error");
        throw new ApiError(res.status, errText || "Streaming request failed.");
      }
    } catch (err) {
      if (err instanceof ApiError) throw err;
      if (!isDemoModeEnabled()) {
        throw readableFetchError("/api/v1/assistant/stream", err);
      }
    }
  }

  if (state === "UNCONFIGURED" && !isDemoModeEnabled()) {
    throw new ApiError(500, "EduAccess AI processing service is not configured.");
  }

  // Simulated SSE stream from demo assistant — ONLY when demo-mode explicitly enabled
  if (!isDemoModeEnabled()) {
    throw new ApiError(503, "Backend unavailable. Please try again later.");
  }
  const demoResp = demoStore.chatDemoAssistant(payload);
  const words = demoResp.reply.split(" ");
  for (let i = 0; i < words.length; i++) {
    await new Promise((r) => setTimeout(r, 30));
    yield {
      token: words[i] + (i < words.length - 1 ? " " : ""),
      done: i === words.length - 1,
      action: i === words.length - 1 ? (demoResp.action ?? undefined) : undefined,
      action_payload: i === words.length - 1 ? (demoResp.action_payload ?? undefined) : undefined,
    };
  }
}
