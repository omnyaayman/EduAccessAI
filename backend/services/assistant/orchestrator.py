"""Assistant Orchestrator for EduAccess AI.

Coordinates intent classification, deterministic action matching, multimodal
visual telemetry, accessibility disparity analysis, grounded RAG retrieval,
and general AI assistance across the platform.

Architecture:
- GENERAL AI ASSISTANT by default across the entire website.
- OPTIONAL CURRENT LECTURE CONTEXT when an active lecture is open and the user's
  query is lecture-specific.
- NEVER defaults to or injects DEMO_python_loops when outside a lecture context.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, AsyncGenerator

from backend import config, storage
from backend.services.ai.gemma_service import get_gemma_service
from backend.services.assistant.intent import AssistantIntent, classify_intent, requires_lecture_context
from backend.services.assistant.tools import execute_tool, ASSISTANT_TOOL_DEFINITIONS
from backend.services.rag import get_retriever

logger = logging.getLogger("eduaccess.ai.assistant.orchestrator")

GENERAL_AI_SYSTEM_PROMPT = (
    "You are EduAccess AI, an intelligent, accessible, and friendly educational AI assistant.\n"
    "You provide clear, accurate, concise, and helpful answers across programming, data science, AI/ML, math, science, and general education.\n"
    "When explaining concepts, break them down simply, provide intuitive examples where helpful, and keep answers accessible for learners of all backgrounds.\n"
    "You are not restricted to any single lecture. Answer general questions and ordinary conversation naturally and directly.\n"
    "An open lecture is not evidence that a general question refers to it. Do not introduce lecture details, timestamps, or citations unless the user's request asks about lecture content."
)

LECTURE_TUTOR_SYSTEM_PROMPT = (
    "You are EduAccess AI, an educational accessibility learning tutor.\n"
    "The student needs a simplified, beginner-friendly explanation, breakdown, or intuitive example.\n"
    "Explain the concept clearly and simply using the provided lecture evidence.\n"
    "Do not just copy or dump raw lecture transcript. Break it down step by step with clear intuition.\n"
    "When relevant, cite the timestamp (e.g. [01:24]).\n"
)

LECTURE_GROUNDED_SYSTEM_PROMPT = (
    "You are EduAccess AI, a helpful, accessible learning assistant.\n"
    "Answer the student's question accurately using the provided lecture context.\n"
    "Be clear, concise, and educational. When relevant, cite the timestamp (e.g. [01:24]).\n"
)


def _visual_description(visual: dict[str, Any]) -> str:
    description = str(visual.get("description") or "").strip()
    if description in (
        "No active lecture selected.",
        "No visual event found at this timestamp.",
        "Standard video scene without notable slides or code.",
    ):
        return ""
    return description


def _lecture_evidence(
    chunks: list[dict[str, Any]],
    segment: dict[str, Any],
    visual: dict[str, Any],
    timestamp: float,
) -> list[dict[str, str]]:
    """Carry retrieved and current multimodal evidence in both response modes."""
    evidence = [
        {"time": str(c.get("timestamp_label") or ""), "snippet": str(c.get("text") or "")[:120]}
        for c in chunks[:3]
    ]
    time_label = f"{int(timestamp // 60):02d}:{int(timestamp % 60):02d}"
    speech = str(segment.get("text") or "").strip()
    if speech and speech not in ("No speech detected at this exact second.", "No active lecture selected."):
        evidence.append({"time": time_label, "type": "transcript", "snippet": speech[:120]})
    description = _visual_description(visual)
    ocr = str(visual.get("ocr_text") or "").strip()
    if description or ocr:
        evidence.append({
            "time": time_label,
            "type": str(visual.get("type") or "visual"),
            "snippet": (description or ocr)[:120],
        })
    return evidence[:3]


class AssistantOrchestrator:
    """Orchestrator for the floating global assistant."""

    def __init__(self):
        self.gemma = get_gemma_service()

    def _general_fallback(self, clean_msg: str) -> str:
        """Deterministic educational explanation when cloud AI is unreachable."""
        lower = clean_msg.lower()
        if "python" in lower:
            return "Python is a high-level, interpreted programming language known for its clear syntax and versatility across web development, data science, automation, and AI."
        if "for loop" in lower or "حلقة" in lower:
            return "A for loop is a control flow statement used to iterate over a sequence (such as a list, string, or range) and execute a block of code for each element."
        if "while loop" in lower:
            return "A while loop executes a block of code repeatedly as long as a given boolean condition evaluates to True."
        if "machine learning" in lower or "ml" in lower:
            return "Machine learning is a field of artificial intelligence focused on building algorithms that learn patterns from data to make predictions or decisions."
        if "sql" in lower:
            return "SQL (Structured Query Language) is the standard language for storing, retrieving, and manipulating data in relational databases."
        if "recursion" in lower:
            return "Recursion is a programming technique where a function calls itself to solve smaller instances of the same problem until a base condition is met."
        if "neural network" in lower:
            return "Neural networks are computational models inspired by biological neural networks, consisting of layers of nodes that process data to recognize patterns."
        if "data science" in lower:
            return "Data science is an interdisciplinary field that uses statistical and computational methods to extract meaningful insights and knowledge from data."
        return f"I am EduAccess AI, your accessible learning companion. I'm here to help explain concepts, write code examples, and assist with your studies. Let me know what you'd like to explore!"

    def chat(
        self,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Process an assistant message, routing by intent and context awareness."""
        clean_msg = message.strip()
        classification = classify_intent(clean_msg)
        intent = classification.intent

        # 1. Deterministic UI actions (captions, audio descriptions, font size, open quiz)
        if intent == AssistantIntent.DETERMINISTIC_ACTION:
            return {
                "reply": classification.direct_reply or "Action executed.",
                "action": classification.action,
                "action_payload": classification.action_payload,
                "evidence": [],
                "provider": "deterministic_action",
            }

        # 2. Conversational, Platform explanation, and Ambiguous clarification
        if intent in (AssistantIntent.CONVERSATIONAL, AssistantIntent.PLATFORM, AssistantIntent.CLARIFICATION):
            return {
                "reply": classification.direct_reply or "",
                "action": None,
                "evidence": [],
                "provider": "intent_router",
            }

        # 3. Extract and normalize lecture context (if active)
        job_id = (
            context.get("lecture_id")
            or context.get("job_id")
            or context.get("lectureId")
            or context.get("job")
            or ""
        )
        has_active_lecture = bool(job_id and storage.job_exists(job_id))
        timestamp = float(context.get("timestamp") or 0.0)

        # 4. Learning Progress / Next Best Action
        if intent == AssistantIntent.LEARNING_PROGRESS:
            try:
                from backend.services import learning_agent
                student_id = context.get("student_id") or "default_student"
                agent_view = learning_agent.build_personal_agent(student_id)
                insights = agent_view.get("insights", [])
                recommended = agent_view.get("recommended_actions", [])

                mastery_info = next((ins for ins in insights if ins.get("kind") == "mastery"), None)
                if mastery_info:
                    mastered = mastery_info.get("mastered", [])
                    needs_work = mastery_info.get("needs_work", [])
                    reply = "📊 **Learning Progress Summary**:\n"
                    if mastered:
                        reply += f"• **Mastered Concepts**: {', '.join(mastered)}\n"
                    if needs_work:
                        reply += f"• **Needs Review**: {', '.join(needs_work)}\n"

                    if recommended:
                        top_rec = recommended[0]
                        rec_label = top_rec.get("label") or top_rec.get("action_type", "Review")
                        rec_reason = top_rec.get("reasoning", "")
                        reply += f"\n🎯 **Recommended Next Action**: {rec_label}\n{rec_reason}"
                else:
                    reply = (
                        "You haven't completed any quizzes yet. "
                        "Complete a quiz on a lecture in the Studio to diagnose your learning gaps and get personalized study recommendations!"
                    )
            except Exception as exc:
                logger.warning("Error building personal learning agent: %s", exc)
                reply = "Complete a quiz on a lecture in the Studio to see your personalized learning progress and study recommendations!"

            return {
                "reply": reply,
                "action": "open_learning" if has_active_lecture else None,
                "evidence": [],
                "provider": "learning_agent",
            }

        # 5. Quiz & Practice Intent
        if intent == AssistantIntent.QUIZ:
            if not has_active_lecture:
                return {
                    "reply": "Open or process a lecture first to practice with interactive quizzes, or ask me any topic to test your knowledge!",
                    "action": None,
                    "evidence": [],
                    "provider": "none",
                }

            try:
                from backend.services import quiz as quiz_svc
                quiz_file = config.QUIZZES_DIR / f"{job_id}_quiz.json"
                if quiz_file.exists():
                    q_list = quiz_svc.load_quiz(f"{job_id}_quiz")
                    if q_list:
                        first_q = q_list[0]
                        options = first_q.get("options", [])
                        opts_str = "\n".join(f"  • {opt}" for opt in options) if options else ""
                        reply = (
                            f"📝 **Lecture Practice Question**:\n\n"
                            f"**{first_q.get('question')}**\n"
                            f"{opts_str}\n\n"
                            f"Opening the interactive Quiz in the Studio for you to practice."
                        )
                        return {
                            "reply": reply,
                            "action": "open_quiz",
                            "action_payload": {"action": "open_quiz", "message": "Opening lecture quiz."},
                            "evidence": [],
                            "provider": "quiz_service",
                        }
            except Exception as err:
                logger.warning("Failed to load quiz for %s: %s", job_id, err)

            return {
                "reply": "Opening the interactive Quiz panel in the Studio for this lecture.",
                "action": "open_quiz",
                "action_payload": {"action": "open_quiz", "message": "Opening lecture quiz."},
                "evidence": [],
                "provider": "quiz_service",
            }

        # 7. Accessibility Intent ("What was shown but not explained?")
        if intent == AssistantIntent.ACCESSIBILITY:
            if not has_active_lecture:
                return {
                    "reply": "Please open or select a lecture video first to analyze accessibility gaps.",
                    "action": None,
                    "evidence": [],
                    "provider": "none",
                }

            job = storage.get_job(job_id)
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

        # Lecture evidence is used only when the message itself requires lecture context.
        lecture_ref = requires_lecture_context(clean_msg, intent)

        # 8A. Query is lecture-specific
        if lecture_ref:
            if not has_active_lecture:
                return {
                    "reply": "Please open or select a lecture video first to ask questions about a specific lecture or on-screen content.",
                    "action": None,
                    "evidence": [],
                    "provider": "none",
                }

            job = storage.get_job(job_id)
            stem = Path(job.get("video_path", "")).stem or job_id

            current_segment = execute_tool("get_current_segment", {}, context)
            current_visual = execute_tool("get_current_visual_event", {}, context)

            retriever = get_retriever(job_id, stem)
            chunks = retriever.retrieve(clean_msg, top_k=config.MAX_RAG_CHUNKS)
            rag_context = ""
            if chunks:
                rag_context = "\n---\n".join(f"{c.get('timestamp_label', '')}: {c.get('text', '')}" for c in chunks)
            evidence_list = _lecture_evidence(chunks, current_segment, current_visual, timestamp)
            visual_description = _visual_description(current_visual)

            if intent == AssistantIntent.LEARNING_HELP:
                system_prompt = LECTURE_TUTOR_SYSTEM_PROMPT
                user_prompt = f"Student Request: {clean_msg}\n\n"
            else:
                system_prompt = LECTURE_GROUNDED_SYSTEM_PROMPT
                user_prompt = f"Student Question: {clean_msg}\n\n"

            if rag_context:
                user_prompt += f"Relevant Lecture Evidence:\n{rag_context}\n\n"
            if current_segment.get("text") and current_segment.get("text") not in ("No speech detected at this exact second.", "No active lecture selected."):
                user_prompt += f"Current Speech ({int(timestamp//60):02d}:{int(timestamp%60):02d}): {current_segment.get('text')}\n"
            if visual_description:
                user_prompt += f"Current Visual ({current_visual.get('type')}): {visual_description}\n"
            if current_visual.get("ocr_text"):
                user_prompt += f"On-Screen OCR Text: {current_visual.get('ocr_text')}\n"

            if not rag_context and not current_segment.get("text") and not visual_description and not current_visual.get("ocr_text"):
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
                    if intent == AssistantIntent.LEARNING_HELP:
                        reply = (
                            f"Here is a simple breakdown from the lecture at [{top.get('timestamp_label', '')}]:\n\n"
                            f"• **Key Concept**: {top.get('text', '')}\n"
                            f"• **Intuition**: The instructor explains and demonstrates this step by step."
                        )
                    else:
                        reply = f"Based on the lecture at [{top.get('timestamp_label', '')}]: {top.get('text', '')}"
                        if len(chunks) > 1:
                            reply += f"\n\nAdditional context at [{chunks[1].get('timestamp_label', '')}]: {chunks[1].get('text', '')}"
                    provider = "grounded_evidence"
                elif current_segment.get("text") and current_segment.get("text") not in ("No speech detected at this exact second.", "No active lecture selected."):
                    reply = f"At [{int(timestamp//60):02d}:{int(timestamp%60):02d}], the instructor explains: {current_segment.get('text')}"
                    provider = "transcript_segment"
                elif visual_description or current_visual.get("ocr_text"):
                    visible = visual_description or str(current_visual.get("ocr_text") or "").strip()
                    reply = f"At [{int(timestamp//60):02d}:{int(timestamp%60):02d}], the visible {current_visual.get('type') or 'content'} shows: {visible}"
                    if current_visual.get("ocr_text") and visual_description:
                        reply += f"\nOn-screen text: {current_visual.get('ocr_text')}"
                    provider = "visual_context"
                else:
                    reply = f"I could not reach cloud AI: {exc}. Grounded evidence was cited where available."
                    provider = "unavailable"

            return {
                "reply": reply,
                "action": None,
                "evidence": evidence_list,
                "provider": provider,
            }

        # 8B. Query is GENERAL (General AI Mode across website)
        # Even if a lecture is open, general questions like "What is SQL?", "What is Python?",
        # "Explain recursion simply", or "What is machine learning?" route to General AI.
        try:
            reply = self.gemma.generate_cloud(
                clean_msg,
                system_prompt=GENERAL_AI_SYSTEM_PROMPT,
                history=history,
                max_new_tokens=400,
            )
            provider = "huggingface/gemma"
        except Exception as exc:
            logger.warning("General AI Gemma cloud call failed: %s; using general fallback.", exc)
            reply = self._general_fallback(clean_msg)
            provider = "general_ai"

        return {
            "reply": reply,
            "action": None,
            "evidence": [],
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
        classification = classify_intent(clean_msg)
        intent = classification.intent

        # 1. Deterministic action
        if intent == AssistantIntent.DETERMINISTIC_ACTION:
            yield json.dumps({
                "token": classification.direct_reply or "Action executed.",
                "action": classification.action,
                "action_payload": classification.action_payload,
                "done": True,
            })
            return

        # 2. Conversational, Platform, Clarification
        if intent in (AssistantIntent.CONVERSATIONAL, AssistantIntent.PLATFORM, AssistantIntent.CLARIFICATION):
            direct_reply = classification.direct_reply or ""
            words = direct_reply.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                yield json.dumps({"token": chunk, "done": False})
            yield json.dumps({"token": "", "done": True})
            return

        job_id = (
            context.get("lecture_id")
            or context.get("job_id")
            or context.get("lectureId")
            or context.get("job")
            or ""
        )
        has_active_lecture = bool(job_id and storage.job_exists(job_id))
        timestamp = float(context.get("timestamp") or 0.0)

        # 3. Non-generative intents (Visual, Accessibility, Quiz, Progress)
        if intent in (AssistantIntent.CURRENT_VISUAL, AssistantIntent.ACCESSIBILITY, AssistantIntent.QUIZ, AssistantIntent.LEARNING_PROGRESS):
            chat_res = self.chat(clean_msg, context, history=history)
            full_reply = chat_res.get("reply", "")
            action = chat_res.get("action")
            action_payload = chat_res.get("action_payload")
            words = full_reply.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                yield json.dumps({"token": chunk, "done": False})
            yield json.dumps({"token": "", "action": action, "action_payload": action_payload, "evidence": chat_res.get("evidence", []), "done": True})
            return

        # Use the same message-level lecture-context decision as chat().
        lecture_ref = requires_lecture_context(clean_msg, intent)

        # 4A. Lecture-specific streaming
        if lecture_ref:
            if not has_active_lecture:
                yield json.dumps({"token": "Please open or select a lecture video first to ask questions about a specific lecture or on-screen content.", "done": True})
                return

            job = storage.get_job(job_id)
            stem = Path(job.get("video_path", "")).stem or job_id

            current_segment = execute_tool("get_current_segment", {}, context)
            current_visual = execute_tool("get_current_visual_event", {}, context)

            retriever = get_retriever(job_id, stem)
            chunks = retriever.retrieve(clean_msg, top_k=config.MAX_RAG_CHUNKS)
            rag_context = ""
            if chunks:
                rag_context = "\n---\n".join(f"{c.get('timestamp_label', '')}: {c.get('text', '')}" for c in chunks)
            visual_description = _visual_description(current_visual)

            if intent == AssistantIntent.LEARNING_HELP:
                system_prompt = LECTURE_TUTOR_SYSTEM_PROMPT
                user_prompt = f"Student Request: {clean_msg}\n\n"
            else:
                system_prompt = LECTURE_GROUNDED_SYSTEM_PROMPT
                user_prompt = f"Student Question: {clean_msg}\n\n"

            if rag_context:
                user_prompt += f"Relevant Lecture Evidence:\n{rag_context}\n\n"
            if current_segment.get("text") and current_segment.get("text") not in ("No speech detected at this exact second.", "No active lecture selected."):
                user_prompt += f"Current Speech ({int(timestamp//60):02d}:{int(timestamp%60):02d}): {current_segment.get('text')}\n"
            if visual_description:
                user_prompt += f"Current Visual ({current_visual.get('type')}): {visual_description}\n"
            if current_visual.get("ocr_text"):
                user_prompt += f"On-Screen OCR Text: {current_visual.get('ocr_text')}\n"

            if not rag_context and not current_segment.get("text") and not visual_description and not current_visual.get("ocr_text"):
                yield json.dumps({"token": "I could not find verified evidence in this lecture for that question. Please ask a question related to the lecture content.", "done": True})
                return

            try:
                async for token in self.gemma.stream_chat(user_prompt, system_prompt=system_prompt, history=history):
                    yield json.dumps({"token": token, "done": False})
            except Exception as exc:
                logger.warning("Gemma streaming failed: %s; falling back to grounded chunks.", exc)
                if chunks:
                    top = chunks[0]
                    if intent == AssistantIntent.LEARNING_HELP:
                        fb_text = (
                            f"Here is a simple breakdown from the lecture at [{top.get('timestamp_label', '')}]:\n\n"
                            f"• **Key Concept**: {top.get('text', '')}\n"
                            f"• **Intuition**: The instructor explains and demonstrates this step by step."
                        )
                    else:
                        fb_text = f"Based on the lecture at [{top.get('timestamp_label', '')}]: {top.get('text', '')}"
                        if len(chunks) > 1:
                            fb_text += f"\n\nAdditional context at [{chunks[1].get('timestamp_label', '')}]: {chunks[1].get('text', '')}"
                    words = fb_text.split(" ")
                    for i in range(0, len(words), 3):
                        chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                        yield json.dumps({"token": chunk, "done": False})
                elif current_segment.get("text") and current_segment.get("text") not in ("No speech detected at this exact second.", "No active lecture selected."):
                    fb_text = f"At [{int(timestamp//60):02d}:{int(timestamp%60):02d}], the instructor explains: {current_segment.get('text')}"
                    words = fb_text.split(" ")
                    for i in range(0, len(words), 3):
                        chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                        yield json.dumps({"token": chunk, "done": False})
                elif visual_description or current_visual.get("ocr_text"):
                    visible = visual_description or str(current_visual.get("ocr_text") or "").strip()
                    fb_text = f"At [{int(timestamp//60):02d}:{int(timestamp%60):02d}], the visible {current_visual.get('type') or 'content'} shows: {visible}"
                    if current_visual.get("ocr_text") and visual_description:
                        fb_text += f"\nOn-screen text: {current_visual.get('ocr_text')}"
                    words = fb_text.split(" ")
                    for i in range(0, len(words), 3):
                        chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                        yield json.dumps({"token": chunk, "done": False})
                else:
                    yield json.dumps({"token": f"Cloud AI unavailable: {exc}. Grounded evidence was cited where available.", "done": False})

            yield json.dumps({"token": "", "evidence": _lecture_evidence(chunks, current_segment, current_visual, timestamp), "done": True})
            return

        # 4B. General AI streaming mode
        try:
            async for token in self.gemma.stream_chat(clean_msg, system_prompt=GENERAL_AI_SYSTEM_PROMPT, history=history, max_new_tokens=400):
                yield json.dumps({"token": token, "done": False})
        except Exception as exc:
            logger.warning("Gemma streaming failed for general chat: %s; using general fallback.", exc)
            fb_text = self._general_fallback(clean_msg)
            words = fb_text.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                yield json.dumps({"token": chunk, "done": False})

        yield json.dumps({"token": "", "done": True})


_orchestrator: AssistantOrchestrator | None = None

def get_assistant_orchestrator() -> AssistantOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AssistantOrchestrator()
    return _orchestrator
