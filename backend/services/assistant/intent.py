"""Intent Classification Engine for EduAccess AI Global Assistant.

Classifies incoming user queries into discrete intent categories:
- DETERMINISTIC_ACTION: Direct UI commands (toggles, font size, quiz launch)
- CONVERSATIONAL: Greetings, gratitude, pleasantries, acknowledgements, farewells
- PLATFORM: Questions about EduAccess AI platform features and capabilities
- CURRENT_VISUAL: Questions about what is currently visible on screen at timestamp
- ACCESSIBILITY: Cross-modal disparity gaps, audio description, missing visual elements
- LEARNING_HELP: Requests to simplify, explain simply, beginner explanations, examples
- QUIZ: Practice requests, interactive comprehension questions, quiz hints
- LEARNING_PROGRESS: Next best action, mastery gaps, recommended next steps
- CLARIFICATION: Ambiguous short prompts requesting more context
- LECTURE_CONTENT: Content-specific lecture questions grounded in RAG evidence
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
    LEARNING_HELP = "learning_help"
    QUIZ = "quiz"
    LEARNING_PROGRESS = "learning_progress"
    CLARIFICATION = "clarification"
    LECTURE_CONTENT = "lecture_content"


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
ACK_REPLY = "Got it! Let me know whenever you want to ask a question or explore the lecture."
FAREWELL_REPLY = "Goodbye! Happy learning and have a great day! 👋"

PLATFORM_EXPLANATION = (
    "I am the **EduAccess AI Assistant**, an educational accessibility companion built directly into this platform. Here is what I can help you with:\n\n"
    "• 🎥 **Live On-Screen Visuals**: Ask *'What am I looking at right now?'* to understand on-screen slides, diagrams, and OCR code at your current playback time.\n"
    "• 👁️ **Accessibility & Gap Analysis**: Ask *'What was shown but not explained?'* to discover visual information the teacher displayed without audio narration.\n"
    "• 📖 **Grounded Lecture Q&A**: Ask lecture questions and get verified answers citing exact lecture timestamps and speech evidence.\n"
    "• 💡 **Adaptive Learning Help**: Say *'Explain this simply'* or *'Give me an example'* to get beginner-friendly explanations of difficult concepts.\n"
    "• 📝 **Practice & Quizzes**: Say *'Quiz me'* or *'Test me on this lecture'* to practice interactive questions.\n"
    "• 🎯 **Learning Progress & Next Steps**: Say *'What should I study next?'* to review your concept mastery and personalized study recommendations.\n"
    "• 🎛️ **Accessibility Controls**: Say *'Turn on captions'* or *'Turn on audio descriptions'* to adjust playback controls."
)

CLARIFICATION_REPLY = (
    "Sure — would you like me to explain the current lecture section, describe what's on screen, or help you practice it?"
)


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
    # Normalize punctuation for clean conversational match
    clean_words = re.sub(r"[^\w\s]", "", msg).strip().split()
    clean_joined = " ".join(clean_words)

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

    # 3. PLATFORM CAPABILITY INTENTS
    if any(p in msg for p in (
        "who are you", "what are you", "what is eduaccess", "what is eduaccess ai",
        "what can you do", "how do you work", "how does this platform work", "what can you help me with",
        "what can i do here", "tell me about yourself", "what features do you have", "help me understand eduaccess",
        "introduce yourself", "what is this platform",
        "من انت", "ما هو eduaccess", "ماذا يمكنك ان تفعل", "كيف تعمل هذه المنصة", "بماذا تساعدني", "ما هي مميزاتك"
    )):
        return IntentClassification(
            intent=AssistantIntent.PLATFORM,
            direct_reply=PLATFORM_EXPLANATION,
        )

    # 4. CURRENT VISUAL INTENT
    if any(p in msg for p in (
        "what am i looking at", "what is on screen", "what is on the screen",
        "what is shown", "what is displayed", "describe this slide", "describe the screen",
        "describe what is on screen", "what code is shown", "what diagram is this",
        "show visual", "what is visible", "what am i seeing", "describe current screen",
        "ماذا يظهر على الشاشة", "ما المعروض", "ماذا يوجد على الشاشة", "اشرح الشريحة", "ما هو الرسم", "ما الكود المعروض"
    )):
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

    # 8. LEARNING HELP / SIMPLIFICATION INTENT
    if any(p in msg for p in (
        "i don't understand", "i dont understand", "explain it simply", "explain this simply", "explain this", "explain that",
        "explain like i'm a beginner", "explain like im a beginner", "can you explain this like i'm a beginner",
        "can you explain this like im a beginner", "can you simplify", "give me an example",
        "why does this work", "can you explain that again", "explain that again",
        "eli5", "simplify this", "break this down", "make this simpler", "make it simpler",
        "اشرح ببساطة", "لم افهم", "بسط هذا", "اشرح كمبتدئ", "اعطني مثال", "وضح اكثر"
    )):
        return IntentClassification(
            intent=AssistantIntent.LEARNING_HELP,
        )

    # 9. AMBIGUOUS CLARIFICATION INTENT
    if clean_joined in ("tell me more", "more", "continue", "go on", "why", "elaborate", "tell me more details", "زدني", "اكمل", "تابع"):
        return IntentClassification(
            intent=AssistantIntent.CLARIFICATION,
            direct_reply=CLARIFICATION_REPLY,
        )

    # 10. DEFAULT TO LECTURE CONTENT
    return IntentClassification(
        intent=AssistantIntent.LECTURE_CONTENT,
    )

