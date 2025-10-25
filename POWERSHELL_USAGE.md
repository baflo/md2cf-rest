# PowerShell Usage

## Übersicht

Dieses Dokument beschreibt die Verwendung von md2cf in Windows PowerShell mit Docker.

## Voraussetzungen

- Docker Desktop für Windows installiert und gestartet
- PowerShell 5.1 oder höher (oder PowerShell Core 7+)

## Setup

### 1. Umgebungsvariablen setzen

Setze die Umgebungsvariablen in deiner PowerShell-Session:

```powershell
$env:CONFLUENCE_URL = "https://confluence.lvm.de/confluence/"
$env:JIRA_URL = "https://jira.lvm.de/jira/"
$env:CONFLUENCE_TOKEN = "your-personal-access-token"
$env:CONFLUENCE_SPACE = "DEMO"  # Optional
```

### 2. PowerShell-Funktion installieren

#### Option A: Temporär (nur für aktuelle Session)

Kopiere die folgende Funktion in deine PowerShell-Session:

```powershell
function md2cf {
    <#
    .SYNOPSIS
    Convert Markdown to Confluence Storage Format and publish to Confluence

    .DESCRIPTION
    Wrapper function for md2cf Docker container that converts Markdown files to Confluence format
    and can publish them directly to Confluence.

    .PARAMETER Arguments
    Additional arguments to pass to md2cf

    .EXAMPLE
    md2cf convert README.md

    .EXAMPLE
    md2cf convert README.md -o output.html

    .EXAMPLE
    md2cf publish README.md --space DEMO --title "My Document"

    .EXAMPLE
    md2cf publish docs/api.md --space DEMO --title "API Documentation" --parent-id 123456

    .EXAMPLE
    md2cf download-attachment 813134619 document.md -o ./document.md

    .NOTES
    Requires Docker to be installed and running.
    Uses environment variables CONFLUENCE_URL, JIRA_URL and CONFLUENCE_TOKEN if set.
    #>

    [CmdletBinding()]
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Arguments
    )

    # Docker Befehl zusammenbauen mit relativem Pfad
    $dockerArgs = @(
        'run'
        '--rm'
        '-v'
        './:/workspace'
        '--workdir=/workspace'
    )

    # Umgebungsvariablen hinzufügen, falls gesetzt
    if ($env:CONFLUENCE_URL) {
        $dockerArgs += '-e'
        $dockerArgs += "CONFLUENCE_URL=$env:CONFLUENCE_URL"
    }

    if ($env:JIRA_URL) {
        $dockerArgs += '-e'
        $dockerArgs += "JIRA_URL=$env:JIRA_URL"
    }

    if ($env:CONFLUENCE_TOKEN) {
        $dockerArgs += '-e'
        $dockerArgs += "CONFLUENCE_TOKEN=$env:CONFLUENCE_TOKEN"
    }

    if ($env:CONFLUENCE_SPACE) {
        $dockerArgs += '-e'
        $dockerArgs += "CONFLUENCE_SPACE=$env:CONFLUENCE_SPACE"
    }

    # Image und Befehl hinzufügen
    $dockerArgs += 'md2cf-rest'
    $dockerArgs += 'md2cf'

    # Benutzer-Argumente hinzufügen
    if ($Arguments) {
        $dockerArgs += $Arguments
    }

    # Docker Befehl ausführen
    & docker $dockerArgs
}
```

#### Option B: Permanent (PowerShell-Profil)

1. Öffne dein PowerShell-Profil:

```powershell
notepad $PROFILE
```

Falls die Datei nicht existiert:

```powershell
New-Item -Path $PROFILE -Type File -Force
notepad $PROFILE
```

2. Füge die `md2cf`-Funktion (siehe oben) in die Profil-Datei ein

3. Speichere und schließe

4. Lade das Profil neu:

```powershell
. $PROFILE
```

### 3. Umgebungsvariablen persistent machen (Optional)

