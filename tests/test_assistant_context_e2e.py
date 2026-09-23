"""End-to-End and Context Lifecycle Tests for EduAccess Global AI Assistant.

Validates the full 18-Scenario Context Lifecycle Test Matrix:
Phase 1: No lecture open -> General AI chatbot (conversational, platform, technical, programming, AI/ML).
Phase 2: Active lecture open -> Grounded lecture context for lecture queries, General AI for general queries.
Phase 3: Navigating away / context cleared -> Returns immediately to General AI without stale demo context.
"""
import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock

from backend.services.assistant.orchestrator import AssistantOrchestrator, get_assistant_orchestrator
from backend.services.assistant.intent import (
    GREETING_REPLY,
    THANKS_REPLY,
    STATUS_REPLY,
    AFFECTION_REPLY,
    JOKE_REPLY,
)
from backend import storage


class TestAssistantContextEndToEnd(unittest.TestCase):

    def setUp(self):
        self.orchestrator = AssistantOrchestrator()
        self.demo_job_id = "DEMO_python_loops"

    # ==================== PHASE 1: NO LECTURE OPEN ====================

    def test_scenario_01_no_lecture_hi(self):
        """1. 'Hi' with no lecture open -> normal greeting."""
        res = self.orchestrator.chat("Hi", context={})
        self.assertEqual(res["reply"], GREETING_REPLY)
        self.assertEqual(res["evidence"], [])
        self.assertNotIn("DEMO_python_loops", res["reply"])

    def test_scenario_02_no_lecture_how_are_you(self):
        """2. 'How are you?' with no lecture open -> normal status reply."""
        res = self.orchestrator.chat("How are you?", context={})
        self.assertEqual(res["reply"], STATUS_REPLY)
        self.assertEqual(res["evidence"], [])

    def test_scenario_03_no_lecture_i_love_you(self):
        """3. 'I love you' with no lecture open -> affectionate response."""
        res = self.orchestrator.chat("I love you ❤️", context={})
        self.assertEqual(res["reply"], AFFECTION_REPLY)
        self.assertEqual(res["evidence"], [])

    def test_scenario_04_no_lecture_thank_you(self):
        """4. 'Thank you' with no lecture open -> gratitude response."""
        res = self.orchestrator.chat("Thank you very much", context={})
        self.assertEqual(res["reply"], THANKS_REPLY)
        self.assertEqual(res["evidence"], [])

    def test_scenario_05_no_lecture_what_can_you_do(self):
        """5. 'What can you do?' with no lecture open -> platform explanation."""
        res = self.orchestrator.chat("What can you do?", context={})
        self.assertIn("EduAccess AI Assistant", res["reply"])
        self.assertEqual(res["evidence"], [])

    def test_scenario_06_no_lecture_what_is_python(self):
        """6. 'What is Python?' with no lecture open -> General AI answer."""
        with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="Python is a versatile high-level programming language."):
            res = self.orchestrator.chat("What is Python?", context={})
            self.assertNotIn("Open or process a lecture first", res["reply"])
            self.assertNotIn("DEMO_python_loops", res["reply"])
            self.assertIn("Python", res["reply"])
            self.assertEqual(res["evidence"], [])

    def test_scenario_07_no_lecture_what_is_machine_learning(self):
        """7. 'What is machine learning?' with no lecture open -> General AI answer."""
        with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="Machine learning is a subset of AI where algorithms learn from data."):
            res = self.orchestrator.chat("What is machine learning?", context={})
            self.assertNotIn("Open or process a lecture first", res["reply"])
            self.assertIn("Machine learning", res["reply"])
            self.assertEqual(res["evidence"], [])

    def test_scenario_08_no_lecture_explain_recursion(self):
        """8. 'Explain recursion simply' with no lecture open -> General AI answer."""
        with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="Recursion is a programming technique where a function calls itself."):
            res = self.orchestrator.chat("Explain recursion simply", context={})
            self.assertNotIn("Open or process a lecture first", res["reply"])
            self.assertIn("Recursion", res["reply"])
            self.assertEqual(res["evidence"], [])

    def test_scenario_09_no_lecture_what_is_sql(self):
        """9. 'What is SQL?' with no lecture open -> General AI answer."""
        with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="SQL is a standard language for storing and querying relational databases."):
            res = self.orchestrator.chat("What is SQL?", context={})
            self.assertNotIn("Open or process a lecture first", res["reply"])
            self.assertIn("SQL", res["reply"])
            self.assertEqual(res["evidence"], [])

    # ==================== PHASE 2: ACTIVE LECTURE OPEN ====================

    def test_scenario_10_active_lecture_explain_section(self):
        """10. 'Explain this section.' inside active lecture -> Grounded lecture answer with retriever called."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 12.0}
        with patch("backend.services.assistant.orchestrator.get_retriever") as mock_get_retriever:
            mock_retriever_inst = MagicMock()
            mock_retriever_inst.retrieve.return_value = [{"timestamp_label": "00:10", "text": "for i in range(5):"}]
            mock_get_retriever.return_value = mock_retriever_inst

            with patch.object(
                self.orchestrator.gemma,
                "generate_cloud",
                return_value="The instructor demonstrates a for loop iterating over range(5) citing [00:10]."
            ):
                res = self.orchestrator.chat("Explain this section", context=context)
                mock_get_retriever.assert_called_once()
                self.assertEqual(res["provider"], "huggingface/gemma")
                self.assertIn("range(5)", res["reply"])
                self.assertTrue(len(res["evidence"]) > 0)

    def test_scenario_11_active_lecture_teacher_explanation(self):
        """11. 'What did the teacher just explain?' inside active lecture -> Grounded answer with retriever called."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 10.0}
        with patch("backend.services.assistant.orchestrator.get_retriever") as mock_get_retriever:
            mock_retriever_inst = MagicMock()
            mock_retriever_inst.retrieve.return_value = [{"timestamp_label": "00:10", "text": "The loop executes step by step."}]
            mock_get_retriever.return_value = mock_retriever_inst

            with patch.object(
                self.orchestrator.gemma,
                "generate_cloud",
                return_value="At [00:10], the teacher explained how the for loop header syntax works."
            ):
                res = self.orchestrator.chat("What did the teacher just explain?", context=context)
                mock_get_retriever.assert_called_once()
                self.assertEqual(res["provider"], "huggingface/gemma")
                self.assertTrue(len(res["evidence"]) > 0)

    def test_scenario_12_active_lecture_what_am_i_looking_at(self):
        """12. Current visual questions use the active lecture's grounded evidence."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 12.0}
        with patch("backend.services.assistant.orchestrator.get_retriever") as get_retriever:
            retriever = MagicMock()
            retriever.retrieve.return_value = [{"timestamp_label": "00:12", "text": "for i in range(5):"}]
            get_retriever.return_value = retriever
            with patch("backend.services.assistant.orchestrator.execute_tool", side_effect=[
                {"text": "The teacher demonstrates a loop."},
                {"type": "code", "description": "A Python loop is visible.", "ocr_text": "for i in range(5):"},
            ]):
                with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="A Python loop is visible at [00:12]."):
                    res = self.orchestrator.chat("What am I looking at right now?", context=context)
        get_retriever.assert_called_once()
        self.assertIn("Python loop", res["reply"])
        self.assertTrue(res["evidence"])

    def test_scenario_13_active_lecture_what_was_shown_not_explained(self):
        """13. 'What was shown but not explained?' inside active lecture -> Accessibility disparity."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 10.0}
        res = self.orchestrator.chat("What was shown but not explained?", context=context)
        self.assertEqual(res["provider"], "gap_reasoning")
        self.assertIn("Accessibility Disparity Gap", res["reply"])
        self.assertTrue(len(res["evidence"]) > 0)

    def test_scenario_14_active_lecture_general_i_love_you(self):
        """14. 'I love you' while lecture is active -> General conversational (NO RAG)."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 12.0}
        with patch("backend.services.assistant.orchestrator.get_retriever") as mock_rag:
            res = self.orchestrator.chat("I love you", context=context)
            mock_rag.assert_not_called()
            self.assertEqual(res["reply"], AFFECTION_REPLY)
            self.assertEqual(res["evidence"], [])

    def test_scenario_15_active_lecture_general_what_is_sql(self):
        """15. 'What is SQL?' while lecture is active (Python loops) -> General AI answer (NO RAG failure)."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 12.0}
        with patch("backend.services.assistant.orchestrator.get_retriever") as mock_rag:
            with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="SQL is a database query language."):
                res = self.orchestrator.chat("What is SQL?", context=context)
                mock_rag.assert_not_called()
                self.assertNotIn("Open or process a lecture first", res["reply"])
                self.assertIn("SQL", res["reply"])
                self.assertEqual(res["evidence"], [])

    def test_scenario_16_active_lecture_general_tell_me_a_joke(self):
        """16. 'Tell me a joke' while lecture is active -> General AI joke (NO RAG)."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 12.0}
        with patch("backend.services.assistant.orchestrator.get_retriever") as mock_rag:
            res = self.orchestrator.chat("Tell me a joke", context=context)
            mock_rag.assert_not_called()
            self.assertEqual(res["reply"], JOKE_REPLY)
            self.assertEqual(res["evidence"], [])

    def test_scenario_17_active_lecture_general_how_are_you(self):
        """17. 'How are you?' while lecture is active -> General conversational status (NO RAG)."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 12.0}
        with patch("backend.services.assistant.orchestrator.get_retriever") as mock_rag:
            res = self.orchestrator.chat("How are you?", context=context)
            mock_rag.assert_not_called()
            self.assertEqual(res["reply"], STATUS_REPLY)
            self.assertEqual(res["evidence"], [])

    def test_rag_explicit_avoidance_matrix_with_active_lecture(self):
        """Assert retriever is NOT called for: 'I love you', 'Thank you', 'How are you?', 'Tell me a joke', 'What is SQL?', 'What is Python?'."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 5.0}
        general_queries = [
            "I love you",
            "Thank you",
            "How are you?",
            "Tell me a joke",
            "What is SQL?",
            "What is Python?",
        ]
        with patch("backend.services.assistant.orchestrator.get_retriever") as mock_rag:
            with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="General AI educational answer."):
                for q in general_queries:
                    res = self.orchestrator.chat(q, context=context)
                    mock_rag.assert_not_called()
                    self.assertEqual(res["evidence"], [], f"Expected evidence: [] for '{q}'")

    def test_rag_explicit_invocation_matrix_with_active_lecture(self):
        """Assert retriever IS called for: 'Explain this section', 'What did the teacher just explain?', 'What is shown on this slide?'."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 5.0}
        lecture_queries = [
            "Explain this section",
            "What did the teacher just explain?",
            "What is shown on this slide?",
        ]
        for q in lecture_queries:
            with patch("backend.services.assistant.orchestrator.get_retriever") as mock_rag:
                mock_inst = MagicMock()
                mock_inst.retrieve.return_value = [{"timestamp_label": "00:05", "text": "lecture snippet"}]
                mock_rag.return_value = mock_inst
                with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="Grounded answer citing [00:05]."):
                    res = self.orchestrator.chat(q, context=context)
                    mock_rag.assert_called_once()
                    self.assertEqual(res["provider"], "huggingface/gemma")

    # ==================== PHASE 3: LEAVING / CLOSING LECTURE ====================

    def test_scenario_18_navigate_away_what_is_a_for_loop(self):
        """18. Close/navigate away (context={}) and ask 'What is a for loop?' -> General AI answer without stale lecture context."""
        with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="A for loop repeats a block of code over a sequence."):
            res = self.orchestrator.chat("What is a for loop?", context={})
            self.assertNotIn("Open or process a lecture first", res["reply"])
            self.assertNotIn("DEMO_python_loops", res["reply"])
            self.assertIn("for loop", res["reply"])
            self.assertEqual(res["evidence"], [])

    def test_deterministic_actions_work_globally(self):
        """UI actions like captions or font sizing work anywhere."""
        res = self.orchestrator.chat("turn on captions", context={})
        self.assertEqual(res["action"], "toggle_captions")
        self.assertTrue(res["action_payload"]["enabled"])

    def test_streaming_chat_mode_switch(self):
        """Streaming chat correctly switches between general mode and lecture mode."""
        # 1. General streaming
        async def mock_gen_stream(*args, **kwargs):
            for token in ["SQL ", "is ", "a ", "database ", "language."]:
                yield token

        with patch.object(self.orchestrator.gemma, "stream_chat", side_effect=mock_gen_stream):
            async def run_general_stream():
                tokens = []
                async for chunk_str in self.orchestrator.stream_chat("What is SQL?", context={}):
                    data = json.loads(chunk_str)
                    tokens.append(data.get("token", ""))
                return "".join(tokens)

            gen_out = asyncio.run(run_general_stream())
            self.assertNotIn("Open or process a lecture first", gen_out)
            self.assertEqual(gen_out.strip(), "SQL is a database language.")

        # 2. A lecture-specific stream carries retrieved evidence metadata.
        async def mock_lecture_stream(*args, **kwargs):
            yield "Grounded lecture answer."

        with patch("backend.services.assistant.orchestrator.get_retriever") as get_retriever:
            retriever = MagicMock()
            retriever.retrieve.return_value = [{"timestamp_label": "00:12", "text": "loop evidence"}]
            get_retriever.return_value = retriever
            with patch("backend.services.assistant.orchestrator.execute_tool", side_effect=[{"text": "speech"}, {"type": "code", "description": "loop", "ocr_text": "for"}]):
                with patch.object(self.orchestrator.gemma, "stream_chat", side_effect=mock_lecture_stream):
                    async def run_lecture_stream():
                        return [json.loads(chunk) async for chunk in self.orchestrator.stream_chat(
                            "What am I looking at right now?",
                            context={"lecture_id": self.demo_job_id, "timestamp": 12.0},
                        )]
                    lecture_events = asyncio.run(run_lecture_stream())
        self.assertTrue(any(event.get("evidence") for event in lecture_events))

    def test_general_semantic_categories_never_call_rag_with_active_job(self):
        context = {"lecture_id": self.demo_job_id, "timestamp": 42.0}
        general_queries = (
            "I love you ❤️", "I'm hungry", "I'm tired", "I'm bored", "I'm a snake",
            "Tell me a joke", "How are you?", "Thank you", "What is Python?",
            "What is SQL?", "Explain machine learning", "Explain EduAccess",
            "What is EduAccess?", "Tell me about this platform", "What can you do?",
            "Who are you?", "Can you help me?",
        )

        async def fake_stream(*args, **kwargs):
            yield "General answer."

        with patch("backend.services.assistant.orchestrator.get_retriever") as get_retriever:
            with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="General answer."):
                with patch.object(self.orchestrator.gemma, "stream_chat", side_effect=fake_stream):
                    for query in general_queries:
                        with self.subTest(mode="chat", query=query):
                            result = self.orchestrator.chat(query, context=context)
                            self.assertEqual(result["evidence"], [])
                            self.assertNotIn("DEMO_python_loops", result["reply"])
                            self.assertNotRegex(result["reply"], r"\[\d{2}:\d{2}\]")
                        with self.subTest(mode="stream", query=query):
                            async def collect():
                                return [json.loads(item) async for item in self.orchestrator.stream_chat(query, context=context)]
                            events = asyncio.run(collect())
                            self.assertFalse(any(event.get("evidence") for event in events))
                            self.assertNotIn("DEMO_python_loops", "".join(e.get("token", "") for e in events))
            get_retriever.assert_not_called()

    def test_semantic_lecture_variants_use_rag_in_chat_and_stream(self):
        context = {"lecture_id": self.demo_job_id, "timestamp": 18.0}
        lecture_queries = (
            "Explain this section",
            "What did the teacher just explain?",
            "What is on this slide?",
            "What did the teacher show?",
            "What's happening in the current video?",
            "Can you describe what is displayed on the current screen?",
        )

        async def fake_stream(*args, **kwargs):
            yield "Grounded answer."

        for query in lecture_queries:
            with self.subTest(query=query):
                with patch("backend.services.assistant.orchestrator.get_retriever") as get_retriever:
                    retriever = MagicMock()
                    retriever.retrieve.return_value = [{"timestamp_label": "00:18", "text": "Verified lecture evidence."}]
                    get_retriever.return_value = retriever
                    with patch("backend.services.assistant.orchestrator.execute_tool", side_effect=[
                        {"text": "Current instructor speech."},
                        {"type": "slide", "description": "A diagram is shown.", "ocr_text": "loop"},
                    ] * 2):
                        with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="Grounded answer [00:18]."):
                            chat_result = self.orchestrator.chat(query, context=context)
                        with patch.object(self.orchestrator.gemma, "stream_chat", side_effect=fake_stream):
                            async def collect():
                                return [json.loads(item) async for item in self.orchestrator.stream_chat(query, context=context)]
                            events = asyncio.run(collect())
                    self.assertEqual(get_retriever.call_count, 2)
                    self.assertTrue(chat_result["evidence"])
                    self.assertTrue(any(event.get("evidence") for event in events))


if __name__ == "__main__":
    unittest.main(verbosity=2)
