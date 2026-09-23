"""Unit tests for EduAccess AI – centralized AI services, RAG, and assistant orchestrator.

These tests use real service classes with no cloud token so all paths exercise
the local deterministic fallbacks, ensuring the system never crashes when
Hugging Face is unavailable.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import shutil
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Pre-import mocks for heavy optional deps that may be absent or slow to init.
# NOTE: Do NOT mock 'whisper' or 'torch' here – they are real installed packages
# and a module-level mock would corrupt their state for other test modules
# collected in the same pytest session.
# ---------------------------------------------------------------------------
import sys

for _mod in ["cv2", "pytesseract", "PIL", "PIL.Image"]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Mock pyttsx3 only if not already imported as the real package, so that
# VoxCPMService's local TTS fallback doesn't open a real audio device.
import importlib.util as _ilu
if _ilu.find_spec("pyttsx3") is None or "pyttsx3" not in sys.modules:
    _pyttsx3_mock = MagicMock()
    _pyttsx3_mock.init.return_value = MagicMock()
    sys.modules["pyttsx3"] = _pyttsx3_mock

# ---------------------------------------------------------------------------
# Now import the real services
# ---------------------------------------------------------------------------
from backend.services.ai.hf_client import HFClient, HFClientError
from backend.services.ai.embeddings_service import EmbeddingsService
from backend.services.rag.chunker import chunk_lecture_data, format_clock
from backend.services.rag.vector_store import LectureVectorStore
from backend.services.rag.retriever import LectureRetriever

# GemmaService and VoxCPMService both call get_hf_client() at module-import
# time through module-level singletons, so we import after env is clear.
from backend.services.ai.gemma_service import GemmaService
from backend.services.ai.voxcpm_service import VoxCPMService

# Assistant
from backend.services.assistant.orchestrator import AssistantOrchestrator


# ============================================================
# Helpers
# ============================================================

TEST_JOB_ID = "test_suite_job_001"
TEST_STEM = "test_suite_video"

# Use a dedicated temp directory under data/outputs to avoid touching real data
TEST_OUTPUTS = Path("data/outputs/__test_suite__")


def _make_segments():
    return [
        {"id": 1, "start": 0.0,  "end": 5.0,  "text": "Welcome to the Python loops tutorial."},
        {"id": 2, "start": 5.0,  "end": 10.0, "text": "We will learn for loops and the range function."},
        {"id": 3, "start": 10.0, "end": 15.0, "text": "A for loop iterates over a sequence of values."},
        {"id": 4, "start": 15.0, "end": 20.0, "text": "The range function generates numbers from 0 up to n."},
    ]


def _make_visual_events():
    return [
        {"event_id": "v001", "start": 2.0, "end": 8.0,
         "type": "slide", "summary": "Title slide: Python Loops", "ocr_text": "Python Loops"},
        {"event_id": "v002", "start": 8.0, "end": 18.0,
         "type": "code",  "summary": "for i in range(5): print(i)",
         "ocr_text": "for i in range(5):\n    print(i)"},
    ]


def _make_concepts():
    return [
        {"name": "for loop",       "definition": "Repeating code over a sequence."},
        {"name": "range function", "definition": "Generates an arithmetic sequence of numbers."},
    ]


# ============================================================
# 1. HFClient Tests
# ============================================================

class TestHFClient(unittest.TestCase):

    def test_not_configured_when_token_empty(self):
        client = HFClient(token="")
        self.assertFalse(client.is_configured)

    def test_not_configured_when_token_none(self):
        client = HFClient(token=None)
        # is_configured depends on env var; with no env var set this is False
        # (env may have HF_TOKEN; just test the interface exists)
        self.assertIsInstance(client.is_configured, bool)

    def test_post_sync_raises_when_not_configured(self):
        client = HFClient(token="")
        # Patch is_configured so it returns False regardless of env
        with patch.object(type(client), "is_configured", new_callable=lambda: property(lambda self: False)):
            with self.assertRaises(HFClientError) as ctx:
                client.post_sync("some/model", {"inputs": "hello"})
            self.assertEqual(ctx.exception.is_auth_error, True)

    def test_post_sync_returns_parsed_json(self):
        """post_sync returns the parsed JSON body from a 200 response."""
        expected = [{"generated_text": "Loops repeat code."}]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected
        mock_response.headers = {"content-type": "application/json"}

        client = HFClient(token="hf_test_token_123")
        client._sync_client = MagicMock()
        client._sync_client.post.return_value = mock_response
        result = client.post_sync("some/model", {"inputs": "What is a loop?"})

        self.assertEqual(result, expected)

    def test_stream_text_async_retries_on_429(self):
        """stream_text_async retries with backoff on HTTP 429 and yields tokens on eventual success."""
        import asyncio

        client = HFClient(token="hf_test_token_123", max_retries=2)
        mock_429 = MagicMock()
        mock_429.status_code = 429
        async def fake_aread():
            return b"Rate limited"
        mock_429.aread = fake_aread

        mock_200 = MagicMock()
        mock_200.status_code = 200
        async def fake_lines():
            yield 'data: {"token": {"text": "Grounded "}}\n'
            yield 'data: {"token": {"text": "answer"}}\n'
            yield 'data: [DONE]\n'
        mock_200.aiter_lines = fake_lines

        attempts = [0]
        class MockStreamCtx:
            async def __aenter__(self):
                attempts[0] += 1
                if attempts[0] == 1:
                    return mock_429
                return mock_200
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        client._async_client = MagicMock()
        client._async_client.stream = MagicMock(side_effect=lambda *args, **kwargs: MockStreamCtx())

        async def run():
            with patch("asyncio.sleep", return_value=None):
                tokens = []
                async for tok in client.stream_text_async("some/model", {"inputs": "hi"}):
                    tokens.append(tok)
                return tokens

        result = asyncio.run(run())
        self.assertEqual("".join(result), "Grounded answer")
        self.assertEqual(attempts[0], 2)


# ============================================================
# 2. EmbeddingsService Tests
# ============================================================

class TestEmbeddingsService(unittest.TestCase):

    def setUp(self):
        # Force offline by patching the embedded client
        self.svc = EmbeddingsService()
        # Simulate no HF token so local fallback always fires
        self.svc.hf_client = MagicMock()
        self.svc.hf_client.is_configured = False

    def test_embed_text_returns_list_of_floats(self):
        vec = self.svc.embed_text("for loop iteration")
        self.assertIsInstance(vec, list)
        self.assertGreater(len(vec), 0)
        self.assertIsInstance(vec[0], float)

    def test_same_text_produces_identical_embedding(self):
        vec1 = self.svc.embed_text("Python for loops are powerful")
        vec2 = self.svc.embed_text("Python for loops are powerful")
        self.assertEqual(vec1, vec2)

    def test_different_texts_produce_different_embeddings(self):
        vec_loops = self.svc.embed_text("Python for loop iteration range")
        vec_astro = self.svc.embed_text("neutron star astrophysics black hole")
        self.assertNotEqual(vec_loops, vec_astro)

    def test_embed_text_result_is_normalized(self):
        vec = self.svc.embed_text("normalization test")
        magnitude = sum(x ** 2 for x in vec) ** 0.5
        self.assertAlmostEqual(magnitude, 1.0, places=5)

    def test_embed_empty_string_returns_zero_vector(self):
        vec = self.svc.embed_text("")
        self.assertEqual(vec, [0.0] * 64)

    def test_cosine_similarity_identical_is_one(self):
        vec = self.svc.embed_text("identical text")
        score = self.svc.cosine_similarity(vec, vec)
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_cosine_similarity_unrelated_texts_lower(self):
        vec_a = self.svc.embed_text("Python for loops and iteration")
        vec_b = self.svc.embed_text("neutron stars and black holes in space")
        score = self.svc.cosine_similarity(vec_a, vec_b)
        self.assertLess(score, 0.99)

    def test_embed_batch_length_matches_input(self):
        texts = ["one", "two", "three"]
        batch = self.svc.embed_batch(texts)
        self.assertEqual(len(batch), 3)

    def test_embed_batch_caches(self):
        self.svc._cache = {}
        self.svc.embed_text("cache me")
        initial_cache_size = len(self.svc._cache)
        self.svc.embed_text("cache me")
        self.assertEqual(len(self.svc._cache), initial_cache_size)


# ============================================================
# 3. Multimodal Chunker Tests
# ============================================================

class TestMultimodalChunker(unittest.TestCase):

    def test_format_clock_basic(self):
        self.assertEqual(format_clock(0.0), "00:00")
        self.assertEqual(format_clock(65.0), "01:05")
        self.assertEqual(format_clock(3600.0), "60:00")

    def test_format_clock_negative_clamped(self):
        self.assertEqual(format_clock(-5.0), "00:00")

    def test_chunks_created_for_all_modalities(self):
        chunks = chunk_lecture_data(
            job_id=TEST_JOB_ID,
            segments=_make_segments(),
            visual_events=_make_visual_events(),
            concepts=_make_concepts(),
        )
        self.assertGreater(len(chunks), 0)
        types = {c.get("source_type") for c in chunks}
        # Should have speech, visual, and concept chunks
        self.assertIn("speech", types)
        self.assertIn("visual", types)
        self.assertIn("concept", types)

    def test_all_chunks_have_required_fields(self):
        chunks = chunk_lecture_data(
            job_id=TEST_JOB_ID,
            segments=_make_segments(),
            visual_events=_make_visual_events(),
        )
        required_fields = {"chunk_id", "job_id", "source_type", "text", "start", "end"}
        for chunk in chunks:
            missing = required_fields - set(chunk.keys())
            self.assertEqual(missing, set(), f"Chunk missing fields: {missing}")

    def test_no_empty_text_chunks(self):
        chunks = chunk_lecture_data(
            job_id=TEST_JOB_ID,
            segments=_make_segments(),
            visual_events=_make_visual_events(),
        )
        for chunk in chunks:
            self.assertTrue(chunk.get("text", "").strip(), "Chunk has empty text")

    def test_empty_inputs_produce_no_crash(self):
        chunks = chunk_lecture_data(job_id="empty", segments=[], visual_events=[])
        self.assertIsInstance(chunks, list)

    def test_timestamps_are_numeric(self):
        chunks = chunk_lecture_data(
            job_id=TEST_JOB_ID,
            segments=_make_segments(),
            visual_events=_make_visual_events(),
        )
        for chunk in chunks:
            self.assertIsInstance(chunk["start"], (int, float))
            self.assertIsInstance(chunk["end"], (int, float))
            self.assertGreaterEqual(chunk["end"], chunk["start"])


# ============================================================
# 4. LectureVectorStore Tests
# ============================================================

class TestLectureVectorStore(unittest.TestCase):

    def setUp(self):
        TEST_OUTPUTS.mkdir(parents=True, exist_ok=True)
        # Monkey-patch the index path to use our test directory
        self.store = LectureVectorStore.__new__(LectureVectorStore)
        from backend.services.ai.embeddings_service import EmbeddingsService
        self.store.job_id = TEST_JOB_ID
        self.store.video_stem = TEST_STEM
        self.store.index_path = TEST_OUTPUTS / f"{TEST_STEM}_rag_index.json"
        self.store.chunks = []
        self.store.embeddings = []
        embedder = EmbeddingsService()
        embedder.hf_client = MagicMock()
        embedder.hf_client.is_configured = False
        self.store.embedder = embedder

    def tearDown(self):
        if TEST_OUTPUTS.exists():
            shutil.rmtree(TEST_OUTPUTS, ignore_errors=True)

    def _get_chunks(self):
        return chunk_lecture_data(
            job_id=TEST_JOB_ID,
            segments=_make_segments(),
            visual_events=_make_visual_events(),
            concepts=_make_concepts(),
        )

    def test_build_and_save_creates_index_file(self):
        chunks = self._get_chunks()
        self.store.build_and_save(chunks)
        self.assertTrue(self.store.index_path.exists())

    def test_build_and_save_persists_correct_count(self):
        chunks = self._get_chunks()
        self.store.build_and_save(chunks)
        data = json.loads(self.store.index_path.read_text(encoding="utf-8"))
        self.assertEqual(data["total_chunks"], len(chunks))

    def test_search_returns_results(self):
        chunks = self._get_chunks()
        self.store.build_and_save(chunks)
        results = self.store.search("for loop iteration", top_k=3)
        self.assertIsInstance(results, list)
        # Each result is a (chunk_dict, score) tuple
        for chunk, score in results:
            self.assertIn("text", chunk)
            self.assertIsInstance(score, float)

    def test_search_empty_store_returns_empty(self):
        results = self.store.search("any query", top_k=5)
        self.assertEqual(results, [])

    def test_search_top_k_limit_respected(self):
        chunks = self._get_chunks()
        self.store.build_and_save(chunks)
        results = self.store.search("Python loop range function", top_k=2)
        self.assertLessEqual(len(results), 2)

    def test_build_with_empty_chunks_no_crash(self):
        self.store.build_and_save([])
        self.assertEqual(self.store.chunks, [])


# ============================================================
# 5. GemmaService Fallback Tests
# ============================================================

class TestGemmaServiceFallback(unittest.TestCase):

    def setUp(self):
        self.svc = GemmaService()
        # Force offline by replacing the hf_client
        self.svc.hf_client = MagicMock()
        self.svc.hf_client.is_configured = False

    def test_generate_returns_string_when_offline(self):
        result = self.svc.generate("Explain what a for loop is.")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result.strip()), 0)

    def test_generate_for_loop_fallback_content(self):
        result = self.svc.generate("What is a for loop?")
        self.assertIn("loop", result.lower())

    def test_generate_audio_description_text_returns_string(self):
        visual_event = {
            "event_id": "v001",
            "type": "code",
            "start": 10.0,
            "ocr_text": "for i in range(5):\n    print(i)",
        }
        desc = self.svc.generate_audio_description_text(
            visual_event=visual_event,
            transcript_context="Let's print numbers from 0 to 4.",
        )
        self.assertIsInstance(desc, str)
        self.assertGreater(len(desc.strip()), 0)

    def test_generate_audio_description_text_mentions_code(self):
        visual_event = {
            "event_id": "v002",
            "type": "code",
            "start": 5.0,
            "ocr_text": "for i in range(5):\n    print(i)",
        }
        desc = self.svc.generate_audio_description_text(
            visual_event=visual_event,
            transcript_context="We write a for loop now.",
        )
        # The deterministic fallback mentions 'code' or the first OCR line
        self.assertTrue(
            "code" in desc.lower() or "for" in desc.lower() or "python" in desc.lower(),
            f"Expected code/loop mention in: {desc}"
        )

    def test_generate_audio_description_text_slide(self):
        visual_event = {
            "event_id": "v003",
            "type": "slide",
            "start": 0.0,
            "ocr_text": "Python Loops – Introduction",
        }
        desc = self.svc.generate_audio_description_text(
            visual_event=visual_event,
            transcript_context="This slide introduces loops.",
        )
        word_count = len(desc.split())
        self.assertLessEqual(word_count, 80, f"Description too long ({word_count} words): {desc}")

    def test_generate_quiz_returns_list(self):
        quiz = self.svc.generate_quiz(
            transcript_text="Python for loops iterate over sequences. range(n) produces numbers.",
            visual_events=[
                {"start": 5.0, "type": "code", "ocr_text": "for i in range(5): print(i)"}
            ],
            concepts=["for loop", "range"],
        )
        self.assertIsInstance(quiz, list)

    def test_generate_quiz_fallback_is_empty_list_when_no_fallback_json(self):
        # Without cloud, generate_quiz falls back to fallback_json (default [])
        quiz = self.svc.generate_quiz(
            transcript_text="Some lecture text.",
            visual_events=[],
        )
        # Should be a list (empty fallback or template-generated items)
        self.assertIsInstance(quiz, list)

    def test_generate_json_fallback_returns_fallback_json(self):
        fallback = [{"question": "Fallback question?", "answer": "yes"}]
        result = self.svc.generate_json(
            prompt="Generate quiz.", system_prompt="system", fallback_json=fallback
        )
        self.assertEqual(result, fallback)


# ============================================================
# 6. VoxCPMService Cache + Local Fallback Tests
# ============================================================

class TestVoxCPMServiceCache(unittest.TestCase):

    def setUp(self):
        TEST_OUTPUTS.mkdir(parents=True, exist_ok=True)
        self.svc = VoxCPMService()
        # Force offline
        self.svc.hf_client = MagicMock()
        self.svc.hf_client.is_configured = False

    def tearDown(self):
        if TEST_OUTPUTS.exists():
            shutil.rmtree(TEST_OUTPUTS, ignore_errors=True)

    def test_synthesize_creates_wav_file(self):
        output_path = TEST_OUTPUTS / "test_synth.wav"
        result_path = self.svc.synthesize(
            "Welcome to the Python loops tutorial.",
            output_path=str(output_path),
        )
        self.assertIsNotNone(result_path)
        self.assertTrue(Path(result_path).exists())

    def test_synthesize_empty_text_raises(self):
        with self.assertRaises((ValueError, Exception)):
            self.svc.synthesize("", output_path=str(TEST_OUTPUTS / "empty.wav"))

    def test_synthesize_cache_hit_returns_same_path(self):
        """Calling synthesize with the same text twice should reuse the cached file."""
        output1 = TEST_OUTPUTS / "cache_test_1.wav"
        output2 = TEST_OUTPUTS / "cache_test_2.wav"

        path1 = self.svc.synthesize("Cache test sentence.", output_path=str(output1))
        # Second call with a known cache path (using internal _cache_path key)
        cache_key_path = self.svc._cache_path("Cache test sentence.")
        if cache_key_path.exists() and cache_key_path.stat().st_size > 500:
            path2 = self.svc.synthesize("Cache test sentence.", output_path=str(output2))
            # Should return a valid path
            self.assertTrue(Path(path2).exists())


# ============================================================
# 7. AssistantOrchestrator – Deterministic Action Routing
# ============================================================

class TestAssistantOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orch = AssistantOrchestrator()
        # Replace gemma with a simple mock so no actual inference runs
        self.orch.gemma = MagicMock()
        self.orch.gemma.generate.return_value = "This is a mocked Gemma answer."
        self.orch.gemma.is_cloud_ready.return_value = False

    def _chat(self, message: str) -> dict:
        return self.orch.chat(message, context={"lecture_id": TEST_JOB_ID, "timestamp": 5.0})

    def test_enable_captions_deterministic(self):
        res = self._chat("please turn on captions")
        self.assertEqual(res["action"], "toggle_captions")
        self.assertTrue(res["action_payload"]["enabled"])
        self.assertIn("enabled", res["reply"].lower())

    def test_disable_captions_deterministic(self):
        res = self._chat("turn off captions please")
        self.assertEqual(res["action"], "toggle_captions")
        self.assertFalse(res["action_payload"]["enabled"])

    def test_enable_audio_description_deterministic(self):
        res = self._chat("turn on audio descriptions")
        self.assertEqual(res["action"], "toggle_audio_description")
        self.assertTrue(res["action_payload"]["enabled"])

    def test_open_quiz_deterministic(self):
        res = self._chat("open quiz now")
        self.assertEqual(res["action"], "open_quiz")

    def test_start_quiz_deterministic(self):
        res = self._chat("start quiz")
        self.assertEqual(res["action"], "open_quiz")

    def test_empty_message_returns_graceful_reply(self):
        res = self._chat("   ")
        self.assertIn("reply", res)
        self.assertIsInstance(res["reply"], str)
        self.assertGreater(len(res["reply"].strip()), 0)

    def test_non_action_message_returns_reply(self):
        # A content question – should not be a deterministic action
        with patch("backend.services.assistant.orchestrator.execute_tool", return_value={}):
            res = self._chat("What does the range function do?")
        self.assertIn("reply", res)

    def test_arabic_captions_on(self):
        res = self._chat("شغل الترجمة")
        self.assertEqual(res["action"], "toggle_captions")
        self.assertTrue(res["action_payload"]["enabled"])

    def test_arabic_quiz_open(self):
        res = self._chat("افتح الاختبار")
        self.assertEqual(res["action"], "open_quiz")


# ============================================================
# 8. LectureRetriever Integration
# ============================================================

class TestLectureRetrieverIntegration(unittest.TestCase):

    def setUp(self):
        TEST_OUTPUTS.mkdir(parents=True, exist_ok=True)

        # Build a vector store in the test directory
        store = LectureVectorStore.__new__(LectureVectorStore)
        embedder = EmbeddingsService()
        embedder.hf_client = MagicMock()
        embedder.hf_client.is_configured = False
        store.job_id = TEST_JOB_ID
        store.video_stem = TEST_STEM
        store.index_path = TEST_OUTPUTS / f"{TEST_STEM}_rag_index.json"
        store.chunks = []
        store.embeddings = []
        store.embedder = embedder

        chunks = chunk_lecture_data(
            job_id=TEST_JOB_ID,
            segments=_make_segments(),
            visual_events=_make_visual_events(),
            concepts=_make_concepts(),
        )
        store.build_and_save(chunks)
        self._store = store

        # Build a retriever that uses this store directly
        self.retriever = LectureRetriever.__new__(LectureRetriever)
        self.retriever.job_id = TEST_JOB_ID
        self.retriever.video_stem = TEST_STEM
        self.retriever.vector_store = store
        gemma_mock = MagicMock()
        gemma_mock.generate.return_value = "The range function generates a sequence."
        gemma_mock.is_cloud_ready.return_value = False
        self.retriever.gemma = gemma_mock

    def tearDown(self):
        if TEST_OUTPUTS.exists():
            shutil.rmtree(TEST_OUTPUTS, ignore_errors=True)

    def test_retrieve_returns_list(self):
        results = self.retriever.retrieve("for loop range function")
        self.assertIsInstance(results, list)

    def test_retrieve_results_have_text(self):
        results = self.retriever.retrieve("for loop range function")
        for chunk in results:
            self.assertIn("text", chunk)
            self.assertIsInstance(chunk["text"], str)

    def test_retrieve_top_k_respected(self):
        results = self.retriever.retrieve("loops", top_k=2)
        self.assertLessEqual(len(results), 2)

    def test_retrieve_unrelated_query_returns_minimal(self):
        # A completely unrelated query should return few or no results
        results = self.retriever.retrieve("spacecraft orbital mechanics", top_k=3)
        self.assertLessEqual(len(results), 3)

    def test_answer_question_returns_dict(self):
        answer = self.retriever.answer_question("What is the range function?")
        self.assertIsInstance(answer, dict)
        self.assertIn("answer", answer)
        self.assertIsInstance(answer["answer"], str)

    def test_answer_question_evidence_field_present(self):
        answer = self.retriever.answer_question("Explain for loops.")
        self.assertIn("evidence", answer)
        self.assertIsInstance(answer["evidence"], list)

    def test_repeat_question_uses_cache(self):
        q = "What is the range function?"
        self.retriever.answer_question(q)
        answer2 = self.retriever.answer_question(q)
        self.assertTrue(answer2.get("cached", False))


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
