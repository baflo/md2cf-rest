# OpenAPI Schema Automatisierung

Dieses Dokument beschreibt alle Möglichkeiten, die OpenAPI-Schema-Generierung nach Änderungen an den API-Endpunkten zu automatisieren.

## 📋 Übersicht

Es gibt 5 Hauptansätze zur Automatisierung:

1. **Manueller Export** - Für schnelle Updates
2. **Makefile-Targets** - Für Entwickler-Workflow
3. **File Watcher** - Für automatisches Export bei Änderungen
4. **Git Pre-Commit Hooks** - Für automatisches Commit
5. **CI/CD Pipeline** - Für automatische Validierung und Deployment

---

## 1. Manueller Export

### Mit Python-Script

```bash
# Einfacher Export
python scripts/export-openapi.py

# Mit benutzerdefiniertem Dateinamen
python scripts/export-openapi.py my-schema.json
```

### Mit curl (Server muss laufen)

```bash
# Server starten
uvicorn md2cf.rest_api:app --port 8000 &

# Schema exportieren
curl http://localhost:8000/openapi.json > openapi.json
```

### Vorteile
- ✅ Einfach und schnell
- ✅ Keine zusätzlichen Dependencies

### Nachteile
- ❌ Manueller Prozess
- ❌ Leicht zu vergessen

---

## 2. Makefile-Targets

### Verfügbare Commands

```bash
# Hilfe anzeigen
make help

# OpenAPI Schema exportieren
make export-openapi

# Schema validieren
make validate-openapi

# Clients generieren (exportiert automatisch Schema)
make generate-clients
```

### Integration in Workflow

```bash
# Nach Änderungen an rest_api.py
make export-openapi

# Kompletter Build-Prozess
make format lint test export-openapi
```

### Vorteile
- ✅ Einfach zu merken
- ✅ Teil des Standard-Workflows
- ✅ Kombinierbar mit anderen Tasks

### Nachteile
- ❌ Immer noch manuell
- ❌ Entwickler muss daran denken

---

## 3. File Watcher (Automatisch)

### Installation

```bash
pip install watchdog
```

### Verwendung

```bash
# Watcher starten
make watch-api

# Oder direkt:
python scripts/watch-and-export.py
```

### Was passiert?

1. Script überwacht `md2cf/rest_api.py`
2. Bei Änderungen: Automatischer Export nach `openapi.json`
3. Konsolen-Ausgabe bei jedem Update

```
👀 Watching for changes in REST API...
📁 Monitoring: /path/to/md2cf/rest_api.py
💾 Output: /path/to/openapi.json

Press Ctrl+C to stop

✅ OpenAPI schema updated: openapi.json
   Version: 0.1.0
   Endpoints: 4

🔄 Detected change in rest_api.py
✅ OpenAPI schema updated: openapi.json
   Version: 0.1.0
   Endpoints: 4
```

### Vorteile
- ✅ Vollautomatisch
- ✅ Sofortiges Feedback
- ✅ Ideal für Entwicklung

### Nachteile
- ❌ Muss im Hintergrund laufen
- ❌ Zusätzliche Dependency (watchdog)

---

## 4. Git Pre-Commit Hook

### Installation

```bash
# Automatisch mit Makefile
make setup-hooks

# Oder manuell
mkdir -p .git/hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
make export-openapi
git add openapi.json
EOF
chmod +x .git/hooks/pre-commit
```

### Was passiert?

Bei jedem `git commit`:

1. OpenAPI Schema wird automatisch exportiert
2. Änderungen werden zum Commit hinzugefügt
3. Commit wird fortgesetzt

```bash
# Normal committen
git add md2cf/rest_api.py
git commit -m "Add new endpoint"

# Hook läuft automatisch:
# Exporting OpenAPI schema...
# ✅ Done
# [main abc1234] Add new endpoint
#  2 files changed, 50 insertions(+)
```

### Vorteile
- ✅ Automatisch bei jedem Commit
- ✅ Schema immer aktuell im Git
- ✅ Kein manueller Schritt nötig

### Nachteile
- ❌ Verlangsamt Commits leicht
- ❌ Nur lokal (muss auf jedem Rechner installiert werden)

### Alternative: pre-commit Framework

```bash
# Installation
pip install pre-commit

# .pre-commit-config.yaml erstellen
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: local
    hooks:
      - id: export-openapi
        name: Export OpenAPI Schema
        entry: python scripts/export-openapi.py openapi.json
        language: system
        pass_filenames: false
        files: md2cf/rest_api.py
EOF

# Installieren
pre-commit install
```

---

## 5. CI/CD Pipeline (GitHub Actions)

### Automatische Schema-Generierung

Die Datei `.github/workflows/openapi-export.yml` wurde bereits erstellt.

### Was passiert?

**Bei Push zu main/develop:**
1. API Dependencies installieren
2. OpenAPI Schema exportieren
3. Schema validieren
4. Bei Änderungen: Automatisch committen
5. Als Artifact hochladen

**Bei Pull Request:**
1. Schema exportieren und validieren
2. PR-Kommentar bei Änderungen
3. Artifact bereitstellen

