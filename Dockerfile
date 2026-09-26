# SIH26237 — Production Offline-Ready Container Image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SIH_HOST=0.0.0.0 \
    SIH_PORT=8000 \
    SIH_DATA_DIR=/app/data

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
COPY deployment/requirements-lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY core/ /app/core/
COPY apps/ /app/apps/
COPY demo/ /app/demo/
COPY attacks/ /app/attacks/
COPY scripts/ /app/scripts/
COPY deployment/ /app/deployment/

# Create data and artifact storage directories
RUN mkdir -p /app/data/artifacts /app/data/demo_fixtures /app/artifacts/deployment

# Generate initial demo fixtures
RUN python /app/scripts/deployment/generate_demo_fixtures.py

# Expose API and frontend ports
EXPOSE 8000 5173

# Default entrypoint: start FastAPI backend
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
