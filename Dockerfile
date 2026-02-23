# ===== BUILD STAGE =====
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Python dependencies only
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache

# ===== RUNTIME STAGE =====
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install ONLY essential runtime packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    alsa-utils \
    poppler-utils \
    espeak-ng \
    xclip \
    wl-clipboard \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app
COPY app.py .

# Create cache directory
RUN mkdir -p /root/.cache/tts_app

# Verify setup
RUN echo "=== TTS Setup Verification ===" && \
    echo "EdgeTTS: $(edge-tts --version 2>/dev/null || echo 'not found')" && \
    echo "espeak: $(espeak --version 2>/dev/null || echo 'not found')" && \
    echo "mpg123: $(mpg123 --version 2>/dev/null | head -1 || echo 'not found')"

ENTRYPOINT ["python", "app.py"]
