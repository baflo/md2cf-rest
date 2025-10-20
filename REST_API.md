# md2cf REST API Documentation

Die md2cf REST API ermöglicht es Ihnen, Markdown über HTTP-Requests in Confluence Storage Format zu konvertieren und direkt zu Confluence zu publizieren.

## Installation

```bash
# REST API Dependencies installieren
pip install -e ".[rest]"
```

## Server starten

### Direkt mit Python
```bash
python -m md2cf.rest_api
```

### Mit Uvicorn
```bash
uvicorn md2cf.rest_api:app --host 0.0.0.0 --port 8000 --reload
```

### Mit Docker (Optional)
```bash
docker build -t md2cf-rest .
docker run -p 8000:8000 md2cf-rest
```

## API Endpoints

### 1. Health Check

**GET /** oder **GET /health**

Überprüft, ob die API läuft.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**Beispiel:**
```bash
curl http://localhost:8000/health
```

---

### 2. Markdown konvertieren

**POST /convert**

Konvertiert Markdown in Confluence Storage Format (XHTML).

**Request Body:**
```json
{
  "markdown": "# Hello World\n\nThis is **bold** text."
}
```

**Response:**
```json
{
  "confluence_storage_format": "<h1>Hello World</h1>\n<p>This is <strong>bold</strong> text.</p>\n",
  "character_count": 55
}
```

**Beispiele:**

```bash
# Einfache Konvertierung
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Hello World\n\nThis is **bold** text."}'

# Aus Datei
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "markdown": "# Dokumentation\n\n## Features\n\n- Feature 1\n- Feature 2\n\n```python\nprint('Hello')\n```"
}
EOF

# Mit jq für schönere Ausgabe
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Test"}' | jq .
```

---

### 3. Zu Confluence publizieren

**POST /publish**

Konvertiert Markdown und publiziert es direkt zu Confluence.

**Request Body:**
```json
{
  "markdown": "# My Documentation\n\nContent here.",
  "confluence_url": "https://your-domain.atlassian.net/wiki",
  "token": "YOUR_TOKEN",
  "space": "DEMO",
  "title": "My Page",
  "parent_id": "123456",
  "cloud": true
}
```

**Parameter:**
- `markdown` (required): Markdown-Inhalt
- `confluence_url` (required): Confluence Base URL
- `token` (required): Personal Access Token oder API Token
- `space` (required): Space Key
- `title` (required): Seitentitel
- `parent_id` (optional): Parent Page ID
- `cloud` (default: true): Confluence Cloud (true) oder Server (false)

**Response:**
```json
{
  "page_id": "123456",
  "page_url": "https://your-domain.atlassian.net/wiki/spaces/DEMO/pages/123456",
  "title": "My Page",
  "space": "DEMO",
  "version": 1
}
```

**Beispiele:**

```bash
# Mit Umgebungsvariablen
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_TOKEN="your_token_here"
export CONFLUENCE_SPACE="DEMO"

curl -X POST http://localhost:8000/publish \
  -H "Content-Type: application/json" \
  -d "{
    \"markdown\": \"# Test Page\n\nThis is a test.\",
    \"confluence_url\": \"$CONFLUENCE_URL\",
    \"token\": \"$CONFLUENCE_TOKEN\",
    \"space\": \"$CONFLUENCE_SPACE\",
    \"title\": \"API Test Page\",
    \"cloud\": true
  }"

# Aus Markdown-Datei
MARKDOWN_CONTENT=$(cat examples/sample.md | jq -Rs .)
curl -X POST http://localhost:8000/publish \
  -H "Content-Type: application/json" \
  -d "{
    \"markdown\": $MARKDOWN_CONTENT,
    \"confluence_url\": \"$CONFLUENCE_URL\",
    \"token\": \"$CONFLUENCE_TOKEN\",
    \"space\": \"$CONFLUENCE_SPACE\",
    \"title\": \"Sample Documentation\",
    \"cloud\": true
  }"
```

---

## Interaktive API Dokumentation

Die API bietet automatisch generierte, interaktive Dokumentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Python Client Beispiele

```python
import requests

# API Base URL
API_URL = "http://localhost:8000"

# 1. Markdown konvertieren
def convert_markdown(markdown: str) -> str:
    response = requests.post(
        f"{API_URL}/convert",
        json={"markdown": markdown}
    )
    response.raise_for_status()
    return response.json()["confluence_storage_format"]

# 2. Zu Confluence publizieren
def publish_to_confluence(
    markdown: str,
    confluence_url: str,
    token: str,
    space: str,
    title: str
) -> dict:
    response = requests.post(
        f"{API_URL}/publish",
        json={
            "markdown": markdown,
            "confluence_url": confluence_url,
            "token": token,
            "space": space,
            "title": title,
            "cloud": True
        }
    )
    response.raise_for_status()
    return response.json()

# Verwendung
if __name__ == "__main__":
    # Konvertierung
    result = convert_markdown("# Hello\n\nThis is **bold**.")
    print(result)

    # Publizieren
    import os
    page = publish_to_confluence(
        markdown="# Test\n\nContent",
        confluence_url=os.getenv("CONFLUENCE_URL"),
        token=os.getenv("CONFLUENCE_TOKEN"),
        space=os.getenv("CONFLUENCE_SPACE"),
        title="API Test"
    )
    print(f"Created page: {page['page_url']}")
```

## JavaScript/TypeScript Beispiele

```javascript
// Mit fetch API
async function convertMarkdown(markdown) {
  const response = await fetch('http://localhost:8000/convert', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ markdown })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.confluence_storage_format;
}

// Mit axios
const axios = require('axios');

async function publishToConfluence(config) {
  const response = await axios.post('http://localhost:8000/publish', {
    markdown: config.markdown,
    confluence_url: config.confluenceUrl,
    token: config.token,
    space: config.space,
    title: config.title,
    cloud: true
  });

  return response.data;
}

// Verwendung
(async () => {
  // Konvertierung
  const html = await convertMarkdown('# Hello World');
  console.log(html);

  // Publizieren
  const page = await publishToConfluence({
    markdown: '# Test\n\nContent',
    confluenceUrl: process.env.CONFLUENCE_URL,
    token: process.env.CONFLUENCE_TOKEN,
    space: process.env.CONFLUENCE_SPACE,
    title: 'API Test'
  });

  console.log(`Page created: ${page.page_url}`);
})();
```

## Fehlerbehandlung

Die API verwendet Standard-HTTP-Statuscodes:

- `200 OK` - Erfolgreiche Konvertierung
- `201 Created` - Seite erfolgreich erstellt/aktualisiert
- `400 Bad Request` - Ungültige Anfrage
- `404 Not Found` - Space nicht gefunden
- `500 Internal Server Error` - Server-Fehler

**Fehler-Response:**
```json
{
  "detail": "Publishing failed: Error message here"
}
```

## Production Deployment

### Mit Gunicorn (Production-ready)
```bash
pip install gunicorn
gunicorn md2cf.rest_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Systemd Service
```ini
[Unit]
Description=md2cf REST API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/md2cf
ExecStart=/path/to/venv/bin/gunicorn md2cf.rest_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker Deployment
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY md2cf/ ./md2cf/

RUN pip install -e ".[rest]" && \
    pip install gunicorn

EXPOSE 8000

CMD ["gunicorn", "md2cf.rest_api:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

## CORS Konfiguration

Standardmäßig erlaubt die API alle Origins (`*`). Für Production sollten Sie dies einschränken:

```python
# In md2cf/rest_api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Nur bestimmte Domains
    allow_credentials=True,
    allow_methods=["POST"],  # Nur benötigte Methoden
    allow_headers=["Content-Type", "Authorization"],
)
```

## Authentifizierung (Optional)

Für zusätzliche Sicherheit können Sie API-Key-Authentifizierung hinzufügen:

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-api-key":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

# In Endpoints verwenden:
@app.post("/convert", dependencies=[Depends(verify_api_key)])
async def convert_markdown(request: ConvertRequest):
    # ...
```

## Monitoring

### Health Check
```bash
# Einfacher Health Check
curl http://localhost:8000/health

# Mit Monitoring-Tool (z.B. Prometheus)
while true; do
  curl -s http://localhost:8000/health | jq .
  sleep 5
done
```

## Limits und Performance

- Max Request Body Size: 10MB (Standard)
- Timeout: 30 Sekunden
- Recommended Workers: 2-4 pro CPU Core

## Support

Bei Fragen oder Problemen:
- GitHub Issues: https://github.com/yourusername/md2cf/issues
- API Dokumentation: http://localhost:8000/docs
