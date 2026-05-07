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
    mpg123 \
    poppler-utils \
    espeak-ng \
    xclip \
    wl-clipboard \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r tts && useradd -r -g tts -m -d /home/tts tts

# Copy Python packages from builder and fix ownership
COPY --from=builder /root/.local /home/tts/.local
RUN chown -R tts:tts /home/tts/.local
ENV PATH=/home/tts/.local/bin:$PATH

WORKDIR /app
COPY app.py .

# Create cache directory owned by tts user
RUN mkdir -p /home/tts/.cache/tts_app && chown -R tts:tts /home/tts/.cache/tts_app

# Health check: verify espeak-ng is functional
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD espeak-ng --version || exit 1

# Switch to non-root user
USER tts

ENTRYPOINT ["python", "app.py"]
