FROM python:3.11-slim

# Set environment variables (REMOVE hardcoded PORT=8080)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8080

# Set work directory
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r agent47 && useradd -r -g agent47 agent47

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./requirements.txt
COPY agents/requirements.txt ./agents-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r agents-requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/uploads /app/chroma_db /app/models \
    && chown -R agent47:agent47 /app

# Set permissions for scripts
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# Switch to non-root user
USER agent47

# Expose a common port (optional; Render uses $PORT anyway)
EXPOSE 8080

# Optional: Updated health check to use $PORT (for local/docker testing)
# Render uses its own platform health check configured separately
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run uvicorn using Render's $PORT (defaults to 8080)
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT