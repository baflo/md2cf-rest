# Docker CLI Usage

## Übersicht

Das Docker Image unterstützt **zwei Modi**:

1. **REST API Modus** (Standard): Startet den Web-Server
2. **CLI Modus**: Führt md2cf CLI-Befehle aus

## Voraussetzungen

Umgebungsvariablen setzen (einmalig):

```bash
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_TOKEN="your-personal-access-token"
export CONFLUENCE_SPACE="DEMO"  # Optional
export JIRA_URL="https://jira.lvm.de/jira"  # Optional, für Jira-Link-Konvertierung
```

## Verwendung

### 1. REST API Modus (Standard)

Startet den Web-Server auf Port 8000:

```bash
docker run -p 8000:8000 md2cf-api
```

**Zugriff:**
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

### 2. CLI Modus

#### Grundlegendes Beispiel

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL \
  -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf publish /workspace/document.md --space DEMO --title "My Document"
```

**Erklärung:**
- `--rm`: Container nach Ausführung löschen
- `-v $(pwd):/workspace`: Aktuelles Verzeichnis in Container mounten
- `-e CONFLUENCE_URL`: Umgebungsvariable übergeben
- `md2cf publish ...`: CLI-Befehl ausführen

#### Publish-Beispiel

```bash
# Einfaches Publish
docker run --rm \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL \
  -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf publish /workspace/README.md --space DEMO --title "Documentation"

# Mit Jira-Links (via Umgebungsvariable)
docker run --rm \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL \
  -e CONFLUENCE_TOKEN \
  -e JIRA_URL \
  md2cf-api \
  md2cf publish /workspace/api-docs.md \
    --space DEMO \
    --title "API Documentation"

# Oder mit direktem Parameter
docker run --rm \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL \
  -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf publish /workspace/api-docs.md \
    --space DEMO \
    --title "API Documentation" \
    --jira-url "https://jira.lvm.de/jira"

# Ohne Info-Panel
docker run --rm \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL \
  -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf publish /workspace/doc.md \
    --space DEMO \
    --title "Document" \
    --no-info-panel
```

#### Download-Beispiel

```bash
# Attachment herunterladen
docker run --rm \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL \
  -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf download-attachment 123456 "API_Documentation.md"

# Das File wird nach /workspace/API_Documentation.md gespeichert
# und ist dann im aktuellen Verzeichnis verfügbar
```

#### Convert-Beispiel

```bash
# Nur konvertieren (ohne Publish)
docker run --rm \
  -v $(pwd):/workspace \
  md2cf-api \
  md2cf convert /workspace/input.md -o /workspace/output.html
```

### 3. Docker Compose

Erstelle `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # REST API Service
  api:
    image: md2cf-api
    ports:
      - "8000:8000"
    environment:
      - WORKERS=4
      - LOG_LEVEL=info
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  # CLI Service (für manuelle Ausführung)
  cli:
    image: md2cf-api
    volumes:
      - ./documents:/workspace
    environment:
      - CONFLUENCE_URL=${CONFLUENCE_URL}
      - CONFLUENCE_TOKEN=${CONFLUENCE_TOKEN}
      - CONFLUENCE_SPACE=${CONFLUENCE_SPACE}
      - JIRA_URL=${JIRA_URL}
    entrypoint: ["/usr/local/bin/docker-entrypoint.sh"]
    # Startet nicht automatisch, nur für 'docker-compose run cli ...'
    command: /bin/bash
    profiles:
      - cli
```

**Verwendung:**

```bash
# REST API starten
docker-compose up -d api

# CLI verwenden
docker-compose run --rm cli md2cf publish /workspace/doc.md --space DEMO --title "Title"
```

## Shell-Alias für einfachere Nutzung

Füge zu deiner `~/.bashrc` oder `~/.zshrc` hinzu:

```bash
# md2cf CLI via Docker
alias md2cf-docker='docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN -e CONFLUENCE_SPACE -e JIRA_URL \
  md2cf-api md2cf'
```

**Dann einfach:**

```bash
md2cf-docker publish document.md --space DEMO --title "My Doc"
md2cf-docker download-attachment 123456 "file.md"
```

## Vollständiger Workflow-Beispiel

### 1. Umgebung vorbereiten

```bash
# .env Datei erstellen
cat > .env <<EOF
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_TOKEN=your-token-here
CONFLUENCE_SPACE=DEMO
JIRA_URL=https://jira.lvm.de/jira
EOF

