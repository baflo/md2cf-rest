# Docker Usage

Das md2cf Docker Image unterstützt alle CLI-Befehle über den `md2cf` Befehl.

## Quick Start

### REST API Server

```bash
# Server starten
docker run -p 8000:8000 md2cf api

# API Dokumentation aufrufen
open http://localhost:8000/docs

# Mit benutzerdefinierten Einstellungen
docker run -p 8080:8080 md2cf api --port 8080 --workers 8 --log-level debug
```

### CLI Commands

```bash
# Umgebungsvariablen setzen
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_TOKEN="your-personal-access-token"

# Dokument publizieren
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  publish /workspace/README.md --space DEMO --title "Documentation"
```

## Linux/macOS CLI

### Setup (Einmalig)

```bash
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_TOKEN="your-personal-access-token"
export CONFLUENCE_SPACE="DEMO"  # Optional
export JIRA_URL="https://jira.example.com"  # Optional
```

### Häufige Befehle

#### Publish

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  publish /workspace/README.md --space DEMO --title "My Page"
```

#### Mit Parent Page

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  publish /workspace/README.md \
    --space DEMO \
    --title "Child Page" \
    --parent-id 123456
```

#### Download Source

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  download-source 123456
```

#### Convert Only

```bash
docker run --rm -v $(pwd):/workspace \
  md2cf \
  convert /workspace/input.md -o /workspace/output.html
```

### Helper Funktion (Optional)

Füge zu `~/.bashrc` oder `~/.zshrc` hinzu:

```bash
md2cf() {
    docker run --rm -v $(pwd):/workspace \
      -e CONFLUENCE_URL -e CONFLUENCE_TOKEN -e CONFLUENCE_SPACE -e JIRA_URL \
      md2cf \
      "$@"
}
```

Danach können Sie direkt nutzen:

```bash
md2cf publish README.md --space DEMO --title "My Doc"
md2cf download-source 123456
md2cf api  # API Server starten
```

## Windows PowerShell

### Setup (Einmalig)

```powershell
$env:CONFLUENCE_URL = "https://your-domain.atlassian.net/wiki"
$env:CONFLUENCE_TOKEN = "your-personal-access-token"
$env:CONFLUENCE_SPACE = "DEMO"  # Optional
$env:JIRA_URL = "https://jira.example.com"  # Optional
```

### Häufige Befehle

#### Publish

```powershell
docker run --rm -v ${PWD}:/workspace `
  -e "CONFLUENCE_URL=${env:CONFLUENCE_URL}" -e "CONFLUENCE_TOKEN=${env:CONFLUENCE_TOKEN}" `
  md2cf `
  publish README.md --space DEMO --title "My Page"
```

#### Download Source

```powershell
docker run --rm -v ${PWD}:/workspace `
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN `
  md2cf `
  download-source 123456
```

### PowerShell Funktion (Optional)

Füge zu Ihrem PowerShell Profil hinzu (`$PROFILE`):

```powershell
function md2cf {
    docker run --rm -v ${PWD}:/workspace `
      -e CONFLUENCE_URL=$env:CONFLUENCE_URL `
      -e CONFLUENCE_TOKEN=$env:CONFLUENCE_TOKEN `
      -e CONFLUENCE_SPACE=$env:CONFLUENCE_SPACE `
      -e JIRA_URL=$env:JIRA_URL `
      md2cf `
      $args
}
```

Danach können Sie direkt nutzen:

```powershell
md2cf publish README.md --space DEMO --title "My Doc"
md2cf download-source 123456
md2cf api  # API Server starten
```

## Docker Compose

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    image: md2cf:latest
    command: api
    ports:
      - "8000:8000"
    environment:
      - CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
      - CONFLUENCE_TOKEN=${CONFLUENCE_TOKEN}
      - PORT=8000
      - WORKERS=4
      - LOG_LEVEL=info
    restart: unless-stopped
```

### Starten

```bash
# Production starten
docker compose --profile production up -d

# Development starten
docker compose --profile dev up

# Logs anzeigen
docker compose logs -f api
```

## Image bauen

```bash
# Standard Build
docker build -t md2cf:latest .

# Mit Make
make docker-build

# Mit BuildKit
DOCKER_BUILDKIT=1 docker build -t md2cf:latest .
```

## Troubleshooting

### Volume Mount funktioniert nicht

**Linux/macOS:**
```bash
# Stelle sicher, dass der absolute Pfad verwendet wird
docker run --rm -v $(pwd):/workspace md2cf publish /workspace/file.md
```

**Windows PowerShell:**
```powershell
# Verwende ${PWD} statt $(pwd)
docker run --rm -v ${PWD}:/workspace md2cf publish /workspace/file.md
```

### Permission Denied

```bash
# Führe mit User-ID aus
docker run --rm --user $(id -u):$(id -g) -v $(pwd):/workspace md2cf convert /workspace/file.md
```

### SSL Certificate Errors

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  publish /workspace/file.md --no-verify-ssl
```
