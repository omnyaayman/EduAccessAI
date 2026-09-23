"""End-to-End and Unit Tests for Assistant Context Binding & Grounded Q&A.

Validates:
1. Dynamic context normalization (job_id, lecture_id, lectureId, job).
2. "What am I looking at right now?" at specific timestamps with visual + OCR claims.
3. "What was shown but not explained?" gap disparity reasoning.
4. Grounded RAG responses with timestamped evidence.
5. Honest empty context rejection when no lecture exists.
6. Deterministic UI actions (captions, quiz, narration).
"""
import unittest
import json
from unittest.mock import patch, MagicMock

from backend.services.assistant.orchestrator import AssistantOrchestrator, get_assistant_orchestrator
from backend.services.assistant.tools import execute_tool
from backend import storage


class TestAssistantContextEndToEnd(unittest.TestCase):

    def setUp(self):
        self.orchestrator = AssistantOrchestrator()
        self.demo_job_id = "DEMO_python_loops"

    def test_empty_context_rejection(self):
        """When no lecture ID exists, reject content questions honestly."""
        res = self.orchestrator.chat("What is this video about?", context={})
        self.assertIn("Open or process a lecture first", res["reply"])
        self.assertEqual(res["provider"], "none")

    def test_nonexistent_job_id_rejection(self):
        """When an invalid job ID is passed, reject honestly."""
        res = self.orchestrator.chat(
            "What is on screen?",
            context={"lecture_id": "nonexistent_job_xyz_999"}
        )
        self.assertIn("Open or process a lecture first", res["reply"])

    def test_deterministic_actions_work_without_lecture(self):
        """UI actions like captions or quiz work globally."""
        res = self.orchestrator.chat("turn on captions", context={})
        self.assertEqual(res["action"], "toggle_captions")
        self.assertTrue(res["action_payload"]["enabled"])

    def test_context_normalization_keys(self):
        """Verify orchestrator accepts lecture_id, job_id, lectureId, or job."""
        keys = ["lecture_id", "job_id", "lectureId", "job"]
        for key in keys:
            context = {key: self.demo_job_id, "timestamp": 12.0}
            res = self.orchestrator.chat("What am I looking at right now?", context=context)
            self.assertNotIn("Open or process a lecture first", res["reply"])
            self.assertIn("looking at", res["reply"])

    def test_what_am_i_looking_at_visual_event(self):
        """At t=12s in DEMO_python_loops, verify on-screen visual event is returned."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 12.0}
        res = self.orchestrator.chat("What am I looking at right now?", context=context)
        self.assertIn("reply", res)
        self.assertIn("looking at", res["reply"])
        self.assertEqual(len(res["evidence"]), 1)
        self.assertEqual(res["evidence"][0]["time"], "00:12")

    def test_what_am_i_missing_gap_reasoning(self):
        """Verify cross-modal disparity gaps are retrieved."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 10.0}
        res = self.orchestrator.chat("What was shown but not explained?", context=context)
        self.assertIn("reply", res)
        self.assertNotIn("Open or process a lecture first", res["reply"])

    def test_grounded_rag_with_evidence(self):
        """Verify RAG query returns grounded evidence with timestamps."""
        context = {"lecture_id": self.demo_job_id, "timestamp": 5.0}
        with patch.object(
            self.orchestrator.gemma,
            "generate_cloud",
            return_value="A for loop in Python iterates over a sequence citing [00:10]."
        ):
            res = self.orchestrator.chat("What is a for loop in Python?", context=context)
            self.assertIn("reply", res)
            self.assertNotIn("Open or process a lecture first", res["reply"])
            self.assertIsInstance(res.get("evidence"), list)

    def test_stream_chat_empty_context(self):
        """Verify streaming chat rejects empty context with honest token."""
        import asyncio

        async def run_stream():
            tokens = []
            async for chunk_str in self.orchestrator.stream_chat("What is this?", context={}):
                data = json.loads(chunk_str)
                tokens.append(data.get("token", ""))
            return "".join(tokens)

        result = asyncio.run(run_stream())
        self.assertIn("Open or process a lecture first", result)

    def test_stream_chat_with_valid_context(self):
        """Verify streaming chat with valid job streams grounded answer."""
        import asyncio

        async def run_stream():
            tokens = []
            async for chunk_str in self.orchestrator.stream_chat(
                "What am I looking at right now?",
                context={"lecture_id": self.demo_job_id, "timestamp": 10.0}
            ):
                data = json.loads(chunk_str)
                tokens.append(data.get("token", ""))
            return "".join(tokens)

        result = asyncio.run(run_stream())
        self.assertIn("looking at", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
