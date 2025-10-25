# md2cf Tests

Umfassende Test-Suite für das md2cf Projekt.

## Test-Struktur

```
tests/
├── conftest.py                 # Pytest-Konfiguration und gemeinsame Fixtures
├── test_frontmatter.py         # Tests für Frontmatter-Utilities
├── test_cli.py                 # Tests für CLI-Befehle
├── test_rest_api.py            # Tests für REST API Endpoints
├── test_converter.py           # Tests für Markdown-Konverter
├── test_renderer.py            # Tests für Confluence-Renderer
├── test_confluence_api.py      # Tests für Confluence API Client
└── test_integration.py         # Integration und End-to-End Tests
```

## Tests ausführen

### Alle Tests ausführen

```bash
pytest
```

### Bestimmte Test-Datei ausführen

```bash
pytest tests/test_frontmatter.py
```

### Tests mit Verbose-Output

```bash
pytest -v
```

### Tests mit Coverage-Report

```bash
pytest --cov=md2cf --cov-report=html
```

### Nur Unit-Tests (ohne Integration-Tests)

```bash
pytest -k "not integration"
```

### Nur Integration-Tests

```bash
pytest -k "integration"
```

### Nur API-Tests

```bash
pytest -m api
```

### Nur CLI-Tests

```bash
pytest -m cli
```

## Test-Kategorien

### Unit Tests

- **test_frontmatter.py**: Tests für YAML Frontmatter-Parsing und -Serialisierung
  - FrontmatterMetadata Klasse
  - extract_frontmatter Funktion
  - add_frontmatter Funktion
  - parse_frontmatter_metadata Funktion

- **test_converter.py**: Tests für Markdown zu Confluence Konvertierung
  - Basis-Konvertierung (Headings, Paragraphen, etc.)
  - Code-Blöcke
  - Listen
  - Links und Bilder
  - Tabellen
  - Task Lists
  - Blockquotes

- **test_renderer.py**: Tests für den Confluence-Renderer
  - HTML-Generierung
  - Confluence-Macros
  - XHTML-Validierung

- **test_confluence_api.py**: Tests für den Confluence API Client
  - Seitenoperationen (erstellen, aktualisieren, löschen)
  - Space-Operationen
  - Attachment-Operationen

### CLI Tests

- **test_cli.py**: Tests für Command-Line Interface
  - `convert` Befehl
  - `publish` Befehl
  - `download-attachment` Befehl
  - `download-source` Befehl
  - Argument-Parsing
  - Frontmatter-Integration

### API Tests

- **test_rest_api.py**: Tests für REST API Endpoints
  - Health Check Endpoints
  - Convert Endpoint
  - Publish Endpoint (mit/ohne Attachments)
  - Spaces Endpoint
  - Pages Endpoint
  - Search Endpoint

### Integration Tests

- **test_integration.py**: End-to-End Workflow Tests
  - Kompletter Frontmatter-Workflow (Download → Edit → Publish)
  - Markdown-Konvertierung mit Bildern
  - Jira-Link-Konvertierung
  - PlantUML-Diagramme
  - REST API mit mehreren Attachments
  - Fehlerbehandlung

## Fixtures

### Allgemeine Fixtures (in conftest.py)

- `temp_dir`: Temporäres Verzeichnis für Tests
- `sample_markdown`: Beispiel-Markdown-Content
- `sample_markdown_with_frontmatter`: Markdown mit Frontmatter
- `sample_confluence_html`: Beispiel Confluence HTML
- `mock_confluence_client`: Mock Confluence Client
- `mock_confluence_page`: Mock Confluence Page Objekt
- `temp_markdown_file`: Temporäre Markdown-Datei
- `temp_markdown_file_with_frontmatter`: Temporäre Datei mit Frontmatter

## Test-Abdeckung

Aktuelle Test-Abdeckung für Hauptmodule (Stand: aktuell):

- `md2cf/utils/frontmatter.py`: **100%** ✅
- `md2cf/renderers/confluence.py`: **89%** ✅
- `md2cf/rest_api.py`: **88%** ✅
- `md2cf/cli.py`: **80%** ✅
- `md2cf/converter.py`: **79%** ✅
- `md2cf/api/confluence.py`: **36%** ⚠️

**Gesamt-Abdeckung: 77%** ✅

Ziel: >80% Code-Abdeckung für alle Module (fast erreicht!)

### Aktuelle Test-Ergebnisse

**Gesamt: 149 Tests**
- ✅ **149 Tests erfolgreich** (100% Erfolgsquote) 🎉
- ❌ 0 Tests fehlgeschlagen

**Alle Tests bestehen!** 🎊

Die Test-Suite deckt alle wichtigen Funktionalitäten ab:
- ✅ Frontmatter-Utilities (100% Coverage)
- ✅ CLI-Befehle (80% Coverage)
- ✅ REST API Endpoints (88% Coverage)
- ✅ Markdown zu Confluence Konvertierung (79% Coverage)
- ✅ Confluence Renderer (89% Coverage)
- ✅ Integration Tests für komplette Workflows

## Kontinuierliche Integration

Tests werden automatisch ausgeführt bei:
- Git pre-commit Hook (falls konfiguriert)
- Docker Build
- CI/CD Pipeline (falls konfiguriert)

## Test-Entwicklung

### Neue Tests hinzufügen

1. Erstelle eine neue Test-Datei im `tests/` Verzeichnis
2. Importiere notwendige Fixtures aus `conftest.py`
3. Verwende aussagekräftige Test-Namen (z.B. `test_something_when_condition_then_expected`)
4. Gruppiere verwandte Tests in Klassen
5. Nutze Pytest Markers für Kategorisierung

```python
import pytest

class TestMyFeature:
    """Test my feature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        ...
        # Act
        ...
        # Assert
        ...

    @pytest.mark.integration
    def test_integration_scenario(self):
        """Test integration scenario."""
        ...
```

### Best Practices

- **Arrange-Act-Assert**: Strukturiere Tests klar
- **Isolation**: Tests sollten unabhängig voneinander sein
- **Mocking**: Verwende Mocks für externe Abhängigkeiten
- **Fixtures**: Nutze Fixtures für wiederverwendbare Test-Daten
- **Markers**: Markiere Tests nach Typ (integration, slow, api, cli)
- **Docstrings**: Dokumentiere, was der Test prüft

## Troubleshooting

### Import-Fehler

Wenn Module nicht gefunden werden:

```bash
# Installiere das Projekt in Entwicklungsmodus
pip install -e .

# Installiere Test-Dependencies
pip install -e ".[dev]"
```

### Fixture-Fehler

Stelle sicher, dass `conftest.py` im Tests-Verzeichnis liegt und korrekt importiert werden kann.

### Pydantic-Warnungen

Die Pydantic-Warnungen über deprecated `Config` können ignoriert werden. Sie werden in einer zukünftigen Version behoben.

## Weitere Informationen

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
