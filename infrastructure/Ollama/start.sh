#!/bin/bash

# Ollama LLM Service Startup Script for Agent47

echo "🚀 Starting Ollama LLM Service with Llama 3 8B..."

# Start Ollama service in background
echo "📦 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 15

# Check if Ollama is running
echo "🔍 Checking Ollama service..."
for i in {1..30}; do
    if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama service is running!"
        break
    fi
    echo "⏳ Waiting for Ollama... (attempt $i/30)"
    sleep 3
done

# Download Llama 3 8B model if not present
echo "📥 Checking for Llama 3 8B model..."
if ! curl -f http://localhost:11434/api/tags | grep -q "llama3:8b"; then
    echo "📥 Downloading Llama 3 8B model..."
    ollama pull llama3:8b
    echo "✅ Llama 3 8B model downloaded!"
else
    echo "✅ Llama 3 8B model already available!"
fi

# Start the FastAPI service
echo "🌐 Starting FastAPI service on port 8008..."
python main.py &

# Keep both services running
wait $OLLAMA_PID