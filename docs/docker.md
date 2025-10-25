# Docker Usage

Das md2cf Docker Image unterstützt zwei Modi: **REST API Server** und **CLI Commands**.

## Quick Start

### REST API Server (Standard)

```bash
# Server starten
docker run -p 8000:8000 md2cf

# API Dokumentation aufrufen
open http://localhost:8000/docs
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
  md2cf publish /workspace/README.md --space DEMO --title "Documentation"
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
  md2cf publish /workspace/README.md --space DEMO --title "My Page"
```

#### Mit Parent Page

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf publish /workspace/README.md \
    --space DEMO \
    --title "Child Page" \
    --parent-id 123456
```

#### Download Source

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf download-source 123456
```

#### Convert Only

```bash
docker run --rm -v $(pwd):/workspace \
  md2cf \
  md2cf convert /workspace/input.md -o /workspace/output.html
```

### Helper Funktion (Optional)

Füge zu `~/.bashrc` oder `~/.zshrc` hinzu:

```bash
md2cf() {
    docker run --rm -v $(pwd):/workspace \
      -e CONFLUENCE_URL -e CONFLUENCE_TOKEN -e CONFLUENCE_SPACE -e JIRA_URL \
      md2cf \
      md2cf "$@"
}
```

Danach können Sie direkt nutzen:

```bash
md2cf publish README.md --space DEMO --title "My Doc"
md2cf download-source 123456
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
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN `
  md2cf `
  md2cf publish /workspace/README.md --space DEMO --title "My Page"
```

#### Download Source

```powershell
docker run --rm -v ${PWD}:/workspace `
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN `
  md2cf `
  md2cf download-source 123456
```

### PowerShell Funktion (Optional)

Füge zu Ihrem PowerShell Profil hinzu (`$PROFILE`):

```powershell
function md2cf {
    $mdArgs = $args -join ' '
    docker run --rm -v ${PWD}:/workspace `
      -e CONFLUENCE_URL=$env:CONFLUENCE_URL `
      -e CONFLUENCE_TOKEN=$env:CONFLUENCE_TOKEN `
      -e CONFLUENCE_SPACE=$env:CONFLUENCE_SPACE `
      -e JIRA_URL=$env:JIRA_URL `
      md2cf `
      md2cf $mdArgs
}
```

Danach können Sie direkt nutzen:

```powershell
md2cf publish README.md --space DEMO --title "My Doc"
md2cf download-source 123456
```

## Docker Compose

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    image: md2cf:latest
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

### Starten

```bash
docker-compose up -d
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
docker run --rm -v $(pwd):/workspace md2cf md2cf publish /workspace/file.md
```

**Windows PowerShell:**
```powershell
# Verwende ${PWD} statt $(pwd)
docker run --rm -v ${PWD}:/workspace md2cf md2cf publish /workspace/file.md
```

### Permission Denied

```bash
# Führe mit User-ID aus
docker run --rm --user $(id -u):$(id -g) -v $(pwd):/workspace md2cf md2cf convert /workspace/file.md
```

### SSL Certificate Errors

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf publish /workspace/file.md --no-verify-ssl
```
