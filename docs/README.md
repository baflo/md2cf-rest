# md2cf Documentation

Willkommen zur md2cf Dokumentation! Hier finden Sie alle Anleitungen und Referenzen.

## 📚 Dokumentationsübersicht

### Getting Started

- **[Quick Start Guide](quickstart.md)** - Schnelleinstieg in 5 Minuten
  - Installation
  - Erste Schritte
  - Häufige Use Cases

### Usage Guides

- **[Docker Usage](docker.md)** - Docker CLI & Compose
  - Linux/macOS CLI Befehle
  - Windows PowerShell
  - Helper Funktionen
  - Docker Compose Setup

- **[REST API](rest-api.md)** - Web Service API
  - API Endpoints
  - Request/Response Modelle
  - Beispiele mit curl & PowerShell
  - Client Libraries

### Development

- **[Testing Guide](testing.md)** - Tests ausführen und schreiben
  - Test-Struktur
  - Test ausführen
  - Coverage Reports
  - Neue Tests schreiben

- **[Contributing](contributing.md)** - Zum Projekt beitragen
  - Development Setup
  - Code Style
  - Pull Request Prozess

## 🚀 Quick Links

### Für Anwender

```bash
# Docker: Dokument publizieren
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf publish /workspace/README.md --space DEMO --title "Doc"

# Native: Installation
pip install -e .
md2cf publish README.md --space DEMO --title "Doc"

# REST API: Server starten
docker run -p 8000:8000 md2cf
# Dann: http://localhost:8000/docs
```

### Für Entwickler

```bash
# Development Setup
pip install -e ".[dev]"

# Tests ausführen
pytest --cov=md2cf

# Code formatieren
black md2cf tests
isort md2cf tests
```

## 📋 Features im Überblick

| Feature | Status | Dokumentation |
|---------|--------|---------------|
| Markdown Konvertierung | ✅ | [Quick Start](quickstart.md) |
| CLI Publish | ✅ | [Docker](docker.md) |
| REST API | ✅ | [REST API](rest-api.md) |
| Frontmatter Workflow | ✅ | [Quick Start](quickstart.md) |
| Docker Support | ✅ | [Docker](docker.md) |
| Jira Integration | ✅ | [Quick Start](quickstart.md) |
| PlantUML Diagramme | ✅ | [Quick Start](quickstart.md) |
| Attachments | ✅ | [REST API](rest-api.md) |
| Task Lists | ✅ | [Quick Start](quickstart.md) |

## 🧪 Test Suite

- **149 Tests** (100% Erfolgsquote)
- **77% Code Coverage**
- Siehe [Testing Guide](testing.md) für Details

## 🤝 Support & Community

- **Issues**: [GitHub Issues](https://github.com/yourusername/md2cf/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/md2cf/discussions)
- **Contributing**: Siehe [Contributing Guide](contributing.md)

## 📖 Weitere Ressourcen

- [Confluence Storage Format Documentation](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [Confluence Cloud REST API](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/)
- [Mistune Documentation](https://mistune.lepture.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
