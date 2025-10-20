# md2cf - Projekt Zusammenfassung

## Projektübersicht

Ein vollständiges, idiomatisches Python-Projekt zur Konvertierung von Markdown zu Confluence Storage Format mit PAT-Authentifizierung.

## Projektstruktur

```
md2cf/
├── .github/
│   └── workflows/
│       └── test.yml              # GitHub Actions CI/CD
├── md2cf/                        # Hauptpaket
│   ├── __init__.py              # Package exports
│   ├── converter.py             # Markdown→Confluence Converter
│   ├── cli.py                   # Command-line Interface
│   ├── api/
│   │   ├── __init__.py
│   │   └── confluence.py        # Confluence REST API Client
│   ├── renderers/
│   │   ├── __init__.py
│   │   └── confluence.py        # Mistune Custom Renderer
│   └── utils/
│       └── __init__.py
├── tests/                        # Test Suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest Konfiguration
│   ├── test_renderer.py         # Renderer Tests
│   ├── test_converter.py        # Converter Tests
│   └── test_confluence_api.py   # API Client Tests
├── examples/                     # Beispiele
│   ├── sample.md                # Beispiel Markdown
│   └── api_usage.py             # Python API Beispiele
├── pyproject.toml               # Moderne Python Projektkonfiguration
├── Makefile                      # Entwicklungs-Shortcuts
├── README.md                     # Hauptdokumentation
├── QUICKSTART.md                 # Schnellstart-Guide
├── CONTRIBUTING.md               # Contribution Guidelines
├── LICENSE                       # MIT License
├── .gitignore                   # Git Ignore
└── .env.example                 # Umgebungsvariablen Template
```

## Kernkomponenten

### 1. Mistune Custom Renderer (md2cf/renderers/confluence.py)
- **309 Zeilen**
- Konvertiert Markdown AST → Confluence Storage Format
- Unterstützt: Headings, Listen, Code, Tabellen, Links, Bilder, Quotes
- Vollständig typisiert mit Type Hints

### 2. Confluence API Client (md2cf/api/confluence.py)
- **309 Zeilen**  
- REST API Integration mit PAT-Authentifizierung
- Methoden: create, update, delete, get pages
- Cloud & Server/Data Center Support

### 3. Converter Modul (md2cf/converter.py)
- **139 Zeilen**
- Hauptklasse: MarkdownToConfluence
- Methoden: convert(), convert_file(), convert_and_save()
- Mistune Integration mit Plugins

### 4. CLI Interface (md2cf/cli.py)
- **321 Zeilen**
- Befehle: convert, publish
- Argparse-basiert
- Umgebungsvariablen-Support

### 5. Test Suite (tests/)
- **741 Zeilen Tests**
- Pytest-basiert mit Fixtures
- Unit Tests für alle Komponenten
- Mocking für API-Tests
- Coverage-optimiert

## Features

### Markdown Support
- ✅ Headings (H1-H6)
- ✅ Text Formatting (bold, italic, strikethrough)
- ✅ Code Blocks mit Syntax Highlighting
- ✅ Inline Code
- ✅ Listen (ordered, unordered, nested)
- ✅ Links
- ✅ Images
- ✅ Tables mit Alignment
- ✅ Blockquotes
- ✅ Horizontal Rules

### Technische Features
- ✅ Type Hints (mypy kompatibel)
- ✅ Docstrings (Google Style)
- ✅ Logging
- ✅ Error Handling
- ✅ CLI mit argparse
- ✅ Environment Variables
- ✅ Comprehensive Tests
- ✅ Code Formatting (Black, isort)
- ✅ Linting (Ruff)
- ✅ CI/CD (GitHub Actions)

## Verwendung

### Installation
```bash
pip install -e .              # Normal
pip install -e ".[dev]"       # Development
```

### CLI
```bash
# Konvertieren
md2cf convert document.md -o output.html

# Publizieren
md2cf publish document.md \
  --url https://site.atlassian.net \
  --token TOKEN \
  --space DEMO
```

### Python API
```python
from md2cf import MarkdownToConfluence
from md2cf.api.confluence import ConfluenceClient

# Konvertieren
converter = MarkdownToConfluence()
html = converter.convert("# Titel\n\nText")

# Publizieren
client = ConfluenceClient(url="...", token="...")
page = client.create_or_update_page(
    space="DEMO",
    title="Meine Seite", 
    body=html
)
```

## Entwicklung

### Setup
```bash
make install-dev
```

### Workflow
```bash
make format     # Black + isort
make lint       # Ruff + mypy
make test       # pytest
make test-cov   # pytest mit Coverage
make clean      # Aufräumen
```

### Tests ausführen
```bash
pytest                          # Alle Tests
pytest --cov=md2cf             # Mit Coverage
pytest tests/test_converter.py # Spezifisch
```

## Abhängigkeiten

### Core Dependencies
- **mistune** (>=3.0.0) - Markdown Parser
- **atlassian-python-api** (>=3.41.0) - Confluence API
- **requests** (>=2.31.0) - HTTP Client

### Dev Dependencies
- **pytest** (>=7.4.0) - Testing
- **pytest-cov** (>=4.1.0) - Coverage
- **black** (>=23.7.0) - Formatting
- **isort** (>=5.12.0) - Import Sorting
- **mypy** (>=1.5.0) - Type Checking
- **ruff** (>=0.0.285) - Linting

## Code-Qualität

### Metriken
- **~1400 Zeilen** Production Code
- **~750 Zeilen** Test Code
- **Test Coverage**: Ziel 90%+
- **Type Coverage**: 100% mit mypy
- **Formatting**: Black (line-length: 100)

### Standards
- PEP 8 konform
- Google-Style Docstrings
- Type Hints überall
- Comprehensive Tests
- CI/CD Pipeline

## Dokumentation

1. **README.md** - Vollständige Dokumentation
2. **QUICKSTART.md** - Schnellstart-Guide
3. **CONTRIBUTING.md** - Entwickler-Guide
4. **Docstrings** - Inline Dokumentation
5. **Examples** - Praktische Beispiele

## Lizenz

MIT License - siehe LICENSE Datei

## Nächste Schritte

### Mögliche Erweiterungen
- [ ] Attachment Upload Support
- [ ] Template System
- [ ] Batch Processing
- [ ] Configuration File Support
- [ ] Page Hierarchy Management
- [ ] Confluence Macros Support
- [ ] Markdown Extensions
- [ ] Interactive Mode

### Verbesserungen
- [ ] Async API Support
- [ ] Caching
- [ ] Rate Limiting
- [ ] Retry Logic
- [ ] Progress Bars
- [ ] Dry-run Mode

## Autor & Contribution

Contributions willkommen! Siehe CONTRIBUTING.md für Details.

---
Erstellt: 2025
Python: 3.8+
Framework: Mistune + atlassian-python-api
