#!/bin/sh

echo "🚀 Starting Ollama server in background..."
ollama serve &

# Guardamos el PID del proceso
OLLAMA_PID=$!

# Esperar a que el servidor responda antes de intentar el pull
echo "⏳ Waiting for Ollama server to be ready..."
while ! ollama list > /dev/null 2>&1; do
  sleep 2
done

echo "📦 Pulling model: llava..."
ollama pull llava:7b

echo "✅ Model ready. Switching to foreground..."

# Esperar al proceso principal
wait $OLLAMA_PID