Um die Umgebungsvariablen permanent zu setzen, füge sie ebenfalls zu deinem PowerShell-Profil hinzu:

```powershell
# Am Anfang von $PROFILE
$env:CONFLUENCE_URL = "https://confluence.lvm.de/confluence/"
$env:JIRA_URL = "https://jira.lvm.de/jira/"
$env:CONFLUENCE_TOKEN = "your-personal-access-token"
$env:CONFLUENCE_SPACE = "DEMO"
```

**Sicherheitshinweis:** Alternativ kannst du die Variablen in einer separaten `.env.ps1`-Datei speichern, die **nicht** ins Git-Repository eingecheckt wird:

```powershell
# .env.ps1 erstellen
@"
`$env:CONFLUENCE_URL = "https://confluence.lvm.de/confluence/"
`$env:JIRA_URL = "https://jira.lvm.de/jira/"
`$env:CONFLUENCE_TOKEN = "your-personal-access-token"
`$env:CONFLUENCE_SPACE = "DEMO"
"@ | Out-File -FilePath .env.ps1 -Encoding UTF8

# Laden (vor der Verwendung von md2cf)
. .\.env.ps1
```

Füge `.env.ps1` zu deiner `.gitignore` hinzu:

```
.env.ps1
```

## Verwendung

### Publish-Beispiele

```powershell
# Einfaches Publish
md2cf publish README.md --space DEMO --title "Documentation"

# Mit Custom Title und Parent Page
md2cf publish docs/api.md --space DEMO --title "API Documentation" --parent-id 123456

# Mit Jira-Links (nutzt $env:JIRA_URL)
md2cf publish api-docs.md --space DEMO --title "API Docs"

# Ohne Info-Panel
md2cf publish document.md --space DEMO --title "Document" --no-info-panel

# Mit Verbose Logging
md2cf publish README.md --space DEMO --title "Docs" -v
```

### Download-Beispiele

```powershell
# Attachment herunterladen
md2cf download-attachment 813134619 "API_Documentation.md"

# Mit Custom Output-Pfad
md2cf download-attachment 813134619 "API_Documentation.md" -o ./downloads/doc.md
```

### Convert-Beispiele

```powershell
# Nur konvertieren (ohne Publish)
md2cf convert README.md

# Konvertieren und in Datei speichern
md2cf convert README.md -o output.html
```

### Hilfe anzeigen

```powershell
# md2cf Hilfe
md2cf --help

# PowerShell-Funktion Hilfe
Get-Help md2cf -Full
```

## Vollständiger Workflow

### 1. Setup (einmalig)

```powershell
# Umgebungsvariablen setzen
$env:CONFLUENCE_URL = "https://confluence.lvm.de/confluence/"
$env:JIRA_URL = "https://jira.lvm.de/jira/"
$env:CONFLUENCE_TOKEN = "your-token-here"
$env:CONFLUENCE_SPACE = "DEMO"

# md2cf-Funktion laden (falls nicht im Profil)
. .\md2cf-function.ps1
```

### 2. Dokument publizieren

```powershell
md2cf publish api-docs.md --space DEMO --title "API Documentation"
```

**Ausgabe:**
```
Successfully published page: API Documentation
Page ID: 813134619
URL: https://confluence.lvm.de/confluence/spaces/DEMO/pages/813134619/API+Documentation
```

### 3. Markdown herunterladen

```powershell
md2cf download-attachment 813134619 "API_Documentation.md"
```

**Ausgabe:**
```
Successfully downloaded attachment
File: API_Documentation.md
Saved to: ./API_Documentation.md
```

### 4. Lokal bearbeiten

```powershell
notepad API_Documentation.md
# oder
code API_Documentation.md  # VS Code
```

### 5. Re-publish

```powershell
md2cf publish API_Documentation.md --space DEMO --title "API Documentation"
```

## Tipps & Tricks

