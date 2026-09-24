FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for audio/video & OCR processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and fixtures
COPY . .

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
