import demoPythonLoopsRaw from "./demoData/DEMO_python_loops.json";
import demoQuizPython from "./demoData/DEMO_python_loops_quiz.json";
import demoProfiles from "./demoData/profiles.json";
import demo001History from "./demoData/001_history.json";
import demoDefaultHistory from "./demoData/default_history.json";
import type {
  AskResponse,
  LectureRecord,
  LearningProgress,
  MetricsResponse,
  Quiz,
  QuizSubmissionResponse,
  StudentRecord,
  StudentDetail,
  KnowledgeGraphResponse,
  ConceptsResponse,
  LearningGapsResponse,
  StudentGapsResponse,
  ConceptExplanation,
  LearningAgentView,
  NextActionResponse,
  LearningInsightsResponse,
  StudentProfile,
  TimelineResponse,
  MissingResponse,
  VisualEventsResponse,
  VisualUnderstandingResponse,
  AudioDescriptionResponse,
  AccessibilityResult,
  AccessibilityScore,
  AccessibilityReport,
  ReplayResponse,
} from "@/types/backend";
import { fileBaseName } from "@/lib/format";

export interface DemoJob {
  job_id: string;
  filename: string;
  status: string;
  progress: number;
  current_stage: string;
  error: string | null;
  video_path: string;
  logs: Array<{ ts: string; level: string; message: string }>;
  created_at?: string;
  updated_at?: string;
  result?: Record<string, unknown>;
}

// In-memory demo store
const DEMO_JOBS: Record<string, DemoJob> = {
  DEMO_python_loops: demoPythonLoopsRaw as unknown as DemoJob,
};

const QUIZZES: Record<string, Quiz> = {
  DEMO_python_loops_quiz: {
    quiz_id: "DEMO_python_loops_quiz",
    questions: demoQuizPython as any,
  },
};

const STUDENT_HISTORIES: Record<string, any> = {
  "001": demo001History,
  default: demoDefaultHistory,
};

let studentProfiles: StudentProfile[] = [...(demoProfiles as any)];

export function getDemoLectures(): LectureRecord[] {
  return Object.values(DEMO_JOBS).map((job) => {
    const res = job.result || {};
    const meta = (res.video_metadata as Record<string, unknown>) || {};
    const stageStatus = (res.stage_status as Record<string, string>) || {
      audio: "ok",
      transcription: "ok",
      vision: "ok",
      visual_events: "ok",
      narration: "ok",
      quiz: "ok",
    };

    return {
      job_id: job.job_id,
      filename: job.filename,
      status: job.status,
      progress: job.progress,
      current_stage: job.current_stage,
      error: job.error,
      created_at: job.created_at || "2026-08-30T12:00:00Z",
      updated_at: job.updated_at || "2026-08-30T12:00:00Z",
      duration: (meta.duration as number) || 28,
      has_result: Boolean(job.result),
      student_id: "001",
      assets: {
        video: true,
        transcript: true,
        srt: true,
        captions: true,
        visual_events: true,
        visual_analysis: true,
        narration_audio: true,
        quiz: true,
        knowledge_graph: true,
      },
      stage_status: stageStatus,
      cached: true,
    };
  });
}

export function getDemoJob(jobId: string): DemoJob | null {
  const norm = jobId.replace(/\.mp4$/i, "");
  const found = DEMO_JOBS[norm] || DEMO_JOBS[jobId];
  if (found) return found;
  return DEMO_JOBS["DEMO_python_loops"];
}

export function getDemoTimeline(jobId: string): TimelineResponse {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  return {
    job_id: job?.job_id || jobId,
    timeline: (res.timeline as any) || [],
  } as unknown as TimelineResponse;
}

export function getDemoMissing(jobId: string, mode = "blind"): MissingResponse {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  const missing = (res.missing_analysis as any) || (res.accessibility as any)?.missing_visuals || [];
  return {
    job_id: job?.job_id || jobId,
    profile_mode: mode,
    summary: {
      text: "Visual details from this lecture that are not fully explained by speech.",
      statuses: [],
      status_counts: {},
      actionable_count: Array.isArray(missing) ? missing.length : 0,
      overall_coverage_ratio: 0.94,
      overall_evidence_trust: { trust: "VERIFIED", reason: "Grounded in visual events." },
    },
    items: Array.isArray(missing) ? missing : [],
  } as unknown as MissingResponse;
}

export function getDemoVisualEvents(jobId: string): VisualEventsResponse {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  const events = (res.visual_events as any) || [];
  return {
    job_id: job?.job_id || jobId,
    visual_events: events,
  } as unknown as VisualEventsResponse;
}

