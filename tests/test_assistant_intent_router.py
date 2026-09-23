"""Comprehensive Unit & Regression Tests for Assistant Intent Router.

Tests all intent categories:
1. CONVERSATIONAL ("Hi", "Hello", "Thanks", "How are you?")
2. PLATFORM ("Who are you?", "What can you do?", "What is EduAccess?")
3. CURRENT_VISUAL ("What am I looking at right now?")
4. ACCESSIBILITY ("What was shown but not explained?")
5. LEARNING_HELP ("I don't understand this.", "Explain this simply.")
6. QUIZ ("Quiz me.", "Test me on this lecture.")
7. LEARNING_PROGRESS ("What should I study next?", "What am I weak at?")
8. CLARIFICATION ("Tell me more.")
9. LECTURE_CONTENT ("What is this code doing?", "Explain the for loop.")
10. DETERMINISTIC_ACTION ("turn on captions", "increase font")
"""
import asyncio
import json
import unittest

from backend.services.assistant.intent import (
    AssistantIntent,
    classify_intent,
    GREETING_REPLY,
    THANKS_REPLY,
    STATUS_REPLY,
    PLATFORM_EXPLANATION,
    CLARIFICATION_REPLY,
)
from backend.services.assistant.orchestrator import AssistantOrchestrator


