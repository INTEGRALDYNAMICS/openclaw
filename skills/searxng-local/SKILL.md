---
name: searxng-local
description: Search the web using a self-hosted SearXNG metasearch engine. Use this skill whenever you need to find current information, news, documentation, tutorials, or any web content. No API key required - completely free and unlimited.
metadata: { "openclaw": { "emoji": "🔍", "requires": { "env": ["SEARXNG_URL"] } } }
---

# searxng-local — Web Search (No API Key)

Search the web through your local SearXNG instance. SearXNG aggregates results from Google, Bing, DuckDuckGo, and 70+ other engines with full privacy.

## Setup Check

Before searching, verify SearXNG is running:

```bash
curl -s "${SEARXNG_URL:-http://localhost:8080}/healthz" 2>/dev/null || \
  curl -s "${SEARXNG_URL:-http://localhost:8080}/" -o /dev/null -w "%{http_code}"
```

If it returns non-200, start SearXNG — see the startup section below.

## Searching

```bash
# Basic web search (returns top 5 results with title, URL, snippet)
SEARXNG="${SEARXNG_URL:-http://localhost:8080}"
QUERY="your search query here"

curl -s "${SEARXNG}/search?q=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "${QUERY}")&format=json&categories=general" | python3 -c "
import json, sys
data = json.load(sys.stdin)
results = data.get('results', [])
print(f'Found {len(results)} results\n')
for i, r in enumerate(results[:5], 1):
    print(f'[{i}] {r[\"title\"]}')
    print(f'    URL: {r[\"url\"]}')
    print(f'    {r.get(\"content\", \"\")[:200]}')
    print()
"
```

## Parameters

| Parameter    | Values                                       | Description          |
| ------------ | -------------------------------------------- | -------------------- |
| `q`          | Any text (URL-encoded)                       | Search query         |
| `categories` | `general`, `news`, `images`, `science`, `it` | Result type          |
| `language`   | `es`, `en`, `auto`                           | Language filter      |
| `pageno`     | 1, 2, 3...                                   | Page number          |
| `format`     | Always `json`                                | Required for parsing |
| `time_range` | `day`, `week`, `month`, `year`               | Recency filter       |

## Examples

```bash
SEARXNG="${SEARXNG_URL:-http://localhost:8080}"

# News search in Spanish
curl -s "${SEARXNG}/search?q=noticias+inteligencia+artificial&categories=news&language=es&format=json" | \
  python3 -c "import json,sys; [print(r['title'], '\n', r['url'], '\n') for r in json.load(sys.stdin).get('results',[])[:5]]"

# Technical documentation search
curl -s "${SEARXNG}/search?q=python+asyncio+tutorial&categories=it&format=json" | \
  python3 -c "import json,sys; [print(r['title'], '\n', r['url'], '\n') for r in json.load(sys.stdin).get('results',[])[:5]]"

# Recent news (last 24h)
curl -s "${SEARXNG}/search?q=AI+news&categories=news&time_range=day&format=json" | \
  python3 -c "import json,sys; [print(r['title'], '\n', r['url'], '\n') for r in json.load(sys.stdin).get('results',[])[:5]]"

# Fetch full content from a specific URL (no API key needed)
curl -s "https://example.com/article" | python3 -c "
import sys
from html.parser import HTMLParser
class P(HTMLParser):
    def handle_data(self, d):
        if d.strip(): print(d.strip())
p = P(); p.feed(sys.stdin.read())
"
```

## Starting SearXNG (if not running)

### Option A: Docker (recommended)

```bash
# First run
docker run -d \
  --name searxng \
  --restart unless-stopped \
  -p 8080:8080 \
  searxng/searxng

# Enable JSON format (required)
docker exec searxng sed -i 's/formats:/formats:\n    - json/' /etc/searxng/settings.yml 2>/dev/null || true
docker restart searxng
```

### Option B: Python (no Docker needed)

```bash
# Check if already running as a background service
ps aux | grep searxng

# Start with the installed script (if available)
~/.local/searxng/run_searxng.sh &
```

### Check if JSON is enabled

```bash
SEARXNG="${SEARXNG_URL:-http://localhost:8080}"
curl -s "${SEARXNG}/search?q=test&format=json" | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    print('✅ JSON format enabled, SearXNG is ready!')
    print(f'   Found {len(d.get(\"results\",[]))} results for test query')
except:
    print('❌ JSON format NOT enabled. Enable it in SearXNG settings.')
"
```

## Notes

- **No API key required** — completely free and unlimited
- **Privacy-first** — results aggregated without tracking
- **70+ engines** — Google, Bing, DuckDuckGo, Wikipedia, GitHub, and more
- **Set `SEARXNG_URL`** in your `.env` file if running on a different port
