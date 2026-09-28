# ==============================================================================
# AegisTrace — Multi-Stage Production & Self-Hosted Container Image
# Stage 1: Build the React / Vite Web Application
# Stage 2: PQC / Dilithium / Kyber Python Runtime with Embedded Static Serving
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Frontend Build
# ------------------------------------------------------------------------------
FROM node:20-alpine AS web-builder

WORKDIR /web

# Install dependencies with lockfile consistency
COPY apps/web/package*.json ./
RUN npm ci --silent

# Build production bundle into /web/dist
COPY apps/web/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Backend & Workstation Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SIH_HOST=0.0.0.0 \
    SIH_PORT=8000 \
    SIH_DATA_DIR=/app/data \
    DEMO_AUTH_ENABLED=false

WORKDIR /app

# Install system dependencies for cryptography and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
COPY deployment/requirements-lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and core forensic engine
COPY core/ /app/core/
COPY apps/ /app/apps/
COPY demo/ /app/demo/
COPY attacks/ /app/attacks/
COPY scripts/ /app/scripts/
COPY deployment/ /app/deployment/

# Copy compiled SPA assets from Stage 1 into FastAPI's static serving path
COPY --from=web-builder /web/dist /app/apps/web/dist

# Create storage directories
RUN mkdir -p /app/data/artifacts /app/data/demo_fixtures /app/artifacts/deployment

# Expose workstation port (Unified Web + API, 8000 default or $PORT on Render)
EXPOSE 8000

# Deep healthcheck against /ready, honoring dynamic $PORT
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, os; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/ready')" || exit 1

# Default entrypoint: Start FastAPI server with signal handling, honoring $PORT
CMD ["sh", "-c", "exec uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 30"]
