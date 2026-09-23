# EduAccess AI — The Accessibility Compiler for Education

**EduAccess AI** turns any educational video lecture into an accessible, audited, and personalized learning experience for blind, low-vision, deaf, hard-of-hearing, and cognitive-support learners:

- **Multimodal Audio Description Engine** — Classifies on-screen content into 9 distinct visual types (`code editor`, `slide`, `diagram`, `flowchart`, `chart`, `table`, `formula`, `ui`, `scene`) with semantic code understanding (*"Python for-loop using range(5)"*) without speech repetition or character spelling.
- **Accessibility Difference Engine** — Real-time cross-modal analyzer comparing Teacher Speech vs Screen Visuals to identify 6 disparity categories (`VISUAL_NOT_SPOKEN`, `SPOKEN_NOT_VISUAL`, `VISUAL_PARTIALLY_SPOKEN`, `VISUAL_CONTRADICTS_SPEECH`, `VISUAL_TOO_UNCLEAR`, `VISUAL_IMPORTANT_NOT_DESCRIBED`).
- **Accessibility Debt Metric** — Explainable 0–100 deficit score with an itemized backlog and severity rankings (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- **Modal Accessibility Timeline** — Second-by-second matrix tracking availability across Speech, Visuals, OCR, Audio Description, and Assessment.
- **Accessibility Simulator** — Live persona emulation allowing educators/judges to experience the lecture as a blind, low-vision, deaf, cognitive-support, or standard learner.
- **"Make Video Accessible" One-Click Bundle** — Complete automated accessibility package compilation.
- **Multimodal Lecture Health Score** — 7-dimension evidence-based audit (Speech Coverage, Visual Coverage, Speech-Visual Alignment, OCR Accessibility, Assessment Coverage, Learning Gap Health, Accessibility Coverage).
- **Temporal & Grounded "Ask the Video"** — Interval queries (*"between 00:10 and 00:20"*), exact timestamp anchoring (*"at 00:08"*), and unspoken visual reasoning (*"what was shown but not explained?"*) with evidence trust badges (`VERIFIED`, `UNCERTAIN`, `UNAVAILABLE`).
- **Real-Time Accessibility Copilot** — Synchronized playback awareness bar delivering live contextual briefings and gap alerts at any second $t$.
- **Semantic Knowledge Graph** — Concept graph grounded in real lecture timestamps with `demonstrated_by`, `prerequisite_of`, `related_to`, `shown_at`, `explained_at`, and `assessed_by` relationships.
- **Personal Learning Agent** — Formulates grounded Next Best Actions (*Why, What, Where, Next Action*) based on student quiz performance and accessibility profile.
- **Zero-Fabrication Guarantee** — Every claim is 100% traceable to real pipeline artifacts; uncertainty is reported honestly rather than hallucinated.

---

## 1. Install (one-time)

| Tool | Why |
|---|---|
| **Python 3.10+** | runs everything |
| **FFmpeg** | extracts audio from video |
| **Tesseract OCR** | reads on-screen text/code for the free offline vision fallback |
| **espeak-ng (optional)** | Linux needs it; Windows/macOS use built-in voices via `pyttsx3` |

**Windows:** install FFmpeg + Tesseract and add their folders to `PATH`. **Tesseract is also
auto-discovered** from common install locations if it isn't on `PATH`.

Verify:
```bash
python --version
ffmpeg -version
tesseract --version
```

## 2. Setup

```bash
cd EduAccess-AI
python -m venv .venv
.venv\Scripts\activate        # Windows      (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Optional higher-quality AI features (still fully functional without):
```bash
cp .env.example .env         # Windows: copy .env.example .env
```
Fill in `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` if you have them. Everything works without.

## 3. Run the app (two terminals)

```bash
uvicorn backend.main:app --reload      # Terminal 1 — Backend: http://127.0.0.1:8000/docs
cd frontend/next-app && npm run dev    # Terminal 2 — Frontend: http://localhost:3000
```

Check `/system/status` on the backend for a live health report of every dependency (FFmpeg, Tesseract, Whisper model).

## 4. Product Experience & User Journey

The modern Next.js interface organizes the full lecture intelligence pipeline into 3 consolidated hubs:

1. **Compiler & Library (`/upload`)** — Ingest any video lecture (MP4/MOV/AVI/MKV/WEBM/M4V), track real-time stage progress ledgers, and browse the library of compiled lectures.
2. **Accessibility Studio & Workspace (`/lectures/[jobId]`)** — Full interactive studio combining:
   - **Video Player**: Native HTML5 player with speed controls (0.75x–2.0x), synchronized transcript segment scrubbing, and non-destructive dual audio narration.
   - **Overview Tab**: Real-time coverage metrics and interactive transcript segments.
   - **Visual Intelligence Tab**: Keyframe OCR bounding boxes, slide analysis, and visual scene events.
   - **Audio Description Tab**: Layered dual-audio narration synchronized to visual timestamps (original lecture audio remains audible by default).
   - **What Am I Missing? Tab**: Cross-Modal Difference Engine comparing Speech vs. Screen to isolate unspoken visual content (`VISUAL_NOT_SPOKEN`) with grounded remediations.
   - **Timeline Matrix Tab**: Multi-track timeline synchronizing speech segments, OCR keyframes, and accessibility checkpoints.
   - **Ask the Video Tab**: Temporal and grounded Q&A with verifiable evidence snippets, trust badges (`VERIFIED`, `UNCERTAIN`, `UNAVAILABLE`), and *"Jump to Moment"* links.
   - **Accessibility Report Tab**: Explainable Health Score based on: `Modality Baseline − Unmitigated Disparities + Verified Remediation Benefit`.
3. **Learning Intelligence Hub (`/learning`)** — Pedagogical mastery suite:
   - **Knowledge Graph**: Concept hierarchy and prerequisite graphs grounded in lecture timestamps.
   - **Learning Gaps**: Disparity-informed gap diagnostics.
   - **Adaptive Quiz & Semantic Grading**: Assessment questions with LLM/semantic evaluation.
   - **Student Progress**: Longitudinal history, topic mastery tracking, and review recommendations.
   - **Personal Learning Agent**: Personalized Next Best Actions (*Why, What, Where, Next Action*).

### Accessibility Scope & Honest Limitations
- **Blind & Low-Vision**: Layered Audio Descriptions, OCR extraction, and visual companion briefings.
- **Deaf & Hard-of-Hearing**: Verbatim synchronized captions, timestamped transcripts, and visual concept maps. *(Note: Egyptian Sign Language (EgSL) / sign language translation is NOT IMPLEMENTED in this release.)*
- **Cognitive Support**: Chunked transcript explanations, structured timelines, and adaptive quiz pacing.
9. **Audio Description** — per-event read-aloud descriptions (with per-event audio files) and
   the full narration track.
10. **Quiz & Results** — automatically lists the quiz for the active lecture, grades your
    answers, flags weak concepts, adapts difficulty (≥80% → harder, <50% → easier), and stores
    every attempt in the student's history.
11. **Learning Progress** — *Smart Learning Progress*: per-lecture history with
    rollups, strong topics (≥70%) vs. needs-review topics with the actual missed
    questions, **repeatedly-missed detection** (same question wrong in 2+ attempts,
    never based on a single slip), a **suggested next step** resolved back to a real
    evidence timestamp (segment/visual-event) where possible, and the accessibility
    profile of the student. Progress is recomputed live from stored quiz history —
    never fabricated.
12. **Accessibility Report** — the competition-facing transparency centre:
    - **Accessibility score (0–100)** with `HIGH` / `MEDIUM` / `LOW`, broken into
      7 weighted, fully auditable components (each shows its raw evidence value and
      max contribution) and a composite evidence-trust badge.
    - **Lecture Accessibility Report** in plain language, with an honest statement
      that says exactly how much on-screen content could NOT be verified.
    - **Profile-specific presentation** guidance (blind / low-vision / deaf /
      hard-of-hearing / cognitive) — a presentation plan, never a pipeline re-run.
    - **Live pipeline metrics** (transcript words, visual events, verified evidence,
      quiz questions, missing items, grounded answers) computed on every call from
      the stored job.
    - **Jump-to-moment deep-links** — Ask-the-Video and What-am-I-Missing link to
      `/lectures/<job>?t=<s>`; the workspace auto-seeks the video to that moment.
13. **Knowledge Graph** — the evidence-grounded map of the lecture's concepts,
    each connected to real spoken segments, verified on-screen visuals, and real
    quiz questions. Every concept shows its honest status (`VERIFIED` /
    `PARTIALLY_EXPLAINED` / `assessed_but_not_explained` / `visual_only` /
    `spoken_only` / `UNAVAILABLE`), and any concept expands to a **jump-to-evidence**
    moment in the player. Nothing is guessed: concepts come only from quiz labels,
    recorded objectives and educational vocabulary that literally appears.
14. **Learning Gaps** — surfaces lecture-level gaps (`assessed_but_not_explained` /
    `visual_only` / `spoken_only` / `unverified_visual`) derived from the graph's
    honest statuses, plus per-student mastery gaps computed from real quiz attempts
    with **review-at** links that jump to a real evidence moment. Explains a missing
    concept by gathering only real evidence (`covered` / `partial` / `not_covered`)
    and offering the closest covered concepts the lecturer actually explained.
15. **Personal Learning Agent** — a ranked **Next Best Action** (REVIEW_VIDEO /
    LISTEN_TO_AUDIO_DESCRIPTION / READ_TRANSCRIPT / REVIEW_VISUAL / EXPLAIN_CONCEPT /
    RETAKE_QUIZ / PRACTICE_CONCEPT) that is accessibility-aware and anchored to a real
    lecture + concept + evidence moment, plus the agent's insights and recommendations
    and an explain-a-concept view. A student with insufficient history gets an honest
    "not enough learning history yet" instead of a guess. The dashboard also shows a
    **Next Best Action** banner linking into this screen.

### Demo mode
Choose a lecture from the sidebar catalogue ("Demo mode: open a processed lecture") to explore
all screens without uploading or re-running the pipeline. DEMO lectures are labelled in the
catalogue and marked "ACTIVE LECTURE: DEMO SAMPLE" so generated content is never mistaken for
a real upload.

**Load the DEMO lecture** from the guided tour on the Welcome screen, or generate it fresh:

```bash
python backend/scripts/make_demo_lecture.py   # renders real frames + TTS narration -> data/videos/DEMO_python_loops.mp4
```
Then push it through the same pipeline as any upload:
```bash
python -c "from backend import storage,config; from backend.services.pipeline import run_pipeline; \
jid='DEMO_python_loops'; storage.create_job(jid,{'video_path':str(config.VIDEOS_DIR/'DEMO_python_loops.mp4'),'filename':'DEMO_python_loops.mp4'}); \
run_pipeline(jid, str(config.VIDEOS_DIR/'DEMO_python_loops.mp4'), mode='both')"
```

The DEMO video is **not fake AI output**: frames are rendered to disk, narration is real TTS,
and the pipeline (Whisper + OCR + accessibility) runs on genuine pixels and audio — it simply
has readable on-screen content so the Visual Companion can be demonstrated honestly.

## 5. API

Interactive docs at http://127.0.0.1:8000/docs. Key endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /upload` | upload video (extension + magic-byte validation) |
| `POST /process` | queue the pipeline (mode `both`/`hearing`/`visual`) |
| `GET /result/{job_id}` | poll status/progress/stage ledger/result |
| `GET /lectures` | demo-mode catalogue with per-job asset flags |
| `GET /lectures/{job}/timeline` | synchronized speech/visual/quiz timeline (visual entries carry duration/importance/complement/trust/OCR text) |
| `GET /lectures/{job}/missing?mode=` | profile-aware "What am I missing?" items: status (`REDUNDANT`/`PARTIALLY_MISSING`/`MISSING`/`UNAVAILABLE`), importance rank, complement + trust, evidence, dedup; summary carries per-event statuses, counts, coverage and composite trust |
| `GET /lectures/{job}/visual-events` | raw visual events + grounded Visual Companion analysis + `understanding` array |
| `GET /lectures/{job}/visual-understanding` | evidence-grounded visual understanding per event: `visual_type` (slide/code/diagram/chart/table/ui/scene, never guessed) + complement level (`REDUNDANT`/`PARTIALLY_MISSING`/`COMPLEMENTARY`/`VISUALLY_ONLY`/`AUDIO_ONLY`/`UNAVAILABLE`), grounded `visual_claims` (each with its own evidence + confidence), verbatim OCR, accessible descriptions, honest `limitations` (colors/numbers/code/labels never invented) |
| `GET /lectures/{job}/evidence` | per-event evidence records + composite claim trust |
| `GET /lectures/{job}/transcript` | transcript text + timestamped segments |
| `GET /lectures/{job}/accessibility?mode=` | per-mode accessibility representation |
| `POST /ask` | evidence-grounded Q&A: retrieval → deterministic grounded answer → optional LLM polish on retrieved context only. Returns `answer`, `timestamps`, `source_refs`, `evidence[]` (per-record trust), composite `trust`, `trust_reason`, `status`/`status_reason`, `category`, `why[]`, `conflict`, `jump`, and a structured `trust_explanation` block (`lines` + `sources_agree` + `cap`) |
| `GET /lectures/{job}/accessibility-score` | explainable Accessibility Coverage Score: `score` 0–100, `level`, 7 weighted `components` (each with `evidence_value`, `cap`, `contribution`), `explanation[]`, composite `trust`, `basis` |
| `GET /lectures/{job}/report` | Lecture Accessibility Report: speech / visual-understanding / missing-information / evidence / audio-description + honest statement |
| `GET /lectures/{job}/presentation?mode=` | profile-specific presentation plan (blind / low-vision / deaf / hard-of-hearing / cognitive / default) — no pipeline re-run |
| `GET /lectures/{job}/replay?timestamp=` | visual-moment replay metadata: moment + seek point, OCR text, trust, transcript context, why-it-matters, source frames |
| `GET /lectures/{job}/metrics` | real live metrics (transcript words, events, verified evidence, quiz questions, missing items, grounded answers) |
| `GET /lectures/{job}/pipeline-status` | canonical 12-stage pipeline in order with per-stage status / seconds / fallback / counts + READY |
| `GET /lectures/{job}/knowledge-graph` | Lecture Knowledge Graph: concept/segment/event/quiz nodes + edges (speech/shown/assessed/followed_by), each concept with honest status + trust |
| `GET /lectures/{job}/concepts` | per-concept mapping to real spoken snippets + readable visual evidence + status + assessed flag |
| `GET /lectures/{job}/learning-gaps` | lecture-level gaps from honest statuses: `assessed_but_not_explained` / `visual_only` / `spoken_only` / `unverified_visual` |
| `GET /lectures/{job}/concepts/{concept}/explain` | honest explain-missing-concept: real evidence only, verdict `covered`/`partial`/`not_covered` + closest covered concepts |
| `GET /lectures/{job}/students/{sid}/learning-gaps` | per-student mastery gaps from real quiz attempts, resolved to a real evidence timestamp |
| `GET /students/{sid}/learning-agent` | Personal Learning Agent view (mastery, trend, access-aware recommended actions, grounded_on) |
| `GET /students/{sid}/next-action` | ranked Next Best Action (whitelisted types, real lecture+concept+timestamp) or honest insufficient-history |
| `GET /students/{sid}/learning-insights` | agent insights summary |
| `GET /students/{id}/progress` | Smart Learning Progress (strong vs needs-review, repeatedly-missed, next action grounded in evidence) |
| `GET /quizzes` / `GET /quizzes/{id}` | list / fetch sanitized quiz (no answer leakage) |
| `POST /quizzes/submit` | grade + persist attempt + adaptive difficulty |
| `GET /students` / `GET /students/{id}` | student list + enriched progress |
| `POST /students/{id}/profile` | save accessibility profile |
| `GET /system/status` | dependency + model health |

## 6. Tests

```bash
python -m pytest -q        # 182 tests: API, profile, timeline, ask
                           # (incl. 21 evidence-grounded P3 scenarios: Arabic,
                           # conflicts, partial OCR, property no-guess,
                           # hallucinated-citation guard, observability),
                           # evidence/trust, visual companion, complement score,
                           # missing classification & ranking, quiz-flow,
                           # accessibility, end-to-end demo-mode, 25 P4
                           # competition-readiness tests (score explainability,
                           # honest report, presentation, trust explanation,
                           # replay, smart progress, live metrics, pipeline
                           # transparency, crash safety, demo-mode import),
                           # and 27 P5 visual-understanding tests
                           # (classification, adversarial no-fabrication: color/
                           # count/code never guessed on empty OCR, complement,
                           # accessibility layers, schema, API routes)
                           # and 29 P7 intelligent-engine tests (knowledge graph
                           # grounding & determinism, honest no-history agent,
                           # gap kinds, API contracts) => 223 tests total
```

Tests use isolated synthetic jobs and clean up every artifact they create, so running them
never pollutes real lecture data.

## 7. Project structure

```
backend/
├── main.py            # FastAPI app (v2), static mounts, CORS
├── config.py          # settings, path discovery (tesseract), limits
├── storage.py         # atomic JSON job store
├── observability.py   # per-stage timing/status ledger
├── routes/            # upload, process(+lectures/ask/status), quiz, student,
│                      # analytics (score/report/presentation/replay/metrics/pipeline-status),
│                      # learning (knowledge-graph/concepts/gaps/explain/agent/next-action)
├── scripts/           # make_demo_lecture.py (regenerable DEMO lecture)
├── services/          # video, speech, vision, llm, tts, pipeline,
│                      # accessibility, visual_companion, evidence,
│                      # visual_understanding, lecture_data,
│                      # accessibility_score, progress, quiz,
│                      # quiz_generator, ask, knowledge_graph,
│                      # concept_mapping, learning_gaps, learning_agent
└── models/schemas.py  # request/response models
frontend/app.py        # 12-screen Streamlit UI (+ Visual Companion, evidence,
                       # trust player, Accessibility Report + progress)
frontend/next-app/     # Next.js app: workspace, dashboard (Next Best Action banner),
                       # + knowledge-graph / learning-gaps / agent pages (INTELLIGENCE nav)
data/videos|audio|frames|outputs|quizzes|students   # generated at runtime
tests/                 # 319 automated tests (313 passed, 6 skipped) + shared fixtures
```

Competition-readiness detail, acceptance checklist (A–I) and the two live case
studies (DEMO `DEMO_python_loops`, real `2924ba8f8909`) are documented in
[`docs/COMPETITION_READINESS_REPORT.md`](docs/COMPETITION_READINESS_REPORT.md).

## 8. Pipeline

```
video.mp4
   ├─ ffmpeg ──► audio.wav ──► Whisper ──► transcript + segments ──► .srt
   └─ OpenCV scene sampling ──► Tesseract OCR / vision ──► visual events
        ──► Visual Companion analysis (grounding, complement, trust, importance)
        ──► visual_understanding (evidence-grounded type + claims + accessibility per event)
        ──► missing_information_analysis (REDUNDANT / PARTIALLY_MISSING / MISSING / UNAVAILABLE + importance rank)
        ──► profile-aware accessibility events (what's NOT covered by speech)
        ──► narration TTS (per event + full track)
        ──► adaptive quiz generation
```

Every visual event gets a grounded analysis record: lecture id, timestamps,
previous/next event, overlapping transcript + segment ids, OCR text (only what
was actually read), a categorical **visual complement score** with a written
reason, importance, source (`ocr`/`vision`) and a **trust level**
(`VERIFIED`/`UNCERTAIN`/`UNAVAILABLE`). Unreadable frames are marked
UNAVAILABLE and are gated out of "What am I missing?" — never fabricated.

Built on top of that, every visual event also gets an **evidence-grounded
visual understanding record**: a `visual_type` (`slide`/`code`/`diagram`/
`chart`/`table`/`ui`/`scene` — guessed only from actual OCR + detection
confidence markers, never invented), verbatim OCR, grounded `visual_claims`
(two to four claims, each with its own evidence + confidence), a
`complement_level` relating the visual to what speech covered, short/standard
accessible descriptions, and an honest `limitations` list (colors, counts,
unreadable code, and fake node numbers are explicitly refused when the OCR
cannot support them). The `visual_understanding` stage runs after Visual
Companion analysis and its `{stem}_visual_understanding.json` cache is what
`/visual-understanding`, `/visual-events`, `/timeline`, `/missing` and Ask-the-Video
all read.

Heavy artifacts (audio, transcript, frames, visual events) are cached and reused across job
runs; per-stage status — `completed` / `cached` / `partial` / `failed` — is recorded in the
job's ledger and shown in the dashboard. A degraded stage is reported as partial, never as a
silently faked success.

## 9. Troubleshooting

- **"ffmpeg failed"** → `ffmpeg -version` must work on your PATH.
- **Whisper slow** → set `WHISPER_MODEL_SIZE=tiny` in `.env`.
- **No narration audio** → check `pyttsx3` voice (Windows/macOS built-in) or install `espeak-ng`
  on Linux; or set `TTS_PROVIDER=openai` + `OPENAI_API_KEY`.
- **Vision says "no readable on-screen text"** → that's the honest offline OCR fallback for a
  webcam-style video; it only reads text, not photos/diagrams. Add `OPENAI_API_KEY` /
  `ANTHROPIC_API_KEY` for full scene understanding.
- **"What am I missing?" is empty for a lecture** → for deaf/cognitive profiles the panel
  intentionally surfaces only educational visuals; for any lecture with no readable content the
  trust layer (UNAVAILABLE) gates everything out — check the Visual Timeline, where the gated
  events are still shown with their trust badges.
- **DEMO lecture missing** → run `python backend/scripts/make_demo_lecture.py` (needs FFmpeg +
  a working pyttsx3 voice), then process it (see Demo mode above).
- **Streamlit can't reach backend** → keep Terminal 1 (`uvicorn`) running; the app uses
  `http://127.0.0.1:8000`.