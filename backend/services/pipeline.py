"""Backward-compatible orchestration plus Person 4 accessibility artifacts.

Person 5 additions:
  - Transparent per-stage status reporting (completed / partial / failed /
    cached) with durations and fallback notes (AI failure transparency).
  - Skip-if-processed: heavy artifacts (audio, transcript, frames, visual
    events) are reused across jobs for performance and demo reliability.
  - The narration audio path is persisted per accessibility event so the UI
    can offer "Play description" controls.
  - Empty transcripts / unavailable vision are handled gracefully and marked
    honestly instead of being silently faked.
"""
from __future__ import annotations

import json
from pathlib import Path

from backend import config, storage
from backend.observability import StageTimer, record_stage
from backend.services import video, speech, vision, tts, accessibility


def _find_event_for_time(events: list[dict], timestamp: float) -> dict | None:
    for event in events:
        if event["start"] <= timestamp <= event["end"]:
            return event
    return min(events, key=lambda e: min(abs(e["start"] - timestamp), abs(e["end"] - timestamp)), default=None)


def _load_existing_events(video_stem: str, job_id: str) -> list[dict] | None:
    path = config.OUTPUTS_DIR / f"{video_stem}_visual_events.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("job_id") in (None, job_id) and isinstance(payload.get("events"), list):
            return payload["events"]
    except (OSError, ValueError, TypeError):
        return None
    return None


