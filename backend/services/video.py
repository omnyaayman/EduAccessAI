"""
Video processing service.

Two jobs:
1. extract_audio()  -> pulls a mono 16kHz WAV out of the video (for Whisper)
2. extract_frames() -> samples still frames every N seconds (for Vision)
"""

import importlib
import shutil
import subprocess
from pathlib import Path

from backend import config


def _cv2():
    global _cv2_mod
    if _cv2_mod is None:
        _cv2_mod = importlib.import_module("cv2")
    return _cv2_mod


def _np():
    global _np_mod
    if _np_mod is None:
        _np_mod = importlib.import_module("numpy")
    return _np_mod


_cv2_mod = None
_np_mod = None


def check_system_dependencies() -> dict[str, bool]:
    """
    Check if FFmpeg and Tesseract OCR binaries are installed and reachable.

    Tesseract is frequently installed but simply missing from PATH -- we also
    probe the usual install locations before declaring it unavailable.
    """
    from backend.config import find_tesseract
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "tesseract": find_tesseract() is not None
    }


def get_video_metadata(video_path: str) -> dict:
    """
    Extract video metadata (duration, fps, width, height, frame_count) using OpenCV.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cv2 = _cv2()
    video = cv2.VideoCapture(str(video_path))
    if not video.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = video.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    duration = 0.0
    if fps > 0 and frame_count > 0:
        duration = round(frame_count / fps, 2)
    else:
        duration = round(get_video_duration(str(video_path)), 2)

    video.release()

    return {
        "duration": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "frame_count": frame_count
    }


def extract_audio(video_path: str, audio_path: str | None = None) -> str:
    """Extract mono 16kHz WAV audio from a video file using ffmpeg."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if audio_path is None:
        audio_path = config.AUDIO_DIR / f"{video_path.stem}.wav"
    audio_path = Path(audio_path)
    audio_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",              # no video
        "-ac", "1",         # mono
        "-ar", "16000",     # 16kHz sample rate (what Whisper expects)
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-2000:]}")

    return str(audio_path)


def calculate_frame_difference(frame1, frame2) -> float:
    """
    Calculate the mean absolute difference between two frames.
    Resizes frames to 64x64 and converts to grayscale for speed and noise reduction.
    """
    cv2 = _cv2()
    np = _np()
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    resized1 = cv2.resize(gray1, (64, 64))
    resized2 = cv2.resize(gray2, (64, 64))
    diff = cv2.absdiff(resized1, resized2)
    return float(np.mean(diff))


def extract_frames(video_path: str, output_folder: str | None = None,
                    interval_seconds: float | None = None,
                    scene_threshold: float | None = None) -> list[dict]:
    """
    Sample frames from the video every `interval_seconds` (minimum interval)
    if the visual difference exceeds `scene_threshold` (scene-change detection).
    Always keeps the first frame.
    Returns a list of {"path": ..., "timestamp": seconds} dicts.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    min_interval = interval_seconds or config.FRAME_MIN_INTERVAL
    threshold = scene_threshold or config.SCENE_CHANGE_THRESHOLD
    output_folder = Path(output_folder) if output_folder else (config.FRAMES_DIR / video_path.stem)
    output_folder.mkdir(parents=True, exist_ok=True)

    cv2 = _cv2()
    video = cv2.VideoCapture(str(video_path))
    if not video.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = video.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = 0
    saved_count = 0
    frames = []

    last_candidate_time = -min_interval
    last_saved_frame = None

    while True:
        success, frame = video.read()
        if not success:
            break

        current_time = frame_count / fps

        if frame_count == 0 or current_time >= last_candidate_time + min_interval:
            last_candidate_time = current_time

            if len(frames) == 0:
                filename = output_folder / f"frame_{saved_count:04}.jpg"
                cv2.imwrite(str(filename), frame)
                frames.append({"path": str(filename), "timestamp": round(current_time, 2)})
                saved_count += 1
                last_saved_frame = frame.copy()
            else:
                diff = calculate_frame_difference(frame, last_saved_frame)
                if diff >= threshold:
                    filename = output_folder / f"frame_{saved_count:04}.jpg"
                    cv2.imwrite(str(filename), frame)
                    frames.append({"path": str(filename), "timestamp": round(current_time, 2)})
                    saved_count += 1
                    last_saved_frame = frame.copy()

        frame_count += 1

    video.release()
    return frames


def get_video_duration(video_path: str) -> float:
    """Return video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0
