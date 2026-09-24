"""
Speech-to-text service, built on OpenAI's Whisper (runs 100% locally,
no API key needed -- it just needs the `openai-whisper` pip package and
enough disk space for the model weights to download once).

Whisper is imported lazily so the rest of the app still works (frames,
quizzes, TTS, etc.) even before you've installed/downloaded it.

Arabic support: Whisper runs 100% in transcription mode (task="transcribe",
never translation), and when it confidently detects Arabic we force the exact
language code ("ar") so the spoken Arabic is preserved as Arabic -- never
translated to English and never transliterated. Timestamps come from the same
real audio that is transcribed.
"""

from pathlib import Path

from backend import config

_WHISPER_AVAILABLE = False
whisper = None
try:
    import whisper
    _WHISPER_AVAILABLE = True
except ImportError:
    pass


def is_whisper_available() -> bool:
    """True if the openai-whisper package can be imported (its weights may
    still need to be downloaded before the first transcription)."""
    return _WHISPER_AVAILABLE


def _get_whisper():
    import sys
    if "whisper" in sys.modules and sys.modules["whisper"] is not None:
        return sys.modules["whisper"]
    global whisper, _WHISPER_AVAILABLE
    if _WHISPER_AVAILABLE and whisper is not None:
        return whisper
    try:
        import whisper as _whisper
        whisper = _whisper
        _WHISPER_AVAILABLE = True
        return whisper
    except ImportError as e:
        raise RuntimeError(
            "openai-whisper is not installed. Run: pip install openai-whisper"
        ) from e


_model_cache = {}
# Tracks the model actually loaded for each requested size, so callers and the
# API can report the true runtime model even after a fallback (never silently).
_model_actual_used: dict[str, str] = {}


def _load_model(model_size: str | None = None) -> "object":
    """
    Load (and cache) a Whisper model by requested size.

    Robust fallback: if the requested size cannot be downloaded or loaded (e.g.
    missing weights, download failure, OOM), we fall back down the configured
    chain (default configuration.WHISPER_MODEL_FALLBACK). The model size that is
    *actually* used is always recorded in `_model_actual_used`, so we honestly
    report runtime model rather than silently claiming the requested one.
    """
    model_size = model_size or config.WHISPER_MODEL_SIZE
    if model_size in _model_cache:
        _model_actual_used[model_size] = _model_actual_used.get(model_size, model_size)
        return _model_cache[model_size]

    whisper = _get_whisper()

    import threading
    errors: list[str] = []
    for candidate in _candidate_models(model_size):
        try:
            model = whisper.load_model(candidate)
            _model_cache[model_size] = model
            _model_actual_used[model_size] = candidate
            return model
        except Exception as e:  # noqa: BLE001 - honest fallback across sizes
            errors.append(f"{candidate}: {e}")
    raise RuntimeError(
        f"Could not load any Whisper model (requested {model_size!r}). Errors: {errors}"
    )


def _candidate_models(requested: str) -> list[str]:
    """Requested model first, then the configured fallback chain (no dups)."""
    candidates = [requested]
    for m in config._fallback_list():
        if m != requested and m not in candidates:
            candidates.append(m)
    return candidates


def actual_model_size(model_size: str | None = None) -> str:
    """The exact model size actually loaded for a request (after any fallback)."""
    model_size = model_size or config.WHISPER_MODEL_SIZE
    return _model_actual_used.get(model_size, model_size)


def _load_mel(audio_path: Path):
    """Load + preprocess audio exactly the way Whisper transcribes it."""
    whisper = _get_whisper()
    audio = whisper.load_audio(str(audio_path))
    audio = whisper.pad_or_trim(audio)
    return whisper.log_mel_spectrogram(audio).to(_load_model().device)


def detect_language(audio_path: str, model_size: str | None = None) -> dict:
    """
    Detect the spoken language of an audio file using Whisper's language
    classifier. Returns {"language": <code>, "confidence": <0..1>,
    "probabilities": {lang: prob}}.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    whisper = _get_whisper()
    model = _load_model(model_size)
    mel = _load_mel(audio_path)
    # Whisper's detect_language returns (language_token, {lang: prob}).
    tokens, probs = model.detect_language(mel)
    lang = max(probs, key=probs.get)
    return {
        "language": lang,
        "confidence": float(probs.get(lang, 0.0)),
        "probabilities": {k: float(v) for k, v in probs.items()},
    }


def resolve_language(detected: dict | None) -> str | None:
    """
    Decide which explicit language code to force for transcription.

    Arabic is a first-class language here: if it is the top detected language
    and its probability clears the threshold, we return "ar" so Whisper
    transcribes Arabic as Arabic (transcription mode, never translation).
    For all other languages we return None and let Whisper use its own
    (accurate) auto-detection, preserving existing English behaviour.
    """
    if not detected:
        return None
    if detected.get("language") == "ar":
        ar_conf = detected.get("probabilities", {}).get("ar")
        if ar_conf is not None and ar_conf >= config.LANGUAGE_FORCE_THRESHOLD:
            return "ar"
    return None


def transcribe(
    audio_path: str,
    model_size: str | None = None,
    language: str | None = None,
    task: str = "transcribe",
) -> dict:
    """
    Transcribe audio to text with segment-level timestamps.

    Returns Whisper's raw result dict:
        {"text": "...", "segments": [{"start":.., "end":.., "text":..}, ...], "language": "en"}

    - `language` (language code) forces that language when supplied.
    - `task` defaults to "transcribe" and is always transcription mode -- the
      system never translates the teacher's speech (so Arabic is never turned
      into English).
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    model = _load_model(model_size)
    result = model.transcribe(
        str(audio_path),
        language=language,
        task=task,
        fp16=False,  # CPU-safe (torch is CPU-only here); avoids FP16 warnings.
        no_speech_threshold=config.WHISPER_NO_SPEECH_THRESHOLD,
        logprob_threshold=config.WHISPER_LOGPROB_THRESHOLD,
        condition_on_previous_text=config.WHISPER_CONDITION_ON_PREVIOUS_TEXT,
    )
    # Always re-record the effective language on the result object.
    result["language"] = result.get("language") or language
    # Record which model size actually produced this transcription.
    result["model_size"] = actual_model_size(model_size)
    return result


def save_transcript(result: dict, output_path: str) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result["text"].strip(), encoding="utf-8")
    return str(output_path)


def _format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def segments_to_srt(segments: list[dict]) -> str:
    """Convert Whisper segments into SRT-formatted subtitle text."""
    lines = []
    for i, seg in enumerate(segments, start=1):
        start = _format_srt_time(seg["start"])
        end = _format_srt_time(seg["end"])
        text = seg["text"].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def save_srt(segments: list[dict], output_path: str) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(segments_to_srt(segments), encoding="utf-8")
    return str(output_path)