export function getDemoVisualUnderstanding(jobId: string): VisualUnderstandingResponse {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  const events = (res.visual_understanding as any) || (res.visual_analysis as any) || [];
  return {
    job_id: job?.job_id || jobId,
    events: events,
  } as unknown as VisualUnderstandingResponse;
}

export function getDemoAudioDescription(jobId: string): AudioDescriptionResponse {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  const events = (res.accessibility_events as any) || [];
  const fullNarration = (res.narration_audio_path as string) || "/files/outputs/DEMO_python_loops_narration.wav";
  return {
    job_id: job?.job_id || jobId,
    events: events.map((e: any, idx: number) => ({
      ...e,
      narration_audio_url: e.narration_audio_path
        ? `/files/outputs/${fileBaseName(e.narration_audio_path)}`
        : `/files/outputs/DEMO_narration_${idx}.wav`,
    })),
  } as unknown as AudioDescriptionResponse;
}

export function getDemoTranscript(jobId: string) {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  return {
    job_id: job?.job_id || jobId,
    transcript_text: (res.transcript_text as string) || "Welcome to Python Loops introduction. Today we explore for loops.",
    segments: (res.segments as any) || [],
  };
}

export function getDemoAccessibility(jobId: string, mode = "blind"): AccessibilityResult {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  const acc = (res.accessibility as any) || {};
  return {
    job_id: job?.job_id || jobId,
    accessibility_profile: { mode },
    visual_events: (res.visual_events as any) || [],
    accessibility_events: (res.accessibility_events as any) || [],
    quality_score: acc.score || 94,
  } as unknown as AccessibilityResult;
}

export function getDemoAccessibilityScore(jobId: string): AccessibilityScore {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  return (res.accessibility_score as any) || {
    job_id: job?.job_id || jobId,
    score: 94,
    level: "HIGH",
    trust: { trust: "VERIFIED", reason: "Grounded benchmark.", records: 14 },
    basis: "multi-modal",
    components: {},
    explanation: ["Synchronized multimodal alignment verified."],
  };
}

export function getDemoAccessibilityReport(jobId: string): AccessibilityReport {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  return (res.accessibility_report as any) || {
    job_id: job?.job_id || jobId,
    accessibility_score: 94,
    level: "HIGH",
    trust: { trust: "VERIFIED", reason: "Grounded benchmark.", records: 14 },
    components: {},
    strengths: ["Clear spoken articulation of loop principles."],
    gaps_detected: ["Loop syntax at 00:08 required descriptive enhancement."],
    remediations_applied: ["Synchronized audio description cue injected at 00:08."],
    verifications: ["Zero disparity gaps remaining after dual-audio synthesis."],
  };
}

export function getDemoMetrics(jobId: string): MetricsResponse {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  const meta = (res.video_metadata as Record<string, unknown>) || {};
  return {
    job_id: job?.job_id || jobId,
    video_duration_seconds: (meta.duration as number) || 28,
    transcript_segments: ((res.segments as any[]) || []).length || 8,
    transcript_words: 140,
    visual_events: ((res.visual_events as any[]) || []).length || 6,
    visual_analysis_records: 6,
    described_accessibility_events: ((res.accessibility_events as any[]) || []).length || 4,
    accessibility_events: ((res.accessibility_events as any[]) || []).length || 4,
    missing_information_items: 2,
    quiz_questions: 3,
    evidence_grounded_ask_answers: 4,
    supported_ask_answers: 4,
    verified_evidence_records: 12,
    computed_at: new Date().toISOString(),
  };
}

export function getDemoPresentation(jobId: string): Record<string, unknown> {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  return {
    job_id: job?.job_id || jobId,
    slides: (res.visual_events as any[]) || [],
    transcript: (res.segments as any[]) || [],
    cues: (res.accessibility_events as any[]) || [],
  };
}

export function getDemoReplay(jobId: string, timestamp: number): ReplayResponse {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  const segments = (res.segments as any[]) || [];
  const events = (res.visual_events as any[]) || [];
  const currSeg = segments.find((s) => timestamp >= s.start && timestamp <= s.end);
  const currEv = events.find((e) => timestamp >= e.start && timestamp <= e.end);

  return {
    job_id: job?.job_id || jobId,
    active_segment: currSeg || null,
    active_visual_event: currEv || null,
    context_summary: currSeg?.text || "Exploring lecture content",
  } as unknown as ReplayResponse;
}

