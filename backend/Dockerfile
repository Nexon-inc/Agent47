FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y build-essential curl libpq-dev gcc g++ git \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN groupadd -r agent47 && useradd -r -g agent47 agent47

# Install Python packages
COPY requirements.txt .
COPY agents/requirements.txt ./agents-requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r agents-requirements.txt

# Copy code
COPY . .

# Setup dirs and permissions
RUN mkdir -p /app/logs /app/uploads /app/chroma_db /app/models \
    && chown -R agent47:agent47 /app

USER agent47

EXPOSE 8080

# Best for Cloud Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]