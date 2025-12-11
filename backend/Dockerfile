# Agent47 Backend Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

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

# Copy requirements first for better Docker layer caching (using repo root context)
COPY backend/requirements.txt ./requirements.txt
COPY backend/agents/requirements.txt ./agents-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r agents-requirements.txt

# Copy application code
COPY backend/ .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/uploads /app/chroma_db /app/models \
    && chown -R agent47:agent47 /app

# Set permissions for scripts
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# Switch to non-root user
USER agent47

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]