export function getDemoKnowledgeGraph(jobId: string): KnowledgeGraphResponse {
  const job = getDemoJob(jobId);
  const res = job?.result || {};
  if (res.knowledge_graph) {
    return res.knowledge_graph as any;
  }
  return {
    job_id: job?.job_id || jobId,
    concepts: [
      { concept: "Loops & Iteration", status: "EXPLAINED", has_speech: true, has_visual: true, verified_visual: true },
      { concept: "For Loop", status: "PARTIALLY_EXPLAINED", has_speech: true, has_visual: true, verified_visual: true },
      { concept: "range() Function", status: "VISUALLY_SHOWN", has_speech: false, has_visual: true, verified_visual: false },
      { concept: "Loop Variable", status: "ASSESSED", has_speech: true, has_visual: true, verified_visual: true },
    ],
    relationships: [
      { source: "Loops & Iteration", target: "For Loop", type: "prerequisite" },
      { source: "For Loop", target: "range() Function", type: "uses" },
      { source: "For Loop", target: "Loop Variable", type: "contains" },
    ],
  } as unknown as KnowledgeGraphResponse;
}

export function getDemoConcepts(jobId: string): ConceptsResponse {
  const graph = getDemoKnowledgeGraph(jobId);
  return {
    job_id: jobId,
    concepts: graph.concepts || [],
  } as unknown as ConceptsResponse;
}

export function getDemoConceptExplanation(jobId: string, concept: string): ConceptExplanation {
  return {
    concept: concept,
    explanation: `Concept '${concept}' is grounded in the lecture evidence with synchronized video and audio references.`,
    evidence_timestamps: [0, 20],
    suggested_review: "Review segment at 0:10 with synchronized audio descriptions.",
  } as unknown as ConceptExplanation;
}

export function getDemoLectureGaps(jobId: string): LearningGapsResponse {
  return {
    job_id: jobId,
    gaps: [
      {
        concept_id: "range_func",
        concept: "range() Function",
        headline: "Visual code on screen without spoken explanation",
        status: "NOT_COVERED",
        covered: false,
        partial: false,
        not_covered: true,
        reasons: ["Shown visually on screen without explicit spoken syntax breakdown."],
        spoken: [],
        shown: [],
        assessed: true,
        closest_covered: [],
      },
    ],
  } as unknown as LearningGapsResponse;
}

export function getDemoStudentGaps(jobId: string, studentId: string): StudentGapsResponse {
  return {
    student_id: studentId,
    identified_gaps: [
      {
        concept: "loops_indexing",
        description: "Zero-based indexing in Python loops requires additional reinforcement.",
        mastery_level: 0.45,
        target_timestamp: 15,
      },
    ],
  } as unknown as StudentGapsResponse;
}

export function getDemoQuizzes(): { quizzes: string[] } {
  return { quizzes: Object.keys(QUIZZES) };
}

export function getDemoQuiz(quizId: string): Quiz {
  return QUIZZES[quizId] || QUIZZES["DEMO_python_loops_quiz"];
}

export function submitDemoQuiz(payload: {
  quiz_id: string;
  answers: Record<string, string>;
  lesson_title?: string;
  student_id?: string;
}): QuizSubmissionResponse {
  const quiz = getDemoQuiz(payload.quiz_id);
  const questions = quiz.questions || [];
  let correctCount = 0;
  const gradedQuestions = questions.map((q: any, idx: number) => {
    const userAns = payload.answers[String(idx)] ?? payload.answers[q.question] ?? "";
    const isCorrect = userAns.trim().toLowerCase() === String(q.answer).trim().toLowerCase();
    if (isCorrect) correctCount++;
    return {
      question: q.question,
      user_answer: userAns,
      correct_answer: q.answer,
      correct: isCorrect,
      concept: q.concept,
    };
  });

  const total = questions.length || 1;
  const scorePercent = Math.round((correctCount / total) * 100);

  return {
    student_id: payload.student_id || "001",
    score_percent: scorePercent,
    correct_count: correctCount,
    total: total,
    passed: scorePercent >= 60,
    feedback: scorePercent >= 80 ? "Excellent mastery of concepts!" : "Good effort! Review the flagged concepts.",
    graded_questions: gradedQuestions,
    next_step: scorePercent >= 60 ? "Advance to nested loops & collections" : "Replay video segment at 00:10",
  } as unknown as QuizSubmissionResponse;
}

export function getDemoStudents(): { students: StudentRecord[] } {
  return {
    students: studentProfiles.map((p) => ({
      student_id: p.id,
      name: p.name || `Student ${p.id}`,
      accessibility_mode: p.accessibility_mode || "blind",
      level: "intermediate",
    })),
  } as unknown as { students: StudentRecord[] };
}

export function getDemoStudentDetail(studentId: string): StudentDetail {
  const profile = studentProfiles.find((p) => p.id === studentId) || studentProfiles[0];
  const history = STUDENT_HISTORIES[studentId] || STUDENT_HISTORIES["default"] || {};
  return {
    student_id: profile.id,
    profile,
    history,
  } as unknown as StudentDetail;
}

export function getDemoStudentProgress(studentId: string): LearningProgress {
  const history = STUDENT_HISTORIES[studentId] || STUDENT_HISTORIES["default"] || {};
  return {
    student_id: studentId,
    overall_mastery: 84,
    total_quizzes_taken: history.attempts?.length || 5,
    average_score: 88.5,
    weak_topics: history.weak_topics || [{ topic: "loops_indexing", score: 45 }],
    recent_attempts: history.attempts || [],
    learning_streak_days: 4,
  } as unknown as LearningProgress;
}

export function getDemoLearningAgent(studentId: string): LearningAgentView {
  const profile = studentProfiles.find((p) => p.id === studentId) || studentProfiles[0];
  return {
    student_id: studentId,
    profile,
    has_history: true,
    insights: [
      { kind: "STRENGTH", text: "Student excels at high-level algorithm understanding." },
      { kind: "RETENTION", text: "Demonstrates 95% retention with synchronized audio descriptions." },
      { kind: "IMPROVEMENT", text: "Requires minor practice with loop index boundary conditions." },
    ],
    recommended_actions: [
      {
        action_type: "REVIEW_VIDEO",
        label: "Review Loop Range Boundaries",
        reasoning: "Re-listen to the 00:12 explanation of range(start, stop) with audio description.",
        lecture_id: "DEMO_python_loops",
        timestamp: 12,
        grounded_on: true,
        priority: 1,
      },
      {
        action_type: "RETAKE_QUIZ",
        label: "Python Loops Confidence Check",
        reasoning: "Take a 3-question adaptive quiz to cement mastery.",
        lecture_id: "DEMO_python_loops",
        grounded_on: true,
        priority: 2,
      },
    ],
    generated_at: new Date().toISOString(),
  };
}

export function getDemoNextAction(studentId: string): NextActionResponse {
  const agent = getDemoLearningAgent(studentId);
  const first = agent.recommended_actions[0];
  return {
    student_id: studentId,
    action_type: first.action_type,
    label: first.label,
    reasoning: first.reasoning,
    lecture_id: first.lecture_id,
    timestamp: first.timestamp,
    grounded_on: true,
    insufficient_history: false,
  };
}

export function getDemoLearningInsights(studentId: string): LearningInsightsResponse {
  const agent = getDemoLearningAgent(studentId);
  return {
    student_id: studentId,
    has_history: true,
    insights: agent.insights,
    recommended_actions: agent.recommended_actions,
    generated_at: agent.generated_at,
  };
}

export function saveDemoProfile(payload: any) {
  const idx = studentProfiles.findIndex((p) => p.id === payload.student_id);
  if (idx >= 0) {
    studentProfiles[idx] = { ...studentProfiles[idx], ...payload };
  } else {
    studentProfiles.push({ id: payload.student_id, ...payload });
  }
  return {
    status: "ok",
    profile: studentProfiles.find((p) => p.id === payload.student_id) || studentProfiles[0],
  };
}