def _load_json_if_valid(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_json(path: Path, payload: dict) -> str:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def _load_video_cache(video_stem: str):
    """Return cached heavy artifacts for a video stem (across jobs)."""
    transcript_txt = config.OUTPUTS_DIR / f"{video_stem}_transcript.txt"
    srt_path = config.OUTPUTS_DIR / f"{video_stem}.srt"
    segments_path = config.OUTPUTS_DIR / f"{video_stem}_segments.json"
    frames_path = config.OUTPUTS_DIR / f"{video_stem}_frames.json"
    audio_path = config.AUDIO_DIR / f"{video_stem}.wav"

    cached = {}
    if audio_path.exists():
        cached["audio_path"] = str(audio_path)
    if segments_path.exists():
        payload = _load_json_if_valid(segments_path)
        if payload and isinstance(payload.get("segments"), list):
            cached["segments"] = payload["segments"]
            cached["transcript_text"] = payload.get("text", "")
    if transcript_txt.exists():
        cached["transcript_path"] = str(transcript_txt)
    if srt_path.exists():
        cached["srt_path"] = str(srt_path)
    if frames_path.exists():
        payload = _load_json_if_valid(frames_path)
        if payload and isinstance(payload.get("frames"), list):
            cached["frames"] = payload["frames"]
            cached["video_metadata"] = payload.get("metadata", {})
    return cached


def _profile_cache_key(job: dict, student_id: str, accessibility_mode: str | None) -> bool:
    """True if the stored result matches the requested profile (cache hit)."""
    result = job.get("result") or {}
    stored = result.get("accessibility_profile") or {}
    req_mode = accessibility.normalize_mode(
        accessibility_mode or (accessibility.load_student_profile(student_id).get("accessibility_mode"))
    )
    return str(stored.get("id")) == str(student_id) and str(stored.get("accessibility_mode")) == str(req_mode)


def run_pipeline(job_id: str, video_path: str, mode: str = "both", student_id: str = "default", accessibility_mode: str | None = None) -> dict:
    """Run existing stages and add profile-aware, grounded Person 4 output."""
    video_path = str(video_path)
    stem = Path(video_path).stem
    profile = accessibility.load_student_profile(student_id)
    if accessibility_mode:
        profile["accessibility_mode"] = accessibility.normalize_mode(accessibility_mode)
    mode_name = accessibility.normalize_mode(profile.get("accessibility_mode"))
    stage_status: dict[str, dict] = {}

    # 1. High-Performance Cache Check (done job + matching profile + assets, or reused content hash)
    if storage.job_exists(job_id):
        try:
            job = storage.get_job(job_id)
            reused_id = job.get("reused_from_job")
            if reused_id and storage.job_exists(reused_id):
                reused_job = storage.get_job(reused_id)
                if reused_job.get("status") == "done" and reused_job.get("result"):
                    reused_res = dict(reused_job["result"])
                    reused_res["cached"] = True
                    reused_res["reused_from_job"] = reused_id
                    reused_res["video_path"] = str(video_path)
                    storage.update_job(job_id, status="done", progress=100, current_stage="completed", error=None, result=reused_res)
                    record_stage(job_id, "pipeline", ok=True, seconds=0.0, note=f"Reused outputs from content hash match {reused_id}")
                    return reused_res

            if job.get("status") == "done" and job.get("result") and _profile_cache_key(job, student_id, accessibility_mode):
                acc_path = config.OUTPUTS_DIR / f"{stem}_accessibility_{mode_name}.json"
                ext = "mp3" if config.TTS_PROVIDER == "openai" else "wav"
                narration_path = config.OUTPUTS_DIR / f"{stem}_narration.{ext}"
                if acc_path.exists() and (mode == "hearing" or narration_path.exists()):
                    return dict(job["result"]) | {"cached": True}
        except Exception:
            pass

    try:
        deps = video.check_system_dependencies()
        if not deps["ffmpeg"]:
            raise RuntimeError("FFmpeg is not installed or is not available on PATH.")

        visual_provider = "none"
        if mode in ("visual", "both"):
            visual_provider = vision._pick_provider()
            if visual_provider == "ocr" and not deps["tesseract"]:
                # Do not hard-fail: mark visual stage as degraded and continue.
                stage_status["_visual_warning"] = {
                    "status": "partial",
                    "fallback": "none",
                    "note": "Tesseract OCR not found on PATH; visual analysis may be unavailable.",
                }

        # ---- Stage: extract audio (skip-if-processed) ----
        with StageTimer(job_id, "extract_audio", stage_status) as t:
            storage.update_job(job_id, status="processing", progress=20, current_stage="extracting_audio")
            audio_path = config.AUDIO_DIR / f"{stem}.wav"
            if audio_path.exists():
                t.mark(status="cached", note="Reused existing extracted audio.")
            else:
                audio_path = Path(video.extract_audio(video_path, str(audio_path)))

        # ---- Stage: transcribe (skip-if-processed) ----
        with StageTimer(job_id, "transcribe", stage_status) as t:
            storage.update_job(job_id, status="processing", progress=35, current_stage="transcribing")
            cache = _load_video_cache(stem)
            if cache.get("segments"):
                transcription = {"text": cache["transcript_text"], "segments": cache["segments"]}
                t.mark(status="cached", note="Reused existing transcription.")
            else:
                if not speech.is_whisper_available():
                    transcription = {"text": "", "segments": [], "language": None}
                    t.mark(status="partial", note="Whisper STT not installed in this deployment; transcription skipped. Install openai-whisper to enable speech-to-text.")
                else:
                    # Arabic is first-class: detect the language, force "ar" when
                    # confidently Arabic, and always transcribe (never translate).
                    language = speech.resolve_language(
                        speech.detect_language(str(audio_path)))
                    transcription = speech.transcribe(str(audio_path), language=language)
                    # Record the effective STT language so downstream features
                    # (e.g. RTL captions) know what language the teacher spoke.
                    transcription.setdefault("language", language or "auto")
            transcript_path = speech.save_transcript(transcription, str(config.OUTPUTS_DIR / f"{stem}_transcript.txt"))
            srt_path = speech.save_srt(transcription["segments"], str(config.OUTPUTS_DIR / f"{stem}.srt"))
            # Persist segments + text so future jobs can skip transcription.
            _write_json(config.OUTPUTS_DIR / f"{stem}_segments.json",
                        {"job_id": job_id, "text": transcription["text"],
                         "segments": transcription["segments"],
                         "language": transcription.get("language", "auto")})
            if not transcription["text"].strip():
                t.mark(status="partial", note="No speech detected in this video.")

        metadata = video.get_video_metadata(video_path)
        result = {"transcript_text": transcription["text"].strip(), "transcript_path": transcript_path,
                  "srt_path": srt_path, "segments": transcription["segments"],
                  "stt_language": transcription.get("language", "auto"),
                  "stt_model_size": transcription.get("model_size", config.WHISPER_MODEL_SIZE),
                  "video_metadata": metadata}

        events: list[dict] = []
        frames: list[dict] = []
        frames_manifest: dict | None = None
        if mode in ("visual", "both"):
            # ---- Stage: analyze video (frames + vision) ----
            with StageTimer(job_id, "analyze_video", stage_status) as t:
                storage.update_job(job_id, status="processing", progress=50, current_stage="analyzing_video")
                cache = _load_video_cache(stem)
                existing = _load_existing_events(stem, job_id)
                if existing is not None:
                    events = existing
                else:
                    if cache.get("frames") and cache.get("video_metadata"):
                        frames = cache["frames"]
                        metadata = {**metadata, **cache["video_metadata"]}
                        result["frameless_reused"] = True
                    else:
                        frames = video.extract_frames(video_path, str(config.FRAMES_DIR / stem))
                        _write_json(config.OUTPUTS_DIR / f"{stem}_frames.json",
                                    {"job_id": job_id, "frames": frames, "metadata": metadata})
                    duration = float(metadata.get("duration") or 0.0)
                    events = []
                    degraded = 0
                    for i, frame in enumerate(frames):
                        start = frame["timestamp"]
                        end = frames[i + 1]["timestamp"] if i + 1 < len(frames) else duration
                        context = " ".join(s["text"].strip() for s in transcription["segments"] if start < s["end"] and end > s["start"])
                        analyzed = vision.describe_frame(frame["path"], context)
                        if analyzed.get("confidence", 1.0) == 0.0 or "Unavailable" in str(analyzed.get("description", "")):
                            degraded += 1
                        events.append({"start": start, "end": end, "type": analyzed["type"],
                                       "description": analyzed["description"], "transcript_context": context,
                                       "confidence": analyzed["confidence"], "source_frames": [Path(frame["path"]).name]})
                    status = "partial" if degraded == len(events) and events else "completed"
                    t.mark(status=status, fallback=visual_provider if visual_provider != "none" else None,
                           note=("Visual analysis fully unavailable; marked honestly." if status == "partial" else None))
            if not events:
                # Everything failed at the vision layer - keep honest, still usable.
                events = [{"start": 0.0, "end": float(metadata.get("duration") or 60.0),
                           "type": "scene", "description": "Visual analysis unavailable for this lecture.",
                           "transcript_context": "", "confidence": 0.0, "source_frames": []}]

            # ---- Stage: group visual events ----
            storage.update_job(job_id, status="processing", progress=65, current_stage="grouping_visual_events")
            events = accessibility.normalize_visual_events(events, job_id)
            visual_path = config.OUTPUTS_DIR / f"{stem}_visual_events.json"
            _write_json(visual_path, {"job_id": job_id, "events": events})
            result["frames"] = [{**frame, **{k: events[i].get(k) for k in ("description", "type", "confidence")}}
                                for i, frame in enumerate(frames)] if frames else []
            result["visual_events"] = events
            result["visual_events_path"] = str(visual_path)

            # ---- Stage: visual event analysis (grounded Visual Companion) ----
            from backend.services import visual_companion
            with StageTimer(job_id, "visual_event_analysis", stage_status) as t:
                storage.update_job(job_id, status="processing", progress=70,
                                   current_stage="grounding_visual_events")
                analysis_path = config.OUTPUTS_DIR / f"{stem}_visual_analysis.json"
                cached_analysis = _load_json_if_valid(analysis_path)
                if cached_analysis and isinstance(cached_analysis.get("events"), list):
                    analysis = cached_analysis["events"]
                    t.mark(status="cached", note="Reused existing visual event analysis.")
                else:
                    analysis = visual_companion.analyze_visual_events(
                        events, transcription["segments"], metadata, job_id)
                    _write_json(analysis_path, {"job_id": job_id, "events": analysis})
                    t.mark(status="completed")
            result["visual_analysis"] = analysis

            # ---- Stage: visual understanding (evidence-grounded structure) ----
            from backend.services import visual_understanding
            with StageTimer(job_id, "visual_understanding", stage_status) as t:
                storage.update_job(job_id, status="processing", progress=71,
                                   current_stage="building_visual_understanding")
                understanding_path = config.OUTPUTS_DIR / f"{stem}_visual_understanding.json"
                cached_understanding = _load_json_if_valid(understanding_path)
                if cached_understanding and isinstance(cached_understanding.get("records"), list):
                    understanding = cached_understanding["records"]
                    t.mark(status="cached", note="Reused existing visual understanding.")
                else:
                    understanding = visual_understanding.build_visual_understanding(
                        events, transcription["segments"], metadata, job_id)
                    _write_json(understanding_path,
                                {"job_id": job_id, "records": understanding})
                    t.mark(status="completed",
                           note=f"Built understanding for {len(understanding)} event(s).")
                result["visual_understanding"] = understanding
                result["visual_understanding_path"] = str(understanding_path)

            # ---- Stage: "What am I missing?" classification (audio vs visual) ----
            with StageTimer(job_id, "missing_information_analysis", stage_status) as t:
                storage.update_job(job_id, status="processing", progress=72,
                                   current_stage="classifying_missing_information")
                missing_path = config.OUTPUTS_DIR / f"{stem}_missing_analysis.json"
                cached_missing = _load_json_if_valid(missing_path)
                if cached_missing and isinstance(cached_missing.get("statuses"), list):
                    missing_statuses = cached_missing["statuses"]
                    t.mark(status="cached", note="Reused existing missing-information classification.")
                else:
                    missing_statuses = visual_companion.classify_missing_info(
                        events, transcription["segments"], analysis)
                    _write_json(missing_path, {"job_id": job_id, "statuses": missing_statuses})
                    t.mark(status="completed",
                           note=f"Classified {len(missing_statuses)} on-screen event(s).")
            result["missing_information_analysis"] = missing_statuses

        # ---- Stage: accessibility content ----
        with StageTimer(job_id, "accessibility", stage_status) as t:
            storage.update_job(job_id, status="processing", progress=80, current_stage="generating_accessibility")
            content = accessibility.build_accessibility_content(job_id, result["transcript_text"], result["segments"], events, profile)
            result["accessibility_profile"] = profile
            result["accessibility_events"] = content["accessibility_events"]
            result["accessibility_segments"] = content["accessibility_events"]
            result["captions"] = content["captions"]
            result["accessibility_quality_score"] = content["quality_score"]
            result["accessibility_metrics"] = content["metrics"]
            acc_write_path = config.OUTPUTS_DIR / f"{stem}_accessibility_{mode_name}.json"
            result["accessibility_content_path"] = _write_json(acc_write_path, content)
            _write_json(config.OUTPUTS_DIR / f"{stem}_captions.json", {"job_id": job_id, "captions": content["captions"]})
            (config.OUTPUTS_DIR / f"{stem}.vtt").write_text(accessibility.captions_vtt(content["captions"]), encoding="utf-8")

        result["full_narration"] = " ".join(e["description"] for e in content["accessibility_events"] if e.get("description"))

        # ---- Stage: audio descriptions & narration TTS (VoxCPM) ----
        if result["full_narration"] and mode in ("visual", "both"):
            with StageTimer(job_id, "narration", stage_status) as t:
                storage.update_job(job_id, status="processing", progress=82, current_stage="generating_audio")
                ext = "mp3" if config.TTS_PROVIDER == "openai" else "wav"
                narration_path = config.OUTPUTS_DIR / f"{stem}_narration.{ext}"
                try:
                    # 1. Synthesize individual event descriptions using VoxCPMService (with per-event cache)
                    from backend.services.ai.voxcpm_service import get_voxcpm_service
                    voxcpm = get_voxcpm_service()
                    content["accessibility_events"] = voxcpm.synthesize_event_descriptions(
                        content["accessibility_events"],
                        stem,
                        rate=float(profile.get("speech_rate", 1.0) or 1.0),
                    )

                    # 2. Mix combined narration track
                    tts.mix_narration_audio(
                        content["accessibility_events"],
                        float(metadata.get("duration") or 1.0),
                        str(narration_path),
                        rate=float(profile.get("speech_rate", 1.0) or 1.0),
                    )
                    result["narration_audio_path"] = str(narration_path)
                    _write_json(acc_write_path, content)
                    t.mark(status="completed", note="Synthesized VoxCPM narration audio descriptions.")
                except Exception as exc:
                    t.mark(status="partial", note=f"TTS unavailable or failed: {exc}")

        # ---- Stage: knowledge graph generation ----
        kg_data = {"concepts": []}
        with StageTimer(job_id, "knowledge_graph", stage_status) as t:
            try:
                storage.update_job(job_id, status="processing", progress=88, current_stage="building_knowledge_graph")
                from backend.services import knowledge_graph
                kg_data = knowledge_graph.get_knowledge_graph(job_id, use_cache=True)
                result["knowledge_graph"] = kg_data
                result["knowledge_graph_path"] = str(config.OUTPUTS_DIR / f"{stem}_knowledge_graph.json")
                t.mark(status="completed", note=f"Extracted {len(kg_data.get('concepts', []))} concepts.")
            except Exception as exc:
                t.mark(status="partial", note=f"Knowledge graph degraded: {exc}")

        # ---- Stage: multimodal RAG index creation ----
        with StageTimer(job_id, "rag_index", stage_status) as t:
            try:
                storage.update_job(job_id, status="processing", progress=92, current_stage="building_rag")
                from backend.services.rag import chunk_lecture_data, get_vector_store
                rag_chunks = chunk_lecture_data(
                    job_id,
                    result["segments"],
                    events,
                    concepts=kg_data.get("concepts"),
                    accessibility_events=content.get("accessibility_events"),
                )
                store = get_vector_store(job_id, stem)
                store.build_and_save(rag_chunks)
                result["rag_chunks_count"] = len(rag_chunks)
                result["rag_index_path"] = str(store.index_path)
                t.mark(status="completed", note=f"Indexed {len(rag_chunks)} multimodal chunks.")
            except Exception as exc:
                t.mark(status="partial", note=f"RAG indexing degraded: {exc}")

        # ---- Stage: quiz generation (Gemma) ----
        with StageTimer(job_id, "quiz", stage_status) as t:
            try:
                storage.update_job(job_id, status="processing", progress=95, current_stage="generating_quiz")
                from backend.services.quiz_generator import generate_quiz
                concept_names = [c.get("label") or c.get("concept_id") for c in kg_data.get("concepts", []) if c.get("label") or c.get("concept_id")]
                generate_quiz(job_id, result["transcript_text"], events, concepts=concept_names)
                quiz_path = config.QUIZZES_DIR / f"{job_id}_quiz.json"
                if quiz_path.exists():
                    result["quiz_id"] = f"{job_id}_quiz"
                t.mark(status="completed")
            except Exception as exc:
                t.mark(status="partial", note=f"Quiz generation unavailable: {exc}")

        # ---- Stage: finalizing & content hashing ----
        storage.update_job(job_id, status="processing", progress=98, current_stage="finalizing")
        result["pipeline_version"] = config.PIPELINE_VERSION
        result["gemma_model"] = config.HF_GEMMA_MODEL
        result["voxcpm_model"] = config.HF_VOXCPM_MODEL
        result["video_path"] = str(video_path)
        result["stage_status"] = stage_status

        # Content hash index mapping (for future upload instant reuse)
        raw_job = storage.get_job(job_id) if storage.job_exists(job_id) else {}
        content_hash = raw_job.get("content_hash")
        if content_hash:
            hash_file = config.HASHES_DIR / f"{content_hash}.json"
            hash_file.write_text(json.dumps({
                "job_id": job_id,
                "video_path": str(video_path),
                "stem": stem,
                "pipeline_version": config.PIPELINE_VERSION,
            }, ensure_ascii=False, indent=2), encoding="utf-8")

        storage.update_job(job_id, status="done", progress=100, current_stage="completed",
                           error=None, result=result)
        record_stage(job_id, "pipeline", ok=True, seconds=0.0, note="pipeline completed")
        return result
    except Exception as exc:
        storage.update_job(job_id, status="failed", error=str(exc))
        record_stage(job_id, "pipeline", ok=False, note=str(exc)[:500])
        return {"status": "failed", "error": str(exc)}