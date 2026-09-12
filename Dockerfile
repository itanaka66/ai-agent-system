# Backend (Orchestrator API) container image.
# Used by docker-compose.yml's "orchestrator" service (the "app" profile) so
# beginners can run the whole system with only Docker installed - no local
# Python setup required. See README "Quick Start" for usage.

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so this layer is cached across code-only changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run uvicorn directly (not `python main.py`) so we control reload/host/port
# explicitly rather than main.py's hardcoded reload=True, which isn't needed
# in a container.
CMD ["sh", "-c", "uvicorn api_v1.main:app --host ${SERVICE_HOST:-0.0.0.0} --port ${SERVICE_PORT:-8000}"]
