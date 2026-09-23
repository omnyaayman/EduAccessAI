# EduAccess AI — Operational Runbook

## System Architecture & Prerequisites

EduAccess AI is designed to run in a dual-server configuration:
1. **Backend API**: Python 3.11+ / FastAPI running on `http://127.0.0.1:8000`
2. **Frontend App**: Next.js 15.5 (React 19) running on `http://localhost:3000`

---

## 1. System Requirements

### Hardware / OS
- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 8 GB (16 GB recommended for local Whisper medium model)
- **CPU / GPU**: Multithreaded modern CPU or NVIDIA CUDA GPU for Whisper/PyTorch acceleration.

### System Software Dependencies
- **Python**: Version `3.11.x` or `3.12.x`
- **Node.js**: Version `18.18.0+` or `20.x+` (npm 9+)
- **FFmpeg**: Must be installed and available on system PATH (`ffmpeg -version` must succeed).
- **Tesseract OCR** *(Optional for local OCR)*:
  - Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - Linux: `sudo apt install tesseract-ocr`
  - macOS: `brew install tesseract`

---

## 2. Environment Configuration (`.env`)

Create `.env` in the repository root (or copy `.env.example`):

```bash
# Optional Hugging Face Cloud Token (Enables Cloud Gemma 3 4B & VoxCPM TTS)
HF_TOKEN=your_hf_token_here
HF_GEMMA_MODEL=google/gemma-3-4b-it
HF_VOXCPM_MODEL=voxcpm/voxcpm-base
HF_PROVIDER=auto

# Speech-to-Text Configuration
WHISPER_MODEL_SIZE=medium
LANGUAGE_FORCE_THRESHOLD=0.5

# Providers (auto defaults to Cloud if key present, else local offline fallback)
VISION_PROVIDER=auto
LLM_PROVIDER=auto
TTS_PROVIDER=auto
```

---

## 3. Step-by-Step Installation & Startup

### Step A: Backend Setup
```bash
# Navigate to repository root
cd EduAccess-AI

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI backend
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend is live at:* `http://127.0.0.1:8000` *(Interactive Swagger API docs at:* `http://127.0.0.1:8000/docs`*)*

### Step B: Frontend Setup
```bash
# Open a new terminal and navigate to Next.js app directory
cd EduAccess-AI/frontend/next-app

# Install Node dependencies
npm install

# Start development server
npm run dev
```
*Frontend is live at:* `http://localhost:3000`

---

## 4. Pre-Loaded Demonstration Data

The repository includes pre-computed lecture assets in `data/outputs/` and pre-packaged video in `data/videos/`:
- `DEMO_python_loops.mp4` (`DEMO_python_loops`): Fully processed lecture on Python Loops with 100% verified captions, visual events, knowledge graph, and audio description tracks.

To run the demo instantly without waiting for Whisper/OCR processing:
1. Open `http://localhost:3000`
2. Launch **"DEMO_python_loops"** (`/lectures/DEMO_python_loops`).
3. The lecture workspace opens immediately with all multimodal representations.

---

## 5. Automated Verification & Testing

```bash
# Run backend test suite
pytest -v

# Run frontend typechecking
cd frontend/next-app
npm run typecheck
```

---

## 6. Troubleshooting Common Issues

| Issue | Cause | Solution |
|---|---|---|
| `FFmpeg is not installed or is not available on PATH` | Missing FFmpeg executable | Install FFmpeg and add the `bin` directory to your system environment variables. |
| `Hugging Face request failed with HTTP 400/401` | Invalid or missing `HF_TOKEN` | System automatically falls back to local offline generators (pyttsx3/Tesseract/Rule templates). Check token in `.env`. |
| `Audio description does not play in browser` | Browser autoplay security policy | Click anywhere on the webpage or click the "Enable Audio Description" switch to grant audio playback permissions. |
| `Port 8000 or 3000 already in use` | Zombie background process | Kill process using port: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`. |
