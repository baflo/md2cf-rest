# Quick Start Guide

Dieses Guide hilft Ihnen, das md2cf-Projekt in wenigen Schritten zum Laufen zu bringen.

## Installation

### 1. Python Virtual Environment erstellen

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# oder
venv\Scripts\activate     # Windows
```

### 2. Projekt installieren

```bash
# Für normale Nutzung
pip install -e .

# Für Entwicklung (mit Tests, Linting, etc.)
pip install -e ".[dev]"
```

### 3. Installation überprüfen

```bash
# Zeige Hilfe
md2cf --help

# Teste Konvertierung
echo "# Test" > test.md
md2cf convert test.md
```

## Erste Schritte

### Markdown konvertieren

```bash
# Einfache Konvertierung
md2cf convert examples/sample.md

# In Datei speichern
md2cf convert examples/sample.md -o output.html
```

### Nach Confluence publizieren

1. **Personal Access Token erstellen** in Confluence:
   - Settings → Personal Access Tokens → Create token

2. **Umgebungsvariablen setzen**:

```bash
export CONFLUENCE_URL="https://yoursite.atlassian.net"
export CONFLUENCE_TOKEN="your_pat_token_here"
export CONFLUENCE_SPACE="DEMO"
```

3. **Publizieren**:

```bash
md2cf publish examples/sample.md \
  --url $CONFLUENCE_URL \
  --token $CONFLUENCE_TOKEN \
  --space $CONFLUENCE_SPACE \
  --title "Meine Dokumentation"
```

## Python API verwenden

```python
from md2cf import MarkdownToConfluence

# Markdown konvertieren
converter = MarkdownToConfluence()
result = converter.convert("# Hallo Welt\n\nDas ist **fett**.")
print(result)
```

## Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=md2cf --cov-report=html

# Bestimmte Tests
pytest tests/test_converter.py
```

## Entwicklung

```bash
# Code formatieren
make format

# Linting
make lint

# Tests
make test

# Alles aufräumen
make clean
```

## Beispiele erkunden

```bash
# Beispiel Markdown ansehen
cat examples/sample.md

# Beispiel Python Script
python examples/api_usage.py
```

## Häufige Probleme

### Import Error

Falls `ImportError: No module named 'md2cf'`:

```bash
pip install -e .
```

### Confluence API Fehler

Falls Authentication Error:
- Token überprüfen
- URL überprüfen (mit https://)
- Permissions im Confluence Space prüfen

## Nächste Schritte

- Lesen Sie das vollständige [README.md](README.md)
- Schauen Sie sich [CONTRIBUTING.md](CONTRIBUTING.md) an
- Erkunden Sie die [Beispiele](examples/)

## Hilfe bekommen

Bei Fragen:
- GitHub Issues öffnen
- Dokumentation lesen
- Beispiele studieren
