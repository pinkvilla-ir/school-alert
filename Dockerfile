# Multi-stage build for school-alert FastAPI app
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    gcc \
    libssl-dev \
    libffi-dev \
    python3-dev \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (copy whole repo so services/, models/, etc. are included)
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port for FastAPI (Cloud Run expects $PORT, usually 8080)
EXPOSE 8080

# Health check — hit the same port the app listens on (respect $PORT)
# Increase start-period to give the app extra time to initialize on cold starts
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-8080}/health || exit 1'

# Run FastAPI with uvicorn, respect Cloud Run's $PORT (default to 8080)
ENV PORT=8080

# Use python -m uvicorn to ensure the module is executed with the container Python
CMD ["sh", "-c", "python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT} --log-level info"]