### Workflow triggern

```bash
# Push zu main
git push origin main

# Bei Änderungen an:
# - md2cf/rest_api.py
# - md2cf/converter.py
# - md2cf/api/confluence.py
```

### Vorteile
- ✅ Zentral und automatisch
- ✅ Validierung für alle
- ✅ Keine lokale Installation nötig
- ✅ Artifacts für Download

### Nachteile
- ❌ Nur auf GitHub
- ❌ Läuft erst nach Push

### Alternative: GitLab CI

```yaml
# .gitlab-ci.yml
export-openapi:
  stage: build
  image: python:3.12
  script:
    - pip install -e ".[rest]"
    - python scripts/export-openapi.py openapi.json
  artifacts:
    paths:
      - openapi.json
    expire_in: 30 days
  only:
    changes:
      - md2cf/rest_api.py
```

---

## 6. Kombination mehrerer Ansätze

### Empfohlener Development-Workflow

```bash
# 1. Setup (einmalig)
make setup-hooks          # Git Hooks installieren
pip install watchdog      # Für File Watcher

# 2. Entwicklung
make watch-api           # Im Hintergrund laufen lassen
make server             # API Server starten

# 3. Änderungen machen
vim md2cf/rest_api.py   # Watcher exportiert automatisch

# 4. Commit
git add .
git commit -m "..."     # Hook exportiert nochmal

# 5. Push
git push                # CI/CD validiert
```

### Für Teams

1. **Lokal**: File Watcher während Entwicklung
2. **Git**: Pre-commit Hook für Konsistenz
3. **CI/CD**: Automatische Validierung und Artifacts

---

## 7. VS Code Integration

### tasks.json

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Export OpenAPI Schema",
      "type": "shell",
      "command": "python scripts/export-openapi.py openapi.json",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": false
      }
    },
    {
      "label": "Watch API Changes",
      "type": "shell",
      "command": "python scripts/watch-and-export.py",
      "isBackground": true,
      "problemMatcher": []
    }
  ]
}
```

### Keyboard Shortcut

```json
// keybindings.json
[
  {
    "key": "ctrl+shift+e",
    "command": "workbench.action.tasks.runTask",
    "args": "Export OpenAPI Schema"
  }
]
```

---

## 8. Docker Integration

### Development Container

```dockerfile
# .devcontainer/Dockerfile
FROM python:3.12

WORKDIR /workspace

COPY requirements.txt .
RUN pip install -e ".[dev,rest]" watchdog

# Auto-export beim Container-Start
CMD ["python", "scripts/watch-and-export.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/workspace
    command: uvicorn md2cf.rest_api:app --host 0.0.0.0 --reload

  watcher:
    build: .
    volumes:
      - .:/workspace
    command: python scripts/watch-and-export.py
```

---

## 9. Monitoring & Validierung

### Schema-Validierung

```bash
# Nach Export validieren
make validate-openapi

# Oder manuell
python -c "
import json
from jsonschema import validate

schema = json.load(open('openapi.json'))
print(f'✅ Valid OpenAPI {schema[\"openapi\"]} Schema')
print(f'   Title: {schema[\"info\"][\"title\"]}')
print(f'   Version: {schema[\"info\"][\"version\"]}')
print(f'   Endpoints: {len(schema[\"paths\"])}')
"
```

### Schema-Diff bei Änderungen

```bash
# Vor Änderungen
cp openapi.json openapi.json.old

# Nach Änderungen
make export-openapi

# Diff anzeigen
diff -u openapi.json.old openapi.json

# Oder mit jq
diff <(jq -S . openapi.json.old) <(jq -S . openapi.json)
```

---

## 10. Troubleshooting

### Schema wird nicht aktualisiert

```bash
# Server neu starten
pkill -f uvicorn
make server

# Cache löschen
find . -type d -name __pycache__ -exec rm -rf {} +
python scripts/export-openapi.py openapi.json
```

### Watcher funktioniert nicht

```bash
# Watchdog neu installieren
pip install --upgrade watchdog

# Manuell testen
python -c "from watchdog.observers import Observer; print('✅ OK')"
```

### Git Hook läuft nicht

```bash
# Permissions prüfen
ls -l .git/hooks/pre-commit

# Hook neu installieren
make setup-hooks

# Manuell testen
.git/hooks/pre-commit
```

---

## Zusammenfassung

| Methode | Automatisch | Setup | Empfohlen für |
|---------|-------------|-------|---------------|
| Manueller Export | ❌ | Einfach | Schnelle Tests |
| Makefile | ❌ | Einfach | Standard-Workflow |
| File Watcher | ✅ | Mittel | Entwicklung |
| Git Hooks | ✅ | Einfach | Teams |
| CI/CD | ✅ | Komplex | Production |

### Beste Kombination

```bash
# Setup (einmalig)
make setup-hooks              # Git Hooks
pip install watchdog         # File Watcher

# Entwicklung (täglich)
make watch-api &            # Automatischer Export
make server                 # API entwickeln

# Production (automatisch via CI/CD)
# → GitHub Actions validiert und published
```
