# Multi-stage build: keep image minimal with fping included
FROM python:3.11-slim as base

# Install fping and other network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    fping \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 2: Runtime
FROM base

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Create data directory for SQLite
RUN mkdir -p /data /config

# Health check using fping
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
