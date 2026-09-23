"""Intent Classification Engine for EduAccess AI Global Assistant.

Classifies incoming user queries into discrete intent categories:
- DETERMINISTIC_ACTION: Direct UI commands (toggles, font size, quiz launch)
- CONVERSATIONAL: Greetings, gratitude, affection, jokes, pleasantries, acknowledgements, farewells
- PLATFORM: Questions about EduAccess AI platform features and capabilities
- CURRENT_VISUAL: Questions about what is currently visible on screen at timestamp
- ACCESSIBILITY: Cross-modal disparity gaps, audio description, missing visual elements
- LEARNING_PROGRESS: Next best action, mastery gaps, recommended next steps
- QUIZ: Practice requests, interactive comprehension questions, quiz hints
- CLARIFICATION: Ambiguous short prompts requesting more context
- LEARNING_HELP: Requests to simplify, explain simply, beginner explanations, examples
- LECTURE_CONTENT: Content-specific lecture questions grounded in active RAG evidence
- GENERAL_QUERY: General programming, AI/ML, tech, data science, math, conceptual Q&A
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any, NamedTuple


class AssistantIntent(str, Enum):
    DETERMINISTIC_ACTION = "deterministic_action"
    CONVERSATIONAL = "conversational"
    PLATFORM = "platform"
    CURRENT_VISUAL = "current_visual"
    ACCESSIBILITY = "accessibility"
    LEARNING_PROGRESS = "learning_progress"
    QUIZ = "quiz"
    CLARIFICATION = "clarification"
    LEARNING_HELP = "learning_help"
    LECTURE_CONTENT = "lecture_content"
    GENERAL_QUERY = "general_query"


class IntentClassification(NamedTuple):
    intent: AssistantIntent
    sub_type: str | None = None
    action: str | None = None
    action_payload: dict[str, Any] | None = None
    direct_reply: str | None = None


# Standard conversational replies (concise, proportional, natural)
GREETING_REPLY = "Hi there! 👋 I'm EduAccess Assistant. How can I help you?"
THANKS_REPLY = "You're welcome! 😊"
STATUS_REPLY = "I'm doing great! Ready to help you learn. What would you like to explore?"
ACK_REPLY = "Got it! Let me know whenever you want to ask a question or explore a concept."
FAREWELL_REPLY = "Goodbye! Happy learning and have a great day! 👋"
AFFECTION_REPLY = "Aww, thank you! ❤️ I'm here to help you learn and explore anytime."
JOKE_REPLY = "Why do programmers prefer dark mode? Because light attracts bugs! 🐛😄 What concept or topic would you like to explore today?"

PLATFORM_EXPLANATION = (
    "I am the EduAccess AI Assistant. EduAccess AI turns educational videos into accessible learning materials for blind, low-vision, deaf, hard-of-hearing, and cognitive-support learners. "
    "The project documentation describes synchronized captions and transcripts, OCR and audio descriptions for visual content, speech-versus-visual accessibility gap analysis, timestamped lecture Q&A, accessibility reports, quizzes, and learning progress tools.\n\n"
    "You can ask general educational questions at any time. When a lecture is open, you can also ask about its transcript, visuals, or a specific moment; those answers use available lecture evidence."
)
CLARIFICATION_REPLY = (
    "Sure — would you like me to explain a concept simply, describe what's on screen, or help you practice with a quiz?"
)


def is_lecture_specific(message: str) -> bool:
    """Check whether the request needs evidence from a particular lecture.

    Topic overlap and an open job alone are never sufficient. The request must
    relate an explanation/question to a lecture artifact, speaker, or moment.
    """
    msg = re.sub(r"\s+", " ", message.lower().strip())
    media = r"(?:lecture|video|lesson|clip|recording|class|presentation|section|part|slide|screen|board|diagram|flowchart|frame|scene|transcript|caption)"
    if re.search(r"\bwhat am i (?:looking at|seeing)\b", msg):
        return True
    if re.search(rf"\b(?:this|that|the|current|last|previous)\s+{media}\b", msg):
        return True
    if re.search(rf"\b(?:in|from|during|according to|based on|within)\s+(?:this|that|the|current|last|previous)\s+{media}\b", msg):
        return True
    if re.search(r"\bwhat\s+(?:did|does|is|was|were|has)\s+(?:the\s+)?(?:teacher|instructor|speaker|presenter|professor|narrator)\b", msg):
        return True
    if re.search(r"\b(?:what|which|where|how|why)\b.*\b(?:shown|displayed|visible|on screen|on the screen|on this slide|on the slide|in the video|in this lecture)\b", msg):
        return True
    if re.search(r"\b(?:what|how|why|explain|summari[sz]e|describe)\b.*\b(?:this|that)\s+(?:part|section|moment|example|step)\b", msg):
        return True
    if re.search(r"\bwhat\s+(?:i|we)\s+(?:just\s+)?(?:watched|saw|heard|learned)\b", msg):
        return True
    if re.search(r"\b(?:in|during)\s+(?:the\s+)?part\s+(?:that\s+)?(?:i|we)\s+just\s+(?:watched|saw)\b", msg):
        return True
    # Arabic lecture references (written as escapes to keep this file encoding-safe).
    arabic_lecture = r"(?:\u0647\u0630\u0627\s+(?:\u0627\u0644\u0645\u0642\u0637\u0639|\u0627\u0644\u0641\u064a\u062f\u064a\u0648|\u0627\u0644\u062f\u0631\u0633)|\u0647\u0630\u0647\s+\u0627\u0644\u0645\u062d\u0627\u0636\u0631\u0629|\u0641\u064a\s+(?:\u0647\u0630\u0627\s+)?(?:\u0627\u0644\u0641\u064a\u062f\u064a\u0648|\u0627\u0644\u0645\u062d\u0627\u0636\u0631\u0629)|\u0627\u0644\u0645\u062f\u0631\u0633|\u0627\u0644\u0645\u0639\u0644\u0645|\u0627\u0644\u0645\u062d\u0627\u0636\u0631|\u0627\u0644\u0634\u0631\u064a\u062d\u0629|\u0627\u0644\u0633\u0644\u0627\u064a\u062f|\u0639\u0644\u0649\s+\u0627\u0644\u0634\u0627\u0634\u0629|\u0641\u064a\s+\u0627\u0644\u0634\u0627\u0634\u0629|\u0645\u0627\u0630\u0627\s+\u0642\u0627\u0644|\u0645\u0627\s+\u0634\u0631\u062d\u0647)"
    if re.search(arabic_lecture, msg):
        return True
    return False


def is_platform_query(message: str) -> bool:
    """Recognize questions whose subject is EduAccess or this assistant."""
    msg = message.lower().replace("what's", "what is")
    msg = re.sub(r"\bwhats\b", "what is", msg)
    msg = re.sub(r"[^\w\s]", " ", msg)
    msg = re.sub(r"\s+", " ", msg).strip()
    product = r"(?:eduaccess(?: ai)?|(?:this|the) platform|(?:this|the) app|(?:this|the) website|(?:this|the) service)"
    about_verbs = r"(?:what is|what does|explain|describe|tell me about|give me an overview of|how does)"
    request_prefix = r"(?:(?:please|could you|can you|would you)\s+)?"
    if re.search(rf"\b{request_prefix}{about_verbs}\s+(?:the\s+)?{product}\b", msg):
        return True
    if re.search(r"\b(?:tell me|explain|describe)\s+(?:what|how)\s+(?:eduaccess(?: ai)?|(?:this|the) platform)\b", msg):
        return True
    arabic_platform = (
        r"\u0645\u0646\s+\u0627\u0646\u062a|"
        r"\u0645\u0627\s+\u0647\u0648\s+eduaccess|"
        r"\u0645\u0627\u0630\u0627\s+\u064a\u0645\u0643\u0646\u0643\s+\u0627\u0646\s+\u062a\u0641\u0639\u0644|"
        r"\u0643\u064a\u0641\s+\u062a\u0639\u0645\u0644\s+\u0647\u0630\u0647\s+\u0627\u0644\u0645\u0646\u0635\u0629|"
        r"\u0628\u0645\u0627\u0630\u0627\s+\u062a\u0633\u0627\u0639\u062f\u0646\u064a|"
        r"\u0645\u0627\s+\u0647\u064a\s+\u0645\u0645\u064a\u0632\u0627\u062a\u0643"
    )
    if re.search(arabic_platform, msg) or "help me understand eduaccess" in msg:
        return True
    return any(phrase in msg for phrase in (
        "who are you", "what are you", "what can you do", "how do you work",
        "what can you help me with", "what can i do here", "tell me about yourself",
        "what features do you have", "introduce yourself",
    ))


def requires_lecture_context(message: str, intent: AssistantIntent) -> bool:
    """Shared message-level decision used by both normal and streaming chat."""
    return intent == AssistantIntent.CURRENT_VISUAL or is_lecture_specific(message)

def classify_intent(message: str) -> IntentClassification:
    """Classify user query into appropriate intent category."""
    raw = message.strip()
    msg = raw.lower()

    if not msg:
        return IntentClassification(
            intent=AssistantIntent.CONVERSATIONAL,
            sub_type="greeting",
            direct_reply=GREETING_REPLY,
        )

    # 1. DETERMINISTIC UI ACTIONS
    # Captions
    if any(p in msg for p in ("turn on caption", "enable caption", "show caption", "شغل الترجمة", "فعل الترجمة")):
        return IntentClassification(
            intent=AssistantIntent.DETERMINISTIC_ACTION,
            action="toggle_captions",
            action_payload={"action": "toggle_captions", "enabled": True, "message": "Captions have been enabled."},
            direct_reply="Captions have been enabled.",
        )
    if any(p in msg for p in ("turn off caption", "disable caption", "hide caption", "اوقف الترجمة", "الغاء الترجمة")):
        return IntentClassification(
            intent=AssistantIntent.DETERMINISTIC_ACTION,
            action="toggle_captions",
            action_payload={"action": "toggle_captions", "enabled": False, "message": "Captions have been disabled."},
            direct_reply="Captions have been disabled.",
        )

    # Audio descriptions
    if any(p in msg for p in ("turn on audio desc", "enable audio desc", "start narration", "شغل الوصف الصوتي")):
        return IntentClassification(
            intent=AssistantIntent.DETERMINISTIC_ACTION,
            action="toggle_audio_description",
            action_payload={"action": "toggle_audio_description", "enabled": True, "message": "Spoken audio descriptions turned on."},
            direct_reply="Spoken audio descriptions turned on.",
        )
    if any(p in msg for p in ("turn off audio desc", "disable audio desc", "stop narration", "اوقف الوصف الصوتي")):
        return IntentClassification(
            intent=AssistantIntent.DETERMINISTIC_ACTION,
            action="toggle_audio_description",
            action_payload={"action": "toggle_audio_description", "enabled": False, "message": "Spoken audio descriptions turned off."},
            direct_reply="Spoken audio descriptions turned off.",
        )

    # Font sizing
    if any(p in msg for p in ("increase font", "larger text", "make text bigger", "تكبير الخط")):
        return IntentClassification(
            intent=AssistantIntent.DETERMINISTIC_ACTION,
            action="font_size",
            action_payload={"action": "font_size", "delta": 1, "message": "Increasing text size."},
            direct_reply="Increasing text size.",
        )
    if any(p in msg for p in ("decrease font", "smaller text", "make text smaller", "تصغير الخط")):
        return IntentClassification(
            intent=AssistantIntent.DETERMINISTIC_ACTION,
            action="font_size",
            action_payload={"action": "font_size", "delta": -1, "message": "Decreasing text size."},
            direct_reply="Decreasing text size.",
        )

    # Open quiz direct UI action
    if any(p in msg for p in ("open quiz", "take quiz", "start quiz", "show quiz", "افتح الاختبار", "بدء الاختبار")):
        return IntentClassification(
            intent=AssistantIntent.DETERMINISTIC_ACTION,
            action="open_quiz",
            action_payload={"action": "open_quiz", "message": "Opening the lecture quiz."},
            direct_reply="Opening the lecture quiz.",
        )

    # 2. CONVERSATIONAL INTENTS
    # Normalize punctuation and emojis for clean conversational match
    clean_words = re.sub(r"[^\w\s]", "", msg).strip().split()
    clean_joined = " ".join(clean_words)

    # Affection & Praise (e.g. "I love you", "love you", "I love you ❤️", "بحبك", "احبك")
    if re.fullmatch(
        r"(i\s+love\s+you(\s+(so\s+much|very\s+much|a\s+lot))?|love\s+you(\s+(so\s+much|too))?|i\s+like\s+you|you\s+are\s+(great|awesome|the\s+best|amazing)|youre\s+(great|awesome|the\s+best|amazing)|بحبك|احبك|أحبك|انت\s+رائع|أنت\s+رائع|ممتاز\s+يا\s+بوت)(\s+(assistant|eduaccess(\s+ai)?|ai|bot|friend))?",
        clean_joined,
    ):
        return IntentClassification(
            intent=AssistantIntent.CONVERSATIONAL,
            sub_type="affection",
            direct_reply=AFFECTION_REPLY,
        )

    # Humor / Jokes
    if any(p in msg for p in ("tell me a joke", "tell a joke", "make me laugh", "say something funny", "قل لي نكتة", "نكتة")):
        return IntentClassification(
            intent=AssistantIntent.CONVERSATIONAL,
            sub_type="joke",
            direct_reply=JOKE_REPLY,
        )

    # Gratitude
    if re.fullmatch(
        r"(thanks(\s+(a\s+lot|very\s+much|so\s+much|again))?|thank\s+you(\s+(very\s+much|so\s+much|a\s+lot|again))?|thx|thank\s+u|many\s+thanks|much\s+appreciated|ty|youre\s+welcome|you\s+are\s+welcome|your\s+welcome|شكرا(\s+جزيلا)?|تسلم|مشكور|جزاك\s+الله\s+خيرا|يعطيك\s+العافية|عفوا)(\s+(assistant|eduaccess(\s+ai)?|ai|bot|team))?",
        clean_joined,
    ):
        return IntentClassification(
            intent=AssistantIntent.CONVERSATIONAL,
            sub_type="gratitude",
            direct_reply=THANKS_REPLY,
        )

    # Status / pleasantries
    if re.fullmatch(
        r"(how\s+are\s+you(\s+doing|\s+today)?|hows\s+it\s+going|how\s+is\s+it\s+going|how\s+are\s+u|whats\s+up|what\s+is\s+up|how\s+do\s+you\s+do|how\s+have\s+you\s+been|كيف\s+حالك|كيفك|عامل\s+ايه|شلونك|اخبارك|كيف\s+الصحة)(\s+(assistant|eduaccess(\s+ai)?|ai|today))?",
        clean_joined,
    ):
        return IntentClassification(
            intent=AssistantIntent.CONVERSATIONAL,
            sub_type="status",
            direct_reply=STATUS_REPLY,
        )

    # Greetings
    if re.fullmatch(
        r"(hi|hello|hey|hiya|howdy|good\s+morning|good\s+afternoon|good\s+evening|good\s+day|welcome|مرحبا|اهلا|السلام\s+عليكم|صباح\s+الخير|مساء\s+الخير|هاي|هلا|اهلين|تحياتي)(\s+(there|assistant|eduaccess(\s+ai)?|ai|bot|friend))?(\s+(there|assistant|eduaccess(\s+ai)?|ai|bot|friend))?",
        clean_joined,
    ):
        return IntentClassification(
            intent=AssistantIntent.CONVERSATIONAL,
            sub_type="greeting",
            direct_reply=GREETING_REPLY,
        )

    # Acknowledgement
    if re.fullmatch(
        r"(ok|okay|got\s+it|great|cool|understood|alright|all\s+right|perfect|sure|sounds\s+good|nice|awesome|gotcha|تمام|حسنا|فهمت|ممتاز|ماشي|اوكي)(\s+(thanks|assistant|eduaccess(\s+ai)?|ai))?",
        clean_joined,
    ):
        return IntentClassification(
            intent=AssistantIntent.CONVERSATIONAL,
            sub_type="acknowledgement",
            direct_reply=ACK_REPLY,
        )

    # Farewells
    if re.fullmatch(
        r"(bye(\s+for\s+now)?|goodbye|good\s+bye|see\s+you(\s+later|\s+soon|\s+around)?|see\s+ya|cya|take\s+care|have\s+a\s+(good|nice|great)\s+(day|evening|night)|مع\s+السلامة|الى\s+اللقاء|إلى\s+اللقاء|باي|وداعا|تصبح\s+على\s+خير)(\s+(assistant|eduaccess(\s+ai)?|ai|friend))?",
        clean_joined,
    ):
        return IntentClassification(
            intent=AssistantIntent.CONVERSATIONAL,
            sub_type="farewell",
            direct_reply=FAREWELL_REPLY,
        )

    # Product identity and capability questions are answered from the project facts above.
    if is_platform_query(msg):
        return IntentClassification(
            intent=AssistantIntent.PLATFORM,
            direct_reply=PLATFORM_EXPLANATION,
        )
    # Visual intent is routed through lecture retrieval so speech, OCR, and visual context can be combined.
    if any(p in msg for p in (
        "what am i looking at", "what is on screen", "what is on the screen",
        "what is shown", "what is displayed", "describe this slide", "describe the screen",
        "describe what is on screen", "what code is shown", "what diagram is this",
        "show visual", "what is visible", "what am i seeing", "describe current screen",
    )) or re.search(r"\b(?:what|describe|show|explain)\b.*\b(?:currently visible|on (?:this|the) screen|on (?:this|the) slide|in (?:this|the) frame|in the current video)\b", msg):
        return IntentClassification(
            intent=AssistantIntent.CURRENT_VISUAL,
        )
    # 5. ACCESSIBILITY & DISPARITY GAP INTENT
    if any(p in msg for p in (
        "what was shown but not explained", "what am i missing", "what did i miss",
        "what important visual information wasnt explained", "what important visual information wasn't explained",
        "accessibility gap", "disparity", "missing visual", "describe visual", "describe this visual",
        "make this easier to understand", "what was not explained", "visual gap",
        "ما الذي فاتني", "ما الذي لم يشرح", "فجوة", "فجوات الشرح", "ما الذي ظهر ولم يذكره المدرس"
    )):
        return IntentClassification(
            intent=AssistantIntent.ACCESSIBILITY,
        )

    # 6. LEARNING PROGRESS / NEXT BEST ACTION INTENT
    if any(p in msg for p in (
        "what should i study next", "what should i do next", "what am i weak at",
        "how can i improve", "what's my next step", "whats my next step", "my progress",
        "next best action", "my learning gaps", "what to study", "recommend next step", "where should i focus",
        "ماذا ادرس بعد ذلك", "ما هي نقاط ضعفي", "كيف احسن مستواي", "ما خطوتي التالية", "تقديمي"
    )):
        return IntentClassification(
            intent=AssistantIntent.LEARNING_PROGRESS,
        )

    # 7. QUIZ / PRACTICE INTENT
    if any(p in msg for p in (
        "quiz me", "give me a quiz", "test me", "test me on this lecture", "give me 5 questions", "give me questions",
        "practice this topic", "practice this topic with me", "practice quiz", "take quiz", "start quiz", "open quiz", "quiz hint",
        "give me a quiz hint", "give me a hint", "show quiz",
        "اختبرني", "اعطني اختبار", "بدء الاختبار", "افتح الاختبار", "تلميح", "اسئلة تدريب"
    )):
        return IntentClassification(
            intent=AssistantIntent.QUIZ,
        )

    # 8. AMBIGUOUS CLARIFICATION INTENT
    if clean_joined in ("tell me more", "more", "continue", "go on", "why", "elaborate", "tell me more details", "زدني", "اكمل", "تابع"):
        return IntentClassification(
            intent=AssistantIntent.CLARIFICATION,
            direct_reply=CLARIFICATION_REPLY,
        )

    # 9. LECTURE-SPECIFIC OR GENERAL CONTENT ROUTING
    lecture_ref = is_lecture_specific(msg)

    # Learning help / simplification queries
    learning_help_phrases = (
        "i don't understand", "i dont understand", "explain it simply", "explain this simply", "explain simply",
        "explain like i'm a beginner", "explain like im a beginner", "can you explain this like i'm a beginner",
        "can you explain this like im a beginner", "can you simplify", "give me an example",
        "why does this work", "can you explain that again", "explain that again",
        "eli5", "simplify this", "break this down", "make this simpler", "make it simpler",
        "اشرح ببساطة", "لم افهم", "بسط هذا", "اشرح كمبتدئ", "اعطني مثال", "وضح اكثر"
    )
    is_learning_help = any(p in msg for p in learning_help_phrases)

    if lecture_ref:
        if is_learning_help:
            return IntentClassification(intent=AssistantIntent.LEARNING_HELP)
        return IntentClassification(intent=AssistantIntent.LECTURE_CONTENT)

    if is_learning_help:
        return IntentClassification(intent=AssistantIntent.LEARNING_HELP)

    # Default to GENERAL_QUERY for all standard technical, programming, AI/ML, educational, or general questions
    return IntentClassification(
        intent=AssistantIntent.GENERAL_QUERY,
    )
