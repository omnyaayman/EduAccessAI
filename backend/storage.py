"""
Very small JSON-file-based job store. No database needed for the MVP --
each processing job gets a JSON file in data/jobs/<job_id>.json that tracks
status and results, so the frontend can poll GET /result/{job_id}.

Writes are atomic (temp file + os.replace) so a crash can never leave a
corrupted JSON file behind. A module-level lock serialises concurrent writes
from background pipeline tasks.
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend import config

_write_lock = threading.RLock()  # serialise concurrent job writes


def new_job_id() -> str:
    return uuid.uuid4().hex[:12]


def _job_path(job_id: str) -> Path:
    return config.JOBS_DIR / f"{job_id}.json"


def _atomic_write_text(path: Path, text: str) -> None:
    """Write text to a temp file then atomically replace the target."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


def create_job(job_id: str, data: dict) -> None:
    data = {
        **data,
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "current_stage": "uploaded",
        "error": None,
        "logs": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _write_lock:
        _atomic_write_text(_job_path(job_id), json.dumps(data, indent=2, ensure_ascii=False))


def update_job(job_id: str, **fields) -> dict:
    data = get_job(job_id)
    data.update(fields)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    with _write_lock:
        _atomic_write_text(_job_path(job_id), json.dumps(data, indent=2, ensure_ascii=False))
    return data


def get_job(job_id: str) -> dict:
    clean_id = job_id.removesuffix(".mp4").removesuffix(".json")
    path = _job_path(clean_id)
    if not path.exists():
        path = _job_path(job_id)
    if not path.exists():
        # Case-insensitive fallback
        for p in config.JOBS_DIR.glob("*.json"):
            if p.stem.lower() == clean_id.lower() or p.stem.lower() == job_id.lower():
                with _write_lock:
                    return json.loads(p.read_text(encoding="utf-8"))
        raise FileNotFoundError(f"Job not found: {job_id}")
    with _write_lock:
        return json.loads(path.read_text(encoding="utf-8"))


def job_exists(job_id: str) -> bool:
    if not job_id:
        return False
    clean_id = job_id.removesuffix(".mp4").removesuffix(".json")
    if _job_path(clean_id).exists() or _job_path(job_id).exists():
        return True
    for p in config.JOBS_DIR.glob("*.json"):
        if p.stem.lower() == clean_id.lower() or p.stem.lower() == job_id.lower():
            return True
    return False


def append_log(job_id: str, level: str, message: str) -> dict:
    """Append an observability event to the job's log, e.g. stage completion."""
    job = get_job(job_id)
    logs = list(job.get("logs", []))
    logs.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
    })
    job["logs"] = logs
    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    with _write_lock:
        _atomic_write_text(_job_path(job_id), json.dumps(job, indent=2, ensure_ascii=False))
    return job


def list_jobs() -> list[dict]:
    """Return all job records, newest first."""
    jobs = []
    for path in config.JOBS_DIR.glob("*.json"):
        try:
            with _write_lock:
                jobs.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    jobs.sort(key=lambda j: str(j.get("updated_at", j.get("created_at", ""))), reverse=True)
    return jobs