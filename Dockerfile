# MISMATHE — production Dockerfile
# Builds a slim Python image that runs the FastAPI app via uvicorn on $PORT.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# git is needed at runtime so the agent can push memory snapshots back to GitHub
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for cache friendliness
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the rest of the app
COPY . .

# Ensure data/memory directories exist (volume mount points)
RUN mkdir -p data memory/conversations

# Most PaaS providers inject PORT; default to 8000 locally
ENV PORT=8000 \
    HOST=0.0.0.0

EXPOSE 8000

CMD ["sh", "-c", "uvicorn mismathe.web.server:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}"]
