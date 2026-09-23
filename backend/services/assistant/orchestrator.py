"""Assistant Orchestrator for EduAccess AI.

Coordinates context assembly, deterministic action matching, RAG retrieval,
and Gemma generation for the global AI assistant.
"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

from backend import config, storage
from backend.services.ai.gemma_service import get_gemma_service
from backend.services.assistant.tools import execute_tool, ASSISTANT_TOOL_DEFINITIONS
from backend.services.rag import get_retriever

logger = logging.getLogger("eduaccess.ai.assistant.orchestrator")


class AssistantOrchestrator:
    """Orchestrator for the floating global assistant."""

    def __init__(self):
        self.gemma = get_gemma_service()

    def _match_deterministic_action(self, user_msg: str) -> dict[str, Any] | None:
        """Fast deterministic route for simple UI commands (Token Optimization)."""
        msg = user_msg.lower().strip()

        # Captions
        if any(p in msg for p in ("turn on caption", "enable caption", "show caption", "شغل الترجمة", "فعل الترجمة")):
            return {"action": "toggle_captions", "enabled": True, "message": "Captions have been enabled."}
        if any(p in msg for p in ("turn off caption", "disable caption", "hide caption", "اوقف الترجمة", "الغاء الترجمة")):
            return {"action": "toggle_captions", "enabled": False, "message": "Captions have been disabled."}

        # Audio descriptions
        if any(p in msg for p in ("turn on audio desc", "enable audio desc", "start narration", "شغل الوصف الصوتي")):
            return {"action": "toggle_audio_description", "enabled": True, "message": "Spoken audio descriptions turned on."}
        if any(p in msg for p in ("turn off audio desc", "disable audio desc", "stop narration", "اوقف الوصف الصوتي")):
            return {"action": "toggle_audio_description", "enabled": False, "message": "Spoken audio descriptions turned off."}

        # Open quiz
        if any(p in msg for p in ("open quiz", "take quiz", "start quiz", "show quiz", "give me a quiz", "افتح الاختبار", "بدء الاختبار")):
            return {"action": "open_quiz", "message": "Opening the lecture quiz."}

        if "next question" in msg:
            return {"action": "next_quiz_question", "message": "Moving to the next quiz question."}
        if any(p in msg for p in ("increase font", "larger text", "make text bigger")):
            return {"action": "font_size", "delta": 1, "message": "Increasing text size."}
        if any(p in msg for p in ("decrease font", "smaller text", "make text smaller")):
            return {"action": "font_size", "delta": -1, "message": "Decreasing text size."}

        return None

    def chat(
        self,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Process an assistant message, returning response text and any triggered action."""
        clean_msg = message.strip()
        if not clean_msg:
            return {"reply": "How can I help you with your lecture today?", "action": None}

        # 1. Check deterministic action
        det_action = self._match_deterministic_action(clean_msg)
        if det_action:
            return {
                "reply": det_action["message"],
                "action": det_action.get("action"),
                "action_payload": det_action,
                "evidence": [],
            }

        # 2. Extract and normalize context
        job_id = (
            context.get("lecture_id")
            or context.get("job_id")
            or context.get("lectureId")
            or context.get("job")
            or ""
        )
        timestamp = float(context.get("timestamp") or 0.0)

        # 3. Validate lecture context presence
        if not job_id or not storage.job_exists(job_id):
            return {
                "reply": "Open or process a lecture first to use the content-aware Assistant.",
                "action": None,
                "evidence": [],
                "provider": "none",
            }

        job = storage.get_job(job_id)
        from pathlib import Path
        stem = Path(job.get("video_path", "")).stem or job_id

        current_segment = execute_tool("get_current_segment", {}, context)
        current_visual = execute_tool("get_current_visual_event", {}, context)

        # 4. Handle "What am I looking at right now" / "What is on screen"
        lower_msg = clean_msg.lower()
        if any(k in lower_msg for k in ("what am i looking at", "what is on screen", "what is shown", "ماذا يظهر", "ما المعروض")):
            vtype = current_visual.get("type", "scene")
            vdesc = current_visual.get("description", "Standard lecture video scene.")
            ocr = current_visual.get("ocr_text", "")
            time_str = f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"

            reply = f"At [{time_str}], you are looking at a {vtype}: {vdesc}"
            if ocr and ocr.strip():
                reply += f"\n\nOn-screen text:\n{ocr.strip()}"
            speech = current_segment.get("text")
            if speech and speech != "No speech detected at this exact second." and speech != "No active lecture selected.":
                reply += f"\n\nInstructor speech at this moment: \"{speech.strip()}\""

            return {
                "reply": reply,
                "action": None,
                "evidence": [{"time": time_str, "type": vtype, "snippet": vdesc}],
                "provider": "visual_telemetry",
            }

        # 5. Handle "What was shown but not explained?" / "What am I missing?"
        if any(k in lower_msg for k in ("what was shown but not explained", "what am i missing", "ما الذي فاتني", "ما الذي لم يشرح")):
            from backend.services import lecture_data, visual_companion
            result_obj = job.get("result") or {}
            segments = lecture_data.load_segments(job, result_obj)
            events = lecture_data.load_visual_events(job, result_obj)
            analysis = []
            if hasattr(lecture_data, "load_analysis"):
                analysis = lecture_data.load_analysis(job, result_obj, events)
            elif isinstance(result_obj.get("analysis"), list):
                analysis = result_obj.get("analysis", [])

            missing_items = visual_companion.build_missing_items(segments, events, analysis, "blind", lecture_id=job_id)
            time_str = f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"
            
            # Find gap near current timestamp or first gap
            nearby_gap = None
            for item in missing_items:
                start_t = float(item.get("timestamp_start") or item.get("timestamp") or 0.0)
                if abs(start_t - timestamp) <= 30.0:
                    nearby_gap = item
                    break
            target_gap = nearby_gap or (missing_items[0] if missing_items else None)

            if target_gap:
                gap_start = float(target_gap.get("timestamp_start") or target_gap.get("timestamp") or 0.0)
                gap_label = f"{int(gap_start//60):02d}:{int(gap_start%60):02d}"
                v_claim = target_gap.get("missing_information") or target_gap.get("what_you_might_miss") or "Visual content on screen"
                s_claim = target_gap.get("what_you_hear") or "General spoken description"
                reasoning = target_gap.get("why_it_matters") or "Visual detail not fully explained by speech."
                
                reply = (
                    f"Accessibility Disparity Gap at [{gap_label}]:\n"
                    f"• Visual on screen: {v_claim}\n"
                    f"• Spoken by instructor: \"{s_claim}\"\n"
                    f"• Reason for gap: {reasoning}"
                )
                evidence = [{"time": gap_label, "type": "gap_disparity", "snippet": str(v_claim)[:120]}]
            else:
                reply = f"At [{time_str}], the visual elements shown on screen are closely aligned with the instructor's spoken explanation."
                evidence = []

            return {
                "reply": reply,
                "action": None,
                "evidence": evidence,
                "provider": "gap_reasoning",
            }

        # 6. Multimodal RAG query via hybrid retriever
        retriever = get_retriever(job_id, stem)
        chunks = retriever.retrieve(clean_msg, top_k=config.MAX_RAG_CHUNKS)
        rag_context = ""
        evidence_list = []
        if chunks:
            rag_context = "\n---\n".join(f"{c.get('timestamp_label', '')}: {c.get('text', '')}" for c in chunks)
            evidence_list = [
                {"time": c.get("timestamp_label"), "snippet": c.get("text", "")[:120]}
                for c in chunks[:3]
            ]

        # 7. Formulate prompt for Gemma
        system_prompt = (
            "You are EduAccess AI, a helpful, accessible learning assistant.\n"
            "Answer the student's question accurately using the provided lecture context.\n"
            "Be clear, concise, and educational. When relevant, cite the timestamp.\n"
        )
        user_prompt = f"Student Question: {clean_msg}\n\n"
        if rag_context:
            user_prompt += f"Relevant Lecture Evidence:\n{rag_context}\n\n"
        if current_segment.get("text") and current_segment.get("text") not in ("No speech detected at this exact second.", "No active lecture selected."):
            user_prompt += f"Current Speech ({int(timestamp//60):02d}:{int(timestamp%60):02d}): {current_segment.get('text')}\n"
        if current_visual.get("description") and current_visual.get("description") not in ("No active lecture selected.",):
            user_prompt += f"Current Visual ({current_visual.get('type')}): {current_visual.get('description')}\n"

        if not rag_context and not current_segment.get("text") and not current_visual.get("description"):
            return {
                "reply": "I could not find verified evidence in this lecture for that question. Please ask a question related to the lecture content.",
                "action": None,
                "evidence": [],
                "provider": "none",
            }

        try:
            reply = self.gemma.generate_cloud(user_prompt, system_prompt=system_prompt, history=history, max_new_tokens=300)
            provider = "huggingface/gemma"
        except Exception as exc:
            logger.warning("Learner-facing Gemma cloud call failed: %s; using grounded fallback.", exc)
            if chunks:
                top = chunks[0]
                reply = f"Based on the lecture at [{top.get('timestamp_label', '')}]: {top.get('text', '')}"
                if len(chunks) > 1:
                    reply += f"\n\nAdditional context at [{chunks[1].get('timestamp_label', '')}]: {chunks[1].get('text', '')}"
                provider = "grounded_evidence"
            elif current_segment.get("text"):
                reply = f"At [{int(timestamp//60):02d}:{int(timestamp%60):02d}], the instructor explains: {current_segment.get('text')}"
                provider = "transcript_segment"
            else:
                reply = f"I could not reach cloud AI: {exc}. Grounded evidence was cited where available."
                provider = "unavailable"

        return {
            "reply": reply,
            "action": None,
            "evidence": evidence_list,
            "provider": provider,
        }

    async def stream_chat(
        self,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream assistant response tokens via SSE."""
        clean_msg = message.strip()
        if not clean_msg:
            yield json.dumps({"token": "How can I help you with your lecture today?", "done": True})
            return

        # For simple deterministic actions, emit immediately
        det_action = self._match_deterministic_action(clean_msg)
        if det_action:
            yield json.dumps({"token": det_action["message"], "action": det_action.get("action"), "action_payload": det_action, "done": True})
            return

        job_id = (
            context.get("lecture_id")
            or context.get("job_id")
            or context.get("lectureId")
            or context.get("job")
            or ""
        )
        timestamp = float(context.get("timestamp") or 0.0)

        if not job_id or not storage.job_exists(job_id):
            yield json.dumps({"token": "Open or process a lecture first to use the content-aware Assistant.", "done": True})
            return

        # Special query routes (visual on-screen and missing disparity)
        lower_msg = clean_msg.lower()
        if any(k in lower_msg for k in ("what am i looking at", "what is on screen", "what is shown", "what was shown but not explained", "what am i missing", "ماذا يظهر", "ما المعروض", "ما الذي فاتني")):
            chat_res = self.chat(clean_msg, context, history=history)
            full_reply = chat_res.get("reply", "")
            words = full_reply.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                yield json.dumps({"token": chunk, "done": False})
            yield json.dumps({"token": "", "done": True})
            return

        job = storage.get_job(job_id)
        from pathlib import Path
        stem = Path(job.get("video_path", "")).stem or job_id

        current_segment = execute_tool("get_current_segment", {}, context)
        current_visual = execute_tool("get_current_visual_event", {}, context)

        # Retrieve RAG context
        rag_context = ""
        retriever = get_retriever(job_id, stem)
        chunks = retriever.retrieve(clean_msg, top_k=config.MAX_RAG_CHUNKS)
        if chunks:
            rag_context = "\n---\n".join(f"{c.get('timestamp_label', '')}: {c.get('text', '')}" for c in chunks)

        system_prompt = (
            "You are EduAccess AI, a helpful, accessible learning assistant.\n"
            "Answer the student's question accurately using the provided lecture context.\n"
            "Be clear, concise, and educational. When relevant, cite the timestamp.\n"
        )
        user_prompt = f"Student Question: {clean_msg}\n\n"
        if rag_context:
            user_prompt += f"Relevant Lecture Evidence:\n{rag_context}\n\n"
        if current_segment.get("text") and current_segment.get("text") not in ("No speech detected at this exact second.", "No active lecture selected."):
            user_prompt += f"Current Speech ({int(timestamp//60):02d}:{int(timestamp%60):02d}): {current_segment.get('text')}\n"
        if current_visual.get("description") and current_visual.get("description") not in ("No active lecture selected.",):
            user_prompt += f"Current Visual ({current_visual.get('type')}): {current_visual.get('description')}\n"

        try:
            async for token in self.gemma.stream_chat(user_prompt, system_prompt=system_prompt, history=history):
                yield json.dumps({"token": token, "done": False})
        except Exception as exc:
            logger.warning("Gemma streaming failed: %s; falling back to grounded chunks.", exc)
            if chunks:
                top = chunks[0]
                fb_text = f"Based on the lecture at [{top.get('timestamp_label', '')}]: {top.get('text', '')}"
                words = fb_text.split(" ")
                for i in range(0, len(words), 3):
                    chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                    yield json.dumps({"token": chunk, "done": False})
            else:
                yield json.dumps({"token": f"Cloud AI unavailable: {exc}. No substitute answer was generated.", "done": False})

        yield json.dumps({"token": "", "done": True})


_orchestrator: AssistantOrchestrator | None = None

def get_assistant_orchestrator() -> AssistantOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AssistantOrchestrator()
    return _orchestrator
