# Ollama LLM Dockerfile for Agent47
FROM python:3.11-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_PORT=11434

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app

# Set working directory
WORKDIR /app

# Copy application files
COPY main.py .
COPY start.sh .
RUN chmod +x start.sh

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# Start the FastAPI service (Ollama will be provided by external service)
CMD ["python", "main.py"]