# Laden
source .env
```

### 2. Dokument publizieren

```bash
docker run --rm \
  -v $(pwd):/workspace \
  --env-file .env \
  md2cf-api \
  md2cf publish /workspace/api-docs.md --space DEMO --title "API Documentation"
```

**Ausgabe:**
```
Successfully published page: API Documentation
Page ID: 123456
URL: https://your-domain.atlassian.net/wiki/spaces/DEMO/pages/123456/API+Documentation
```

### 3. Markdown herunterladen (aus Info-Box kopieren)

```bash
docker run --rm \
  -v $(pwd):/workspace \
  --env-file .env \
  md2cf-api \
  md2cf download-attachment 123456 "API_Documentation.md"
```

**Ausgabe:**
```
Successfully downloaded attachment
File: API_Documentation.md
Saved to: ./API_Documentation.md
```

### 4. Lokal bearbeiten

```bash
vim ./API_Documentation.md
```

### 5. Re-publish

```bash
docker run --rm \
  -v $(pwd):/workspace \
  --env-file .env \
  md2cf-api \
  md2cf publish /workspace/API_Documentation.md --space DEMO --title "API Documentation"
```

## Tipps & Tricks

### Mehrere Dateien publizieren

```bash
# Alle .md Dateien im Verzeichnis
for file in *.md; do
  docker run --rm \
    -v $(pwd):/workspace \
    -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
    md2cf-api \
    md2cf publish "/workspace/$file" --space DEMO --title "${file%.md}"
done
```

### Mit eigenem Netzwerk

```bash
# Netzwerk erstellen
docker network create md2cf-net

# API starten
docker run -d --name md2cf-api --network md2cf-net -p 8000:8000 md2cf-api

# CLI verwenden
docker run --rm --network md2cf-net \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf publish /workspace/doc.md --space DEMO --title "Doc"
```

### Debugging

```bash
# Verbose Logging
docker run --rm \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf publish /workspace/doc.md --space DEMO --title "Doc" -v

# Shell im Container
docker run --rm -it \
  -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf-api \
  /bin/bash
```

## Umgebungsvariablen

| Variable | Beschreibung | Erforderlich | Standard |
|----------|--------------|--------------|----------|
| `CONFLUENCE_URL` | Confluence Base URL | Ja (für CLI) | - |
| `CONFLUENCE_TOKEN` | Personal Access Token | Ja (für CLI) | - |
| `CONFLUENCE_SPACE` | Default Space Key | Nein | - |
| `JIRA_URL` | Jira Base URL für Ticket-Link-Konvertierung | Nein | - |
| `WORKERS` | Anzahl Gunicorn Workers | Nein | 4 |
| `PORT` | REST API Port | Nein | 8000 |
| `LOG_LEVEL` | Log Level (info, debug, etc.) | Nein | info |

## Unterschied REST API vs. CLI

| Aspekt | REST API | CLI |
|--------|----------|-----|
| **Verwendung** | Web-Service | Einmalige Befehle |
| **Start** | `docker run -p 8000:8000 md2cf-api` | `docker run md2cf-api md2cf ...` |
| **Zugriff** | HTTP Requests | Kommandozeile |
| **Files** | Upload via HTTP | Mount via Volume |
| **Auth** | In Request | Via Env Vars |
| **Persistent** | Läuft dauerhaft | Stoppt nach Ausführung |

## Troubleshooting

### "File not found"

**Problem**: `/workspace/document.md: No such file or directory`

**Lösung**: Stelle sicher, dass das Volume korrekt gemountet ist:
```bash
docker run --rm -v $(pwd):/workspace md2cf-api ls -la /workspace
```

### "Confluence URL is required"

**Problem**: Umgebungsvariablen nicht gesetzt

**Lösung**:
```bash
# Prüfen
echo $CONFLUENCE_URL

# Setzen
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
```

### Permission Errors

**Problem**: Permission denied beim Schreiben

**Lösung**: Der Container läuft als User `md2cf` (UID 1000). Stelle sicher, dass die Files lesbar sind:
```bash
chmod -R 755 ./documents
```

## Siehe auch

- [README.md](README.md) - Allgemeine Dokumentation
- [DOCKER.md](DOCKER.md) - Docker Setup & Deployment
- [CLI_EXAMPLE_IN_INFO_PANEL.md](CLI_EXAMPLE_IN_INFO_PANEL.md) - CLI Beispiele aus Info-Panel
