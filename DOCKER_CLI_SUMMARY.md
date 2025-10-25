# Docker CLI - Zusammenfassung

## ✅ Was wurde implementiert

Das Docker Image unterstützt jetzt **zwei Modi**:

### 1. REST API Modus (Standard)

**Start:**
```bash
docker run -p 8000:8000 md2cf-api
```

**Verwendung:**
- Web-Service auf Port 8000
- API Docs: http://localhost:8000/docs
- Für dauerhaften Betrieb

### 2. CLI Modus (Neu!)

**Start:**
```bash
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf publish /workspace/document.md --space DEMO --title "Title"
```

**Verwendung:**
- Einmalige Befehle
- Zugriff auf lokale Dateien via Volume
- Für Automatisierung & Scripting

## 📁 Dateien

| Datei | Beschreibung |
|-------|--------------|
| `docker-entrypoint.sh` | Entrypoint-Script (erkennt Modus automatisch) |
| `Dockerfile` | Angepasst für beide Modi |
| `DOCKER_CLI_USAGE.md` | Ausführliche Dokumentation |
| `DOCKER_CLI_QUICK_REFERENCE.md` | Quick Reference |
| `README.md` | Aktualisiert mit Docker-Beispielen |

## 🔧 Technische Details

### Entrypoint-Logik

```bash
# Keine Argumente oder "gunicorn" → REST API Modus
docker run md2cf-api
# → Startet Gunicorn Web-Server

# "md2cf" als erstes Argument → CLI Modus
docker run md2cf-api md2cf publish ...
# → Führt CLI-Befehl aus
```

### Volume Mapping

```bash
# /workspace ist das Arbeitsverzeichnis
-v $(pwd):/workspace

# Files im aktuellen Verzeichnis sind dann verfügbar als:
/workspace/document.md
/workspace/images/logo.png
```

### Umgebungsvariablen

**CLI Modus:**
- `CONFLUENCE_URL` - Erforderlich
- `CONFLUENCE_TOKEN` - Erforderlich
- `CONFLUENCE_SPACE` - Optional

**REST API Modus:**
- `WORKERS` - Anzahl Gunicorn Workers (default: 4)
- `PORT` - Port (default: 8000)
- `LOG_LEVEL` - Log Level (default: info)

## 🚀 Verwendung

### Einfachstes Beispiel

```bash
# 1. Umgebung vorbereiten
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_TOKEN="your-token"

# 2. Publish
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf-api \
  md2cf publish /workspace/doc.md --space DEMO --title "Doc"
```

### Shell-Alias (empfohlen)

```bash
# Zu ~/.bashrc hinzufügen:
alias md2cf='docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN -e CONFLUENCE_SPACE \
  md2cf-api md2cf'

# Dann einfach:
md2cf publish document.md --space DEMO --title "Title"
md2cf download-attachment 123456 "file.md"
```

### Mit .env File

```bash
# .env erstellen
cat > .env <<EOF
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_TOKEN=your-token
EOF

# Verwenden
docker run --rm -v $(pwd):/workspace --env-file .env \
  md2cf-api \
  md2cf publish /workspace/doc.md --space DEMO --title "Doc"
```

## 📊 Vergleich: Native vs. Docker

| Aspekt | Native Installation | Docker CLI |
|--------|-------------------|------------|
| **Installation** | `pip install` erforderlich | Nur Docker erforderlich |
| **Abhängigkeiten** | Python 3.8+ lokal | Alles im Image enthalten |
| **Updates** | `pip install -U` | `docker pull` |
| **Isolation** | Nutzt System Python | Komplett isoliert |
| **Performance** | Schneller (kein Container-Overhead) | Minimal langsamer |
| **Portabilität** | OS-abhängig | Läuft überall wo Docker läuft |

## 🎯 Use Cases

### Ideal für Docker CLI:

✅ **CI/CD Pipelines**: Automatisches Publizieren nach Builds
✅ **Mehrere Projekte**: Jedes Projekt nutzt eigenes Image/Version
✅ **Keine Python-Installation**: Server ohne Python
✅ **Konsistente Umgebung**: Gleiche Version überall
✅ **Team-Nutzung**: Jeder nutzt dieselbe Version

### Ideal für Native:

✅ **Entwicklung**: Schnelleres Feedback
✅ **Lokale Scripts**: Direkte Integration in Shell-Scripts
✅ **Geringe Latenz**: Keine Container-Startup-Zeit
✅ **Python-Projekt**: Bereits Python-Umgebung vorhanden

## 🔗 Nächste Schritte

1. **Image bauen**: `docker build -t md2cf-api .`
2. **Testen**: Siehe [DOCKER_CLI_QUICK_REFERENCE.md](DOCKER_CLI_QUICK_REFERENCE.md)
3. **Alias erstellen**: Für einfachere Nutzung
4. **Workflow einrichten**: Z.B. in CI/CD Pipeline

## 📚 Dokumentation

- **Quick Start**: [DOCKER_CLI_QUICK_REFERENCE.md](DOCKER_CLI_QUICK_REFERENCE.md)
- **Ausführlich**: [DOCKER_CLI_USAGE.md](DOCKER_CLI_USAGE.md)
- **Allgemein**: [README.md](README.md)
- **REST API**: [DOCKER.md](DOCKER.md)

## ✨ Vorteile der Implementierung

1. ✅ **Rückwärtskompatibel**: REST API funktioniert wie vorher
2. ✅ **Flexibel**: Beide Modi in einem Image
3. ✅ **Einfach**: Automatische Modus-Erkennung
4. ✅ **Dokumentiert**: Umfangreiche Docs & Beispiele
5. ✅ **Getestet**: Beide Modi funktional

---

**Fragen?** Siehe die ausführliche Dokumentation oder öffne ein Issue.
