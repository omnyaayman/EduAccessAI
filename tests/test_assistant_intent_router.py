"""Comprehensive Unit & Regression Tests for Assistant Intent Router & General AI Architecture.

Tests all intent categories & context-aware routing:
1. CONVERSATIONAL ("Hi", "Hello", "Thanks", "How are you?", "I love you", "Tell me a joke")
2. PLATFORM ("Who are you?", "What can you do?", "What is EduAccess?")
3. CURRENT_VISUAL ("What am I looking at right now?")
4. ACCESSIBILITY ("What was shown but not explained?")
5. LEARNING_HELP ("I don't understand this.", "Explain this simply.")
6. QUIZ ("Quiz me.", "Test me on this lecture.")
7. LEARNING_PROGRESS ("What should I study next?", "What am I weak at?")
8. CLARIFICATION ("Tell me more.")
9. LECTURE_CONTENT ("Explain this section.", "What did the teacher say?")
10. GENERAL_QUERY ("What is Python?", "What is SQL?", "What is machine learning?", "What is a for loop?")
11. DETERMINISTIC_ACTION ("turn on captions", "increase font")
"""
import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock

from backend.services.assistant.intent import (
    AssistantIntent,
    classify_intent,
    is_lecture_specific,
    GREETING_REPLY,
    THANKS_REPLY,
    STATUS_REPLY,
    AFFECTION_REPLY,
    JOKE_REPLY,
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

    def test_intent_classification_conversational_affection_and_jokes(self):
        """Test 'I love you', 'love you', 'tell me a joke', 'say something funny'."""
        affections = ["I love you", "love you", "I love you ❤️", "بحبك", "احبك"]
        for a in affections:
            res = classify_intent(a)
            self.assertEqual(res.intent, AssistantIntent.CONVERSATIONAL)
            self.assertEqual(res.sub_type, "affection")
            self.assertEqual(res.direct_reply, AFFECTION_REPLY)

        jokes = ["Tell me a joke", "make me laugh", "say something funny", "قل لي نكتة"]
        for j in jokes:
            res = classify_intent(j)
            self.assertEqual(res.intent, AssistantIntent.CONVERSATIONAL)
            self.assertEqual(res.sub_type, "joke")
            self.assertEqual(res.direct_reply, JOKE_REPLY)

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

    def test_intent_classification_general_query(self):
        """General questions like 'What is Python?', 'What is SQL?' must be GENERAL_QUERY."""
        general_queries = [
            "What is Python?",
            "What is machine learning?",
            "What is a for loop?",
            "What is SQL?",
            "Explain recursion simply",
            "What is data science?",
            "Tell me about neural networks",
        ]
        for q in general_queries:
            res = classify_intent(q)
            self.assertIn(
                res.intent,
                (AssistantIntent.GENERAL_QUERY, AssistantIntent.LEARNING_HELP),
                f"Query '{q}' should be GENERAL_QUERY or LEARNING_HELP, got {res.intent}",
            )

    def test_intent_classification_lecture_specific(self):
        """Lecture-referencing queries must be recognized as lecture-specific."""
        lecture_queries = [
            ("Explain this section", True),
            ("What did the teacher just explain?", True),
            ("What did the instructor say about loops?", True),
            ("According to this video, what is a variable?", True),
            ("What is shown on this slide?", True),
            ("What was shown but not explained?", True),
            ("What am I looking at right now?", True),
            ("What is Python?", False),
            ("What is SQL?", False),
            ("What is machine learning?", False),
            ("I love you", False),
            ("Tell me a joke", False),
        ]
        for q, expected in lecture_queries:
            self.assertEqual(
                is_lecture_specific(q),
                expected,
                f"is_lecture_specific failed for '{q}': expected {expected}",
            )

    def test_intent_classification_deterministic_actions(self):
        actions = [
            ("turn on captions", "toggle_captions"),
            ("turn off captions", "toggle_captions"),
            ("turn on audio description", "toggle_audio_description"),
            ("increase font", "font_size"),
            ("decrease font", "font_size"),
            ("open quiz", "open_quiz"),
        ]
        for query, expected_action in actions:
            res = classify_intent(query)
            self.assertEqual(res.intent, AssistantIntent.DETERMINISTIC_ACTION)
            self.assertEqual(res.action, expected_action)

    # ==================== 2. ORCHESTRATOR BEHAVIOR ====================

    def test_general_chat_without_lecture_context(self):
        """General questions without a lecture context return helpful general AI answers."""
        queries = [
            ("What is Python?", "Python is a versatile high-level programming language."),
            ("What is machine learning?", "Machine learning enables systems to learn from data."),
            ("What is a for loop?", "A for loop iterates over elements in a collection."),
            ("What is SQL?", "SQL is a standard language for querying relational databases."),
            ("Explain recursion simply", "Recursion is when a function calls itself to solve smaller subproblems."),
        ]
        for q, expected_reply in queries:
            with patch.object(self.orchestrator.gemma, "generate_cloud", return_value=expected_reply):
                res = self.orchestrator.chat(q, context={})
                self.assertNotIn("Open or process a lecture first", res["reply"])
                self.assertNotIn("DEMO_python_loops", res["reply"])
                self.assertEqual(res["evidence"], [])
                self.assertEqual(res["provider"], "huggingface/gemma")
                self.assertEqual(res["reply"], expected_reply)

    def test_general_chat_with_active_lecture_bypasses_rag(self):
        """General questions asked WHILE inside an active lecture must NOT fire lecture RAG."""
        context = {"lecture_id": self.demo_job, "timestamp": 12.0}
        with patch("backend.services.assistant.orchestrator.get_retriever") as mock_retriever:
            with patch.object(self.orchestrator.gemma, "generate_cloud", return_value="SQL manages relational databases."):
                res_sql = self.orchestrator.chat("What is SQL?", context=context)
                mock_retriever.assert_not_called()
                self.assertNotIn("Open or process a lecture first", res_sql["reply"])
                self.assertEqual(res_sql["evidence"], [])
                self.assertIn("SQL", res_sql["reply"])

            res_love = self.orchestrator.chat("I love you", context=context)
            mock_retriever.assert_not_called()
            self.assertEqual(res_love["reply"], AFFECTION_REPLY)

            res_joke = self.orchestrator.chat("Tell me a joke", context=context)
            mock_retriever.assert_not_called()
            self.assertEqual(res_joke["reply"], JOKE_REPLY)

    def test_lecture_specific_query_with_active_lecture_uses_rag(self):
        """Lecture-specific queries inside an active lecture execute grounded RAG retrieval."""
        context = {"lecture_id": self.demo_job, "timestamp": 12.0}
        with patch.object(
            self.orchestrator.gemma,
            "generate_cloud",
            return_value="The teacher explains that a for loop iterates 5 times citing [00:10]."
        ):
            res = self.orchestrator.chat("Explain this section", context=context)
            self.assertEqual(res["provider"], "huggingface/gemma")
            self.assertIn("for loop", res["reply"])
            self.assertTrue(len(res["evidence"]) > 0)

    def test_lecture_specific_query_without_lecture_prompts_user(self):
        """Lecture-specific questions without an active lecture guide the user politely."""
        res_visual = self.orchestrator.chat("What am I looking at right now?", context={})
        self.assertIn("Please open or select a lecture video first", res_visual["reply"])

        res_section = self.orchestrator.chat("Explain this section", context={})
        self.assertIn("Please open or select a lecture video first", res_section["reply"])

    def test_streaming_general_chat(self):
        """SSE streaming correctly delivers general AI answers token-by-token."""
        async def mock_stream(*args, **kwargs):
            for token in ["Python ", "is ", "a ", "programming ", "language."]:
                yield token

        with patch.object(self.orchestrator.gemma, "stream_chat", side_effect=mock_stream):
            async def run_stream():
                tokens = []
                async for chunk_str in self.orchestrator.stream_chat("What is Python?", context={}):
                    data = json.loads(chunk_str)
                    tokens.append(data.get("token", ""))
                return "".join(tokens)

            result = asyncio.run(run_stream())
            self.assertNotIn("Open or process a lecture first", result)
            self.assertEqual(result.strip(), "Python is a programming language.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
