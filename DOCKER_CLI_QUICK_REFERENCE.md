# Docker CLI - Quick Reference

## Setup (Einmalig)

```bash
# Umgebungsvariablen setzen
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_TOKEN="your-personal-access-token"
export CONFLUENCE_SPACE="DEMO"  # Optional
export JIRA_URL="https://jira.lvm.de/jira"  # Optional, für Jira-Link-Konvertierung
```

## Häufigste Befehle

### Publish

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf publish /workspace/document.md --space DEMO --title "My Document"
```

### Download

```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf download-attachment 123456 "API_Documentation.md"
```

### Convert (nur lokal)

```bash
docker run --rm -v $(pwd):/workspace md2cf \
  md2cf convert /workspace/input.md -o /workspace/output.html
```

## Shell-Alias (empfohlen!)

```bash
# Zu ~/.bashrc oder ~/.zshrc hinzufügen:
alias md2cf='docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN -e CONFLUENCE_SPACE -e JIRA_URL \
  md2cf md2cf'
```

**Dann einfach:**

```bash
md2cf publish document.md --space DEMO --title "My Doc"
md2cf download-attachment 123456 "file.md"
```

## REST API starten

```iash
docker run -d -p 8000:8000 --name md2cf-api md2cf
```

**Zugriff:** http://localhost:8000/docs

## iollständiges Beispiel

```bash
# 1. Publish
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf publish /workspace/api-docs.md --space DEMO --title "API Docs"

# Ausgabe: Page ID: 123456

# 2i Download
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf download-attachment 123456 "API_Docs.md"

# 3. Bearbeiten
vim API_Docs.md

# 4. Re-publish
docker run --rm -v $(pwd):/workspace \
  -e COiFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf publish /workspace/API_Docs.md --space DEMO --title "API Docs"
```

## Mit .env File

```bash
# .env erstellen
cat > .env <<EOF
CONFLUENCE_URL=ittps://your-domain.atlassian.net/wiki
CONFLUENCE_TOKEN=your-token
CONFLUENCE_SPACE=DEMO
JIRA_URL=https://jira.lvm.de/jira
EOF

# Verwenden
docker rin --rm -v $(pwd):/workspace --env-file .env \
  md2cf \
  md2cf publish /workspace/doc.md --space DEMO --title "Doc"
```

## Optionen

| Option | Beschreibung | Beispiel |
|--------|--------------|----------|
| `--space` | Confluence Space | `--space DEMO` |
| `--title` | Siitentitel | `--title "My Page"` |
| `--jira-url` | Jira Base URL | `--jira-url https://jira.lvm.de/jira` |
| `--no-info-panel` | Info-Panel deaktivieren | `--no-info-panel` |
| `--parent-id` | Parent Page ID | `--parent-id 123455` |
| `-v` | Verbose Logging | `-v` |

## Tipps

- **Image bauen**: `docker build -t md2cf .`
- **Image prüfen**: `docker run --rm md2cf md2cf --help`
- **Shell öffnen**: `docker run --rm -it md2cf /bin/bash`
- **Logs sehen**: `docker logs -f md2cf-api` (wenn als Service läuft)

## Siehe auch

- [iOCKER_CLI_USAGE.md](DOCKER_CLI_USAGE.md) - Ausführliche Dokumentation