class TestAssistantIntentRouter(unittest.TestCase):

    def setUp(self):
        self.orchestrator = AssistantOrchestrator()
        self.demo_job = "DEMO_python_loops"

    # ==================== 1. INTENT CLASSIFICATION UNIT TESTS ====================

    def test_intent_classification_conversational_greetings(self):
        greetings = ["Hi", "Hello", "Hey", "Hi there", "Good morning", "good evening", "مرحبا", "اهلا"]
        for g in greetings:
            res = classify_intent(g)
            self.assertEqual(
                res.intent,
                AssistantIntent.CONVERSATIONAL,
                f"Failed for greeting '{g}': got {res.intent}",
            )
            self.assertEqual(res.sub_type, "greeting")
            self.assertIn("EduAccess Assistant", res.direct_reply)

    def test_intent_classification_conversational_gratitude(self):
        thanks = ["Thanks", "Thank you", "Thanks a lot", "thank you so much", "ty", "شكرا"]
        for t in thanks:
            res = classify_intent(t)
            self.assertEqual(
                res.intent,
                AssistantIntent.CONVERSATIONAL,
                f"Failed for thanks '{t}': got {res.intent}",
            )
            self.assertEqual(res.sub_type, "gratitude")
            self.assertIn("You're welcome", res.direct_reply)

    def test_intent_classification_conversational_status(self):
        statuses = ["How are you?", "How are you doing", "what's up", "كيف حالك"]
        for s in statuses:
            res = classify_intent(s)
            self.assertEqual(
                res.intent,
                AssistantIntent.CONVERSATIONAL,
                f"Failed for status '{s}': got {res.intent}",
            )
            self.assertEqual(res.sub_type, "status")
            self.assertIn("doing great", res.direct_reply)

    def test_intent_classification_platform(self):
        platform_queries = ["Who are you?", "What can you do?", "What is EduAccess?", "How does this platform work?", "من انت"]
        for q in platform_queries:
            res = classify_intent(q)
            self.assertEqual(
                res.intent,
                AssistantIntent.PLATFORM,
                f"Failed for platform query '{q}': got {res.intent}",
            )
            self.assertIn("EduAccess AI Assistant", res.direct_reply)

    def test_intent_classification_current_visual(self):
        queries = ["What am I looking at right now?", "What is on the screen?", "Describe this slide", "What code is shown?"]
        for q in queries:
            res = classify_intent(q)
            self.assertEqual(
                res.intent,
                AssistantIntent.CURRENT_VISUAL,
                f"Failed for visual query '{q}': got {res.intent}",
            )

    def test_intent_classification_accessibility(self):
        queries = ["What was shown but not explained?", "What am I missing?", "What did I miss?", "What important visual information wasn't explained?"]
        for q in queries:
            res = classify_intent(q)
            self.assertEqual(
                res.intent,
                AssistantIntent.ACCESSIBILITY,
                f"Failed for accessibility query '{q}': got {res.intent}",
            )

    def test_intent_classification_learning_help(self):
        queries = ["I don't understand this.", "Explain it simply.", "Can you explain this like I'm a beginner?", "Give me an example.", "Simplify this"]
        for q in queries:
            res = classify_intent(q)
            self.assertEqual(
                res.intent,
                AssistantIntent.LEARNING_HELP,
                f"Failed for learning help query '{q}': got {res.intent}",
            )

    def test_intent_classification_quiz(self):
        queries = ["Quiz me.", "Test me on this lecture.", "Give me 5 questions.", "Practice this topic with me."]
        for q in queries:
            res = classify_intent(q)
            self.assertEqual(
                res.intent,
                AssistantIntent.QUIZ,
                f"Failed for quiz query '{q}': got {res.intent}",
            )

    def test_intent_classification_learning_progress(self):
        queries = ["What should I study next?", "What should I do next?", "What am I weak at?", "How can I improve?", "What's my next step?"]
        for q in queries:
            res = classify_intent(q)
            self.assertEqual(
                res.intent,
                AssistantIntent.LEARNING_PROGRESS,
                f"Failed for progress query '{q}': got {res.intent}",
            )

    def test_intent_classification_clarification(self):
        queries = ["Tell me more.", "More", "Continue", "Elaborate"]
        for q in queries:
            res = classify_intent(q)
            self.assertEqual(
                res.intent,
                AssistantIntent.CLARIFICATION,
                f"Failed for clarification query '{q}': got {res.intent}",
            )

    def test_intent_classification_lecture_content(self):
        queries = ["What is this code doing?", "Explain the for loop.", "What does range(5) do?", "Summarize this lecture."]
        for q in queries:
            res = classify_intent(q)
            self.assertEqual(
                res.intent,
                AssistantIntent.LECTURE_CONTENT,
                f"Failed for lecture content query '{q}': got {res.intent}",
            )

    def test_intent_classification_deterministic_actions(self):
        actions = [
            ("turn on captions", "toggle_captions"),
            ("turn off captions", "toggle_captions"),
            ("turn on audio description", "toggle_audio_description"),
            ("increase font", "font_size"),
            ("decrease font", "font_size"),
        ]
        for query, expected_action in actions:
            res = classify_intent(query)
            self.assertEqual(res.intent, AssistantIntent.DETERMINISTIC_ACTION)
            self.assertEqual(res.action, expected_action)

    # ==================== 2. ORCHESTRATOR END-TO-END BEHAVIOR ====================

    def test_conversational_without_lecture_context(self):
        """Conversational queries should work without lecture context and NOT trigger rejection or RAG."""
        res_hi = self.orchestrator.chat("Hi", context={})
        self.assertEqual(res_hi["reply"], GREETING_REPLY)
        self.assertEqual(res_hi["provider"], "intent_router")
        self.assertEqual(res_hi["evidence"], [])

        res_thanks = self.orchestrator.chat("Thanks", context={})
        self.assertEqual(res_thanks["reply"], THANKS_REPLY)
        self.assertEqual(res_thanks["provider"], "intent_router")

        res_status = self.orchestrator.chat("How are you?", context={})
        self.assertEqual(res_status["reply"], STATUS_REPLY)
        self.assertEqual(res_status["provider"], "intent_router")

    def test_conversational_with_active_lecture_context(self):
        """Conversational queries inside a lecture MUST NOT trigger lecture RAG or lecture summaries."""
        context = {"lecture_id": self.demo_job, "timestamp": 12.0}

        res_hi = self.orchestrator.chat("Hi", context=context)
        self.assertEqual(res_hi["reply"], GREETING_REPLY)
        self.assertEqual(res_hi["provider"], "intent_router")
        self.assertEqual(res_hi["evidence"], [])
        self.assertNotIn("Python", res_hi["reply"])
        self.assertNotIn("loop", res_hi["reply"])

        res_thanks = self.orchestrator.chat("Thank you so much", context=context)
        self.assertEqual(res_thanks["reply"], THANKS_REPLY)
        self.assertEqual(res_thanks["provider"], "intent_router")
        self.assertEqual(res_thanks["evidence"], [])

    def test_platform_intent_with_and_without_lecture(self):
        """Platform intent provides accurate capability overview without lecture RAG."""
        for ctx in [{}, {"lecture_id": self.demo_job, "timestamp": 5.0}]:
            res = self.orchestrator.chat("What can you do?", context=ctx)
            self.assertIn("EduAccess AI Assistant", res["reply"])
            self.assertIn("Live On-Screen Visuals", res["reply"])
            self.assertIn("Accessibility & Gap Analysis", res["reply"])
            self.assertEqual(res["provider"], "intent_router")
            self.assertEqual(res["evidence"], [])

    def test_clarification_intent_natural_followup(self):
        """Clarification intent prompts user gracefully without firing RAG."""
        res = self.orchestrator.chat("Tell me more.", context={"lecture_id": self.demo_job})
        self.assertEqual(res["reply"], CLARIFICATION_REPLY)
        self.assertEqual(res["provider"], "intent_router")
        self.assertEqual(res["evidence"], [])

    def test_current_visual_grounded_telemetry(self):
        """'What am I looking at right now?' returns grounded visual + OCR data with timestamp."""
        context = {"lecture_id": self.demo_job, "timestamp": 12.0}
        res = self.orchestrator.chat("What am I looking at right now?", context=context)
        self.assertEqual(res["provider"], "visual_telemetry")
        self.assertIn("looking at", res["reply"])
        self.assertEqual(len(res["evidence"]), 1)
        self.assertEqual(res["evidence"][0]["time"], "00:12")

    def test_accessibility_disparity_gap(self):
        """'What was shown but not explained?' returns real cross-modal disparity reasoning."""
        context = {"lecture_id": self.demo_job, "timestamp": 10.0}
        res = self.orchestrator.chat("What was shown but not explained?", context=context)
        self.assertEqual(res["provider"], "gap_reasoning")
        self.assertIn("Accessibility Disparity Gap", res["reply"])
        self.assertTrue(len(res["evidence"]) > 0)

    def test_lecture_content_grounded_rag(self):
        """Lecture content question ('What is this code doing?') uses grounded RAG with timestamps."""
        context = {"lecture_id": self.demo_job, "timestamp": 12.0}
        with unittest.mock.patch.object(
            self.orchestrator.gemma,
            "generate_cloud",
            return_value="In Python, this loop repeats 5 times from 0 to 4 citing [00:10]."
        ):
            res = self.orchestrator.chat("What is this code doing?", context=context)
            self.assertEqual(res["provider"], "huggingface/gemma")
            self.assertIn("repeats 5 times", res["reply"])
            self.assertTrue(len(res["evidence"]) > 0)

    def test_lecture_content_grounded_fallback_when_offline(self):
        """When cloud AI is offline, fallback provides grounded transcript and chunk evidence."""
        context = {"lecture_id": self.demo_job, "timestamp": 12.0}
        with unittest.mock.patch.object(
            self.orchestrator.gemma,
            "generate_cloud",
            side_effect=Exception("Connection timeout")
        ):
            res = self.orchestrator.chat("What is this code doing?", context=context)
            self.assertEqual(res["provider"], "grounded_evidence")
            self.assertIn("Based on the lecture at", res["reply"])
            self.assertTrue(len(res["evidence"]) > 0)

    def test_streaming_conversational(self):
        """SSE streaming correctly delivers conversational greetings token-by-token."""
        async def run_stream():
            tokens = []
            async for chunk_str in self.orchestrator.stream_chat("Hi", context={"lecture_id": self.demo_job}):
                data = json.loads(chunk_str)
                tokens.append(data.get("token", ""))
            return "".join(tokens)

        result = asyncio.run(run_stream())
        self.assertEqual(result.strip(), GREETING_REPLY.strip())

    def test_streaming_platform(self):
        """SSE streaming correctly delivers platform capabilities."""
        async def run_stream():
            tokens = []
            async for chunk_str in self.orchestrator.stream_chat("Who are you?", context={}):
                data = json.loads(chunk_str)
                tokens.append(data.get("token", ""))
            return "".join(tokens)

        result = asyncio.run(run_stream())
        self.assertIn("EduAccess AI Assistant", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
