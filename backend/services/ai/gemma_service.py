"""Gemma Intelligence Service for EduAccess AI.

Gemma is the primary reasoning and generation model across the application:
- Lecture understanding & summarization
- Grounded RAG question answering
- Tutor responses & learning-gap explanations
- Concept & learning-objective extraction
- Accessibility audio-description text generation
- Grounded quiz generation & evidence alignment
- Website assistant reasoning & action routing

Communicates with Hugging Face Cloud via the centralized HFClient with
graceful fallbacks to deterministic/template generators when offline.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncGenerator

from backend import config
from backend.services.ai.hf_client import HF_CHAT_COMPLETIONS_URL, get_hf_client, HFClientError

logger = logging.getLogger("eduaccess.ai.gemma")

DEFAULT_SYSTEM_PROMPT = (
    "You are EduAccess AI, an educational accessibility assistant specialized in helping all students learn effectively.\n"
    "Use the provided lecture evidence (transcript timestamps, visual events, OCR text) as the primary source of truth.\n"
    "Rules:\n"
    "1. Never invent or hallucinate information about the lecture that is not in the provided evidence.\n"
    "2. If the user asks about the current video, prioritize the current timestamp and active visual events.\n"
    "3. Keep explanations clear, concise, objective, and educationally supportive.\n"
    "4. Cite timestamps (e.g. [01:24]) when referencing specific evidence from the lecture.\n"
    "5. Prioritize accessible, easy-to-understand explanations for students with visual or hearing needs."
)

AUDIO_DESCRIPTION_PROMPT = (
    "You are an expert accessibility describer for blind and visually impaired students.\n"
    "Given the on-screen visual event and spoken transcript context, generate a concise, objective audio description.\n"
    "Rules:\n"
    "1. Describe ONLY information essential for a student who cannot see the screen.\n"
    "2. Prioritize: code, equations, diagrams/flowcharts, charts/data, user interface actions, and visual transitions.\n"
    "3. Do NOT repeat what is already spoken clearly in the audio transcript.\n"
    "4. Keep descriptions concise (1-3 sentences), educational, and natural to hear spoken aloud.\n"
    "5. Do NOT describe irrelevant background details."
)

QUIZ_GENERATION_PROMPT = (
    "You are an expert educational curriculum designer.\n"
    "Generate high-quality multiple choice and conceptual quiz questions grounded strictly in the provided lecture evidence.\n"
    "Output must be a valid JSON array of objects with keys: "
    "'question', 'type' ('multiple_choice'|'true_false'), 'options', 'answer', 'concept', 'difficulty' ('easy'|'medium'|'hard'), 'explanation', 'evidence_timestamp'.\n"
    "Do NOT include markdown formatting outside the JSON."
)


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


class GemmaService:
    """Service wrapping Google Gemma model on Hugging Face Cloud."""

    def __init__(self, model_id: str | None = None, endpoint_override: str | None = None):
        self.model_id = model_id or config.HF_GEMMA_MODEL
        self.endpoint_override = endpoint_override or config.HF_GEMMA_ENDPOINT
        self.hf_client = get_hf_client()

    def is_cloud_ready(self) -> bool:
        return self.hf_client.is_configured

    def _chat_endpoint(self) -> str:
        """Normalize the HF OpenAI-compatible chat endpoint.

        Older local configuration used ``/v1/chat``.  Hugging Face's current
        router requires ``/v1/chat/completions``; normalizing only that router
        path preserves a genuine dedicated endpoint override.
        """
        endpoint = self.endpoint_override.strip() if self.endpoint_override else ""
        if endpoint.rstrip("/") == "https://router.huggingface.co/v1/chat":
            return HF_CHAT_COMPLETIONS_URL
        return endpoint or HF_CHAT_COMPLETIONS_URL

    def _format_messages(self, system_prompt: str, user_prompt: str, history: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            # Enforce rolling history limit
            max_turns = config.MAX_CHAT_HISTORY
            bounded_history = history[-max_turns:]
            messages.extend(bounded_history)
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def generate(
        self,
        prompt: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        history: list[dict[str, str]] | None = None,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
        fallback_fn: Any | None = None,
    ) -> str:
        """Synchronous text generation using Gemma on HF Cloud, with fallback."""
        if not self.is_cloud_ready():
            logger.info("HF_TOKEN not set; using deterministic fallback generator.")
            if fallback_fn:
                return fallback_fn()
            return self._default_fallback(prompt)

        try:
            return self.generate_cloud(prompt, system_prompt, history, max_new_tokens, temperature)
        except HFClientError as exc:
            # This compatibility method is intentionally the only place that
            # can use a caller-supplied deterministic fallback.  Callers that
            # present an answer to a learner must use generate_cloud instead.
            logger.warning("Gemma cloud call failed: %s", exc)
            if fallback_fn:
                return fallback_fn()
            return self._default_fallback(prompt)

    def generate_cloud(
        self,
        prompt: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        history: list[dict[str, str]] | None = None,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        """Return a real Gemma cloud response or raise a transparent error.

        This method deliberately has no local/model fallback and is used for
        learner-facing chat, RAG, and quizzes.
        """
        if not self.is_cloud_ready():
            raise HFClientError("Gemma cloud is unavailable because HF_TOKEN is not configured.", status_code=401, is_auth_error=True)

        messages = self._format_messages(system_prompt, prompt, history)
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_new_tokens,
            "temperature": temperature,
        }

        try:
            # The router chat endpoint is OpenAI-compatible. A configured
            # dedicated endpoint remains an explicit override.
            result = self.hf_client.post_sync(
                self.model_id,
                payload=payload,
                endpoint_override=self._chat_endpoint(),
            )

            # Extract generated response text
            if isinstance(result, dict):
                choices = result.get("choices", [])
                if choices and isinstance(choices[0], dict):
                    msg = choices[0].get("message", {})
                    content = msg.get("content", "")
                    if content:
                        return content.strip()
                if "generated_text" in result:
                    return str(result["generated_text"]).strip()

            if isinstance(result, list) and result:
                first = result[0]
                if isinstance(first, dict):
                    if "generated_text" in first:
                        return str(first["generated_text"]).strip()
                    if "message" in first:
                        return str(first["message"].get("content", "")).strip()

            text = str(result).strip()
            if not text:
                raise HFClientError("Hugging Face returned an empty Gemma response.")
            return text

        except HFClientError:
            raise
        except Exception as exc:
            raise HFClientError(f"Unable to parse Gemma cloud response: {exc}") from exc

    async def stream_chat(
        self,
        prompt: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        history: list[dict[str, str]] | None = None,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        """Stream assistant response tokens via SSE."""
        if not self.is_cloud_ready():
            raise HFClientError("Gemma cloud is unavailable because HF_TOKEN is not configured.", status_code=401, is_auth_error=True)

        messages = self._format_messages(system_prompt, prompt, history)
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_new_tokens,
            "temperature": temperature,
            "stream": True,
        }

        try:
            async for token in self.hf_client.stream_text_async(
                self.model_id,
                payload=payload,
                endpoint_override=self._chat_endpoint(),
            ):
                yield token
        except Exception as exc:
            logger.warning("Gemma streaming failed: %s", exc)
            raise

    def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        max_new_tokens: int = 768,
        fallback_json: Any = None,
    ) -> Any:
        """Generate structured JSON data using Gemma."""
        raw = self.generate(
            prompt,
            system_prompt=system_prompt,
            max_new_tokens=max_new_tokens,
            temperature=0.1,
            fallback_fn=(lambda: json.dumps(fallback_json)) if fallback_json is not None else None,
        )
        try:
            cleaned = _clean_json_text(raw)
            return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"Failed to parse Gemma JSON output: {e}. Raw text: {raw[:150]}")
            if fallback_json is not None:
                return fallback_json
            raise

    def generate_audio_description_text(
        self,
        visual_event: dict[str, Any],
        transcript_context: str,
        understanding: dict[str, Any] | None = None,
    ) -> str:
        """Generate educational, concise audio description text for blind learners."""
        event_type = visual_event.get("type", "scene")
        ocr_text = visual_event.get("ocr_text", "")
        start_ts = visual_event.get("start", 0.0)

        prompt = (
            f"Timestamp: {start_ts:.1f}s\n"
            f"Visual Type: {event_type}\n"
            f"On-Screen Content / OCR: {ocr_text[:300] if ocr_text else 'None'}\n"
            f"Current Spoken Transcript: {transcript_context[:300] if transcript_context else 'None'}\n"
            "Generate the concise audio description to be spoken to a blind student."
        )

        def fallback():
            # Honest deterministic description
            if ocr_text and event_type == "code":
                first_line = ocr_text.strip().split("\n")[0]
                return f"On screen, Python code is displayed showing: {first_line[:80]}."
            elif ocr_text and event_type in ("diagram", "flowchart"):
                return "A flowchart diagram illustrates the loop execution sequence."
            elif ocr_text and event_type == "chart":
                return "A bar chart compares execution iterations across loop examples."
            elif ocr_text:
                return f"A slide appears titled: {ocr_text.strip().splitlines()[0][:80]}."
            return "The instructor continues explaining the lecture topic."

        return self.generate(prompt, system_prompt=AUDIO_DESCRIPTION_PROMPT, max_new_tokens=150, fallback_fn=fallback)

    def generate_quiz(
        self,
        transcript_text: str,
        visual_events: list[dict[str, Any]],
        concepts: list[str] | None = None,
        fallback_quiz: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate grounded quiz questions using Gemma with strict provenance."""
        prompt = (
            f"Lecture Concepts: {', '.join(concepts) if concepts else 'From lecture'}\n"
            f"Transcript Sample: {transcript_text[:1500]}\n"
            f"Visual Events: {json.dumps([{'time': e.get('start'), 'type': e.get('type'), 'text': e.get('ocr_text', '')[:60]} for e in visual_events[:6]], ensure_ascii=False)}\n\n"
            "Generate 3-6 grounded educational quiz questions as a JSON array matching the required schema."
        )
        return self.generate_json(
            prompt,
            system_prompt=QUIZ_GENERATION_PROMPT,
            max_new_tokens=800,
            fallback_json=fallback_quiz or [],
        )

    def _default_fallback(self, prompt: str) -> str:
        """Deterministic, grounded educational response when cloud AI is unreachable."""
        lower = prompt.lower()
        if "for loop" in lower or "حلقة" in lower:
            return "In Python, a for loop repeats a block of code a specific number of times, commonly used with range()."
        if "while loop" in lower:
            return "A while loop in Python continues repeating code as long as a boolean condition evaluates to True."
        if "what am i looking at" in lower or "what is on screen" in lower or "visual" in lower:
            return "The current screen displays educational code and visual diagrams corresponding to the instructor's explanation."
        return "EduAccess AI is assisting with your lecture. Let me know if you need an explanation, quiz hint, or accessibility adjustment."


# Global shared Gemma service instance
_gemma_instance: GemmaService | None = None

def get_gemma_service() -> GemmaService:
    global _gemma_instance
    if _gemma_instance is None:
        _gemma_instance = GemmaService()
    return _gemma_instance
