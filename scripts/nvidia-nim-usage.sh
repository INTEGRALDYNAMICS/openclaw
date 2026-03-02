#!/bin/bash
# nvidia-nim-usage.sh — Monitor de uso de tokens NVIDIA NIM
# Uso: bash nvidia-nim-usage.sh

API_KEY="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"

echo "📊 NVIDIA NIM — Monitor de uso"
echo "================================"
echo ""

# Check API status
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $API_KEY" \
  "https://integrate.api.nvidia.com/v1/models")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API Status: OK (HTTP $HTTP_CODE)"
    echo ""
    echo "📋 Modelos disponibles:"
    curl -s -H "Authorization: Bearer $API_KEY" \
      "https://integrate.api.nvidia.com/v1/models" 2>/dev/null | \
      python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    for m in d.get('data',[]):
        print(f'  - {m[\"id\"]}')
except: print('  (no se pudo parsear)')
"
else
    echo "❌ API Status: Error (HTTP $HTTP_CODE)"
fi

echo ""
echo "💡 NVIDIA NIM Free Tier:"
echo "  - Rate limit: ~40 req/min per model"
echo "  - No monthly token cap (pero puede cambiar)"
echo "  - Si falla MiniMax, usá: /model meta/llama-3.3-70b-instruct"
