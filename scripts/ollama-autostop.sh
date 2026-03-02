#!/bin/bash
# ollama-autostop.sh — Para Ollama si está idle más de IDLE_MINS minutos
# Uso: ./ollama-autostop.sh [minutos_idle]

IDLE_MINS=${1:-10}
OLLAMA_LOG="/tmp/ollama-last-request.txt"

# Si Ollama no está corriendo, salir sin error
if ! pgrep -f "ollama" > /dev/null 2>&1; then
    exit 0
fi

# Verificar último request via API
LAST_ACTIVE=$(curl -s --max-time 2 http://127.0.0.1:11434/api/tags > /dev/null 2>&1 && echo $(date +%s) || echo 0)

# Leer timestamp del último uso guardado
if [ -f "$OLLAMA_LOG" ]; then
    LAST_SAVED=$(cat "$OLLAMA_LOG")
else
    echo $(date +%s) > "$OLLAMA_LOG"
    exit 0
fi

NOW=$(date +%s)
IDLE_SECS=$((IDLE_MINS * 60))
ELAPSED=$((NOW - LAST_SAVED))

if [ "$ELAPSED" -gt "$IDLE_SECS" ]; then
    echo "$(date): Ollama idle por ${ELAPSED}s, deteniendo..."
    systemctl --user stop ollama 2>/dev/null || pkill -f "ollama serve" 2>/dev/null
    rm -f "$OLLAMA_LOG"
fi
