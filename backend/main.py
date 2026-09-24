"""
EduAccess AI -- FastAPI backend entrypoint.

Run with:
    uvicorn backend.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import config
from backend.routes import upload, process, quiz, student, analytics, learning, assistant

app = FastAPI(
    title="EduAccess AI",
    description="Turns educational videos into accessible learning experiences "
                 "(captions, audio descriptions, adaptive quizzes, 'What am I missing?' "
                 "and grounded Ask-the-Video) for students with visual or hearing disabilities.",
    version="2.0.0",
    contact={"name": "EduAccess AI"},
)

import os

cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
if cors_origins_raw.strip() == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip().rstrip("/") for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if cors_origins_raw.strip() != "*" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(upload.router, tags=["upload"])
app.include_router(process.router, tags=["process"])
app.include_router(quiz.router, tags=["quiz"])
app.include_router(student.router, tags=["student"])
app.include_router(analytics.router, tags=["analytics"])
app.include_router(learning.router, tags=["learning"])
app.include_router(assistant.router, tags=["assistant"])


# Crash-safety net (Priority 4 Feature #12): an unhandled exception must never
# leak a Python traceback to the normal UI. The real detail goes to the server
# logs; the client gets a stable, friendly JSON error.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger("eduaccess").exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "EduAccess AI hit an unexpected error on this request. "
                           "The problem has been recorded in the server logs."},
    )

# Serve generated files (transcripts, SRTs, narration audio, frames) directly
app.mount("/files/outputs", StaticFiles(directory=str(config.OUTPUTS_DIR)), name="outputs")
# Serve the original video files so the player can seek/embed them
app.mount("/files/videos", StaticFiles(directory=str(config.VIDEOS_DIR)), name="videos")


@app.get("/")
async def root():
    return {
        "service": "EduAccess AI",
        "tagline": "Making educational video understandable for everyone.",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "system_status": "/system/status",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "EduAccess AI",
        "version": "2.0.0",
    }