### Mehrere Dateien publizieren

```powershell
# Alle .md Dateien im Verzeichnis
Get-ChildItem -Filter *.md | ForEach-Object {
    $title = $_.BaseName -replace '[_-]', ' '
    md2cf publish $_.Name --space DEMO --title $title
}
```

### Mit Docker Compose

Erstelle `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    image: md2cf-rest
    ports:
      - "8000:8000"
    environment:
      - WORKERS=4
      - LOG_LEVEL=info
```

Starten:

```powershell
docker-compose up -d
```

### Debugging

```powershell
# Verbose Logging
md2cf publish document.md --space DEMO --title "Doc" -v

# Docker Container Shell öffnen
docker run --rm -it -v ./:/workspace md2cf-rest /bin/bash
```

### REST API verwenden (Alternative)

Statt CLI kannst du auch die REST API verwenden:

```powershell
# API starten
docker run -d -p 8000:8000 --name md2cf-api md2cf-rest

# API verwenden (mit Invoke-RestMethod)
$markdown = Get-Content -Path README.md -Raw
$body = @{
    markdown = $markdown
    confluence_url = $env:CONFLUENCE_URL
    token = $env:CONFLUENCE_TOKEN
    space = "DEMO"
    title = "My Document"
    jira_url = $env:JIRA_URL
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/publish `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

## Troubleshooting

### "docker: command not found"

**Problem:** Docker ist nicht im PATH

**Lösung:**
- Stelle sicher, dass Docker Desktop installiert ist
- Starte PowerShell neu nach der Docker-Installation

### "Cannot find path '/workspace/document.md'"

**Problem:** Relativer Pfad funktioniert nicht

**Lösung:** Die Funktion verwendet `./:/workspace`. Stelle sicher, dass du im richtigen Verzeichnis bist:

```powershell
Get-Location  # Zeigt aktuelles Verzeichnis
Get-ChildItem *.md  # Zeigt alle .md Dateien
```

### "Confluence URL is required"

**Problem:** Umgebungsvariablen nicht gesetzt

**Lösung:**

```powershell
# Prüfen
$env:CONFLUENCE_URL

# Setzen
$env:CONFLUENCE_URL = "https://confluence.lvm.de/confluence/"
```

### Encoding-Probleme mit Umlauten

**Problem:** Deutsche Umlaute werden falsch dargestellt

**Lösung:** Stelle sicher, dass die Markdown-Datei UTF-8 kodiert ist:

```powershell
# Datei als UTF-8 speichern
$content = Get-Content -Path document.md -Raw
$content | Out-File -FilePath document.md -Encoding UTF8
```

### PowerShell Execution Policy

**Problem:** `md2cf-function.ps1 cannot be loaded because running scripts is disabled`

**Lösung:**

```powershell
# Execution Policy für aktuelle Session ändern
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Oder für aktuellen Benutzer (permanent)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Umgebungsvariablen-Übersicht

| Variable | Beschreibung | Erforderlich | Beispiel |
|----------|--------------|--------------|----------|
| `CONFLUENCE_URL` | Confluence Base URL | Ja (für Publish) | `https://confluence.lvm.de/confluence/` |
| `CONFLUENCE_TOKEN` | Personal Access Token | Ja (für Publish) | `your-token-here` |
| `CONFLUENCE_SPACE` | Default Space Key | Nein | `DEMO` |
| `JIRA_URL` | Jira Base URL für Ticket-Links | Nein | `https://jira.lvm.de/jira/` |

## Siehe auch

- [README.md](README.md) - Allgemeine Dokumentation
- [DOCKER_CLI_USAGE.md](DOCKER_CLI_USAGE.md) - Docker CLI Usage (Linux/macOS)
- [DOCKER_CLI_QUICK_REFERENCE.md](DOCKER_CLI_QUICK_REFERENCE.md) - Quick Reference
- [REST_API.md](REST_API.md) - REST API Dokumentation