export function askDemoQuestion(jobId: string, question: string): AskResponse {
  const qLower = question.toLowerCase();
  const isArabic = /[\u0600-\u06FF]/.test(question);

  if (isArabic) {
    if (qLower.includes("كود") || qLower.includes("شاشة") || qLower.includes("برمجة")) {
      return {
        answer: "الكود الذي ظهر على الشاشة هو حلقة تكرارية For Loop في بايثون: `for i in range(5): print(i)`، حيث تقوم بتكرار طباعة الأرقام من 0 إلى 4.",
        timestamps: [5, 12],
        evidence: [
          { timestamp: 5, source_type: "visual_event", snippet: "ظهر على الشاشة كود تعريف حلقة التكرار for loop" },
          { timestamp: 12, source_type: "transcript", snippet: "نستخدم حلقة for للمرور عبر نطاق الأرقام وطباعتها" },
        ],
        trust: "VERIFIED",
        trust_reason: "Verified by OCR and visual detection.",
        evidence_records: 2,
      } as unknown as AskResponse;
    }
    return {
      answer: `بناءً على محتوى المحاضرة، تم شرح المفاهيم الأساسية مع دعم الوصف الصوتي وترجمة الشاشة لضمان وصول المعلومة لجميع الطلاب.`,
      timestamps: [0],
      evidence: [
        { timestamp: 0, source_type: "transcript", snippet: "بداية شرح الدرس مع استعراض الأهداف التعليمية" },
      ],
      trust: "VERIFIED",
      trust_reason: "Verified by transcript evidence.",
      evidence_records: 1,
    } as unknown as AskResponse;
  }

  // English questions
  if (qLower.includes("code") || qLower.includes("screen") || qLower.includes("loop") || qLower.includes("syntax")) {
    return {
      answer: "The code on screen shows a Python for loop: `for i in range(5): print(i)`. It iterates 5 times, printing numbers 0 through 4.",
      timestamps: [5, 12],
      evidence: [
        { timestamp: 5, source_type: "visual_event", snippet: "Code block rendered on screen: for i in range(5): print(i)" },
        { timestamp: 12, source_type: "transcript", snippet: "We use a for loop in Python to repeat execution over a sequence." },
      ],
      trust: "VERIFIED",
      trust_reason: "Verified by OCR and visual detection.",
      evidence_records: 2,
    } as unknown as AskResponse;
  }

  return {
    answer: `According to the lecture, the concepts are thoroughly grounded with synchronized audio descriptions and transcript segments.`,
    timestamps: [0],
    evidence: [
      { timestamp: 0, source_type: "transcript", snippet: "Lesson introduction and core programming concepts." },
    ],
    trust: "VERIFIED",
    trust_reason: "Verified by transcript evidence.",
    evidence_records: 1,
  } as unknown as AskResponse;
}

export function chatDemoAssistant(payload: {
  message: string;
  context?: Record<string, any>;
  history?: Array<{ role: string; content: string }>;
}) {
  const msg = payload.message.toLowerCase();
  const isArabic = /[\u0600-\u06FF]/.test(payload.message);

  if (isArabic) {
    if (msg.includes("فيديو") || msg.includes("شغل") || msg.includes("محاضرة") || msg.includes("كود")) {
      return {
        reply: "أهلاً بك! لقد قمت بتحديد المقطع الذي يحتوي على شرح الكود وحلقة التكرار. يمكنك النقر على الرابط للانتقال مباشرة إلى المقطع في الفيديو.",
        action: "SEEK_VIDEO",
        action_payload: { timestamp: 5, lecture_id: "DEMO_python_loops" },
        evidence: [
          { time: "00:05", type: "visual_event", snippet: "ظهور كود بايثون لحلقة for loop على الشاشة" },
        ],
      };
    }
    if (msg.includes("اختبار") || msg.includes("كويز") || msg.includes("اسئلة")) {
      return {
        reply: "بالتأكيد! يمكنك تجربة الاختبار التفاعلي التكيفي لتقييم فهمك للمفاهيم.",
        action: "OPEN_QUIZ",
        action_payload: { quiz_id: "DEMO_python_loops_quiz" },
        evidence: [],
      };
    }
    return {
      reply: "مرحباً بك في EduAccess AI! أنا مساعدك التعليمي الذكي المدعوم بالذكاء الاصطناعي. يمكنني مساعدتك في استكشاف المحاضرات، شرح الأكواد المرئية بالصوت، حل الاختبارات التكيفية، والإجابة على أي سؤال من داخل الفيديو.",
      action: null,
      evidence: [],
    };
  }

  // English
  if (msg.includes("video") || msg.includes("play") || msg.includes("seek") || msg.includes("code")) {
    return {
      reply: "Here is the exact lecture segment where the Python loop syntax is demonstrated on screen!",
      action: "SEEK_VIDEO",
      action_payload: { timestamp: 5, lecture_id: "DEMO_python_loops" },
      evidence: [
        { time: "00:05", type: "visual_event", snippet: "Python for loop code block rendered on screen" },
      ],
    };
  }
  if (msg.includes("quiz") || msg.includes("test") || msg.includes("practice")) {
    return {
      reply: "I have prepared an adaptive quiz based on this lecture to test your comprehension!",
      action: "OPEN_QUIZ",
      action_payload: { quiz_id: "DEMO_python_loops_quiz" },
      evidence: [],
    };
  }

  return {
    reply: "Welcome to EduAccess AI! I am your multimodal learning assistant. I can navigate lectures, explain on-screen visual demonstrations through audio descriptions, trace concept knowledge graphs, and answer questions grounded strictly in video evidence.",
    action: null,
    evidence: [],
  };
}
