"""Whitelisted Tools for EduAccess AI Global Assistant.

Allows the assistant to safely interact with lecture evidence and trigger UI actions:
- Information tools (lecture state, active segments, visual events, RAG search, concepts, gaps)
- Controlled UI actions (navigation, toggles, quiz)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from backend import storage
from backend.services import lecture_data, knowledge_graph, learning_gaps, progress as progress_service
from backend.services.rag import get_retriever

logger = logging.getLogger("eduaccess.ai.assistant.tools")

ASSISTANT_TOOL_DEFINITIONS = [
    {
        "name": "get_current_segment",
        "description": "Get what the teacher is saying at the current playback timestamp.",
        "parameters": {},
    },
    {
        "name": "get_current_visual_event",
        "description": "Get what visual slide, code, or diagram is visible on screen right now.",
        "parameters": {},
    },
    {
        "name": "search_lecture",
        "description": "Search the lecture transcript, visual events, and concepts for an answer.",
        "parameters": {
            "query": {"type": "string", "description": "The search query or concept"}
        },
    },
    {
        "name": "get_concept",
        "description": "Get educational definition, status, and evidence for a specific concept.",
        "parameters": {
            "concept_name": {"type": "string", "description": "The concept name (e.g. 'for loops')"}
        },
    },
    {
        "name": "get_learning_gap",
        "description": "Get the student's weak concepts or unmastered areas.",
        "parameters": {},
    },
    {
        "name": "get_progress",
        "description": "Get overall student progress and quiz performance.",
        "parameters": {},
    },
    {
        "name": "toggle_captions",
        "description": "Turn closed captions on or off in the video player.",
        "parameters": {
            "enabled": {"type": "boolean", "description": "True to enable, False to disable"}
        },
    },
    {
        "name": "toggle_audio_description",
        "description": "Turn spoken audio descriptions on or off.",
        "parameters": {
            "enabled": {"type": "boolean", "description": "True to enable, False to disable"}
        },
    },
    {
        "name": "open_quiz",
        "description": "Open the quiz for the current lecture.",
        "parameters": {},
    },
    {
        "name": "navigate_to",
        "description": "Navigate to a lecture timestamp or page.",
        "parameters": {
            "path_or_time": {"type": "string", "description": "Timestamp in seconds (e.g. '12.4') or page route"}
        },
    },
]


def execute_tool(name: str, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Execute a whitelisted tool against current context."""
    job_id = (
        context.get("lecture_id")
        or context.get("job_id")
        or context.get("lectureId")
        or context.get("job")
        or ""
    )
    current_time = float(context.get("timestamp") or 0.0)
    student_id = context.get("student_id") or "default"

    if name == "get_current_segment":
        if not job_id or not storage.job_exists(job_id):
            return {"text": "No active lecture selected."}
        job = storage.get_job(job_id)
        result = job.get("result") or {}
        segments = lecture_data.load_segments(job, result)
        for s in segments:
            if float(s.get("start", 0)) <= current_time <= float(s.get("end", 0)):
                return {"segment": s, "text": s.get("text", ""), "start": s.get("start"), "end": s.get("end")}
        return {"text": "No speech detected at this exact second."}

    if name == "get_current_visual_event":
        if not job_id or not storage.job_exists(job_id):
            return {"description": "No active lecture selected."}
        job = storage.get_job(job_id)
        result = job.get("result") or {}
        events = lecture_data.load_visual_events(job, result)
        for ev in events:
            if float(ev.get("start", 0)) <= current_time <= float(ev.get("end", 0)):
                return {
                    "type": ev.get("type"),
                    "description": ev.get("description"),
                    "ocr_text": ev.get("ocr_text", ""),
                    "start": ev.get("start"),
                    "end": ev.get("end"),
                }
        return {"description": "Standard video scene without notable slides or code."}

    if name == "search_lecture":
        query = args.get("query", "")
        if not job_id or not query:
            return {"results": []}
        job = storage.get_job(job_id)
        stem = Path(job.get("video_path", "")).stem or job_id
        retriever = get_retriever(job_id, stem)
        chunks = retriever.retrieve(query, top_k=3)
        return {"results": [{"text": c.get("text"), "time": c.get("timestamp_label")} for c in chunks]}

    if name == "get_concept":
        cname = args.get("concept_name", "").strip().lower()
        if not job_id:
            return {"concept": cname, "status": "UNKNOWN"}
        kg = knowledge_graph.get_knowledge_graph(job_id)
        for c in kg.get("concepts", []):
            if c.get("concept_id", "").lower() == cname or c.get("label", "").lower() == cname:
                return c
        return {"concept": cname, "status": "UNKNOWN", "note": "Concept not explicitly catalogued in lecture knowledge graph."}

    if name == "get_learning_gap":
        if not job_id:
            return {"gaps": []}
        return learning_gaps.student_gaps(student_id, job_id)

    if name == "get_progress":
        return progress_service.get_progress(student_id)

    # UI actions return instructions for the frontend to perform
    if name == "toggle_captions":
        return {"action": "toggle_captions", "enabled": bool(args.get("enabled", True))}

    if name == "toggle_audio_description":
        return {"action": "toggle_audio_description", "enabled": bool(args.get("enabled", True))}

    if name == "open_quiz":
        return {"action": "open_quiz", "job_id": job_id}

    if name == "navigate_to":
        return {"action": "navigate_to", "target": str(args.get("path_or_time", ""))}

    return {"error": f"Unknown tool: {name}"}
