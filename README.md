# md2cf - Markdown to Confluence Converter

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Konvertiere Markdown-Dateien zu Confluence Storage Format und publiziere sie direkt zu Confluence mit Personal Access Token (PAT) Authentifizierung.

## Features

- 🚀 **REST API & CLI**: Web-Service oder Command-Line Interface
- 🔐 **PAT Authentication**: Sichere Authentifizierung mit Personal Access Tokens
- 📝 **Full Markdown Support**: Headings, Lists, Code Blocks, Tables, Links, Images, Task Lists
- 🔄 **Frontmatter Workflow**: Download → Edit → Re-publish mit automatischem Versioning
- 🐳 **Docker Support**: Läuft out-of-the-box mit Docker
- 🔗 **Jira Integration**: Automatische Konvertierung von Jira-Links zu Macros
- 📎 **Attachments**: Upload von Bildern und Dateien
- 🌳 **PlantUML Support**: Diagramme als Confluence Macros

## Quick Start

### Docker (Empfohlen)

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

**Weitere Informationen:**
- [Docker Usage Guide](docs/docker.md) - Umfassende Docker-Dokumentation
- [REST API Dokumentation](docs/rest-api.md) - Web-Service nutzen

### Native Installation

```bash
# Installation
pip install -e .

# Publish
md2cf publish README.md \
  --url https://your-domain.atlassian.net \
  --token YOUR_PAT_TOKEN \
  --space DEMO \
  --title "My Documentation"

# Convert only
md2cf convert README.md -o output.html

# Download existing page
md2cf download-source 123456
```

## Frontmatter Workflow

md2cf unterstützt einen Round-Trip Workflow:

```bash
# 1. Download: Lädt Seite mit Frontmatter herunter
md2cf download-source 123456
# Erstellt: My_Page_Title.md mit Metadaten (page_id, version, etc.)

# 2. Edit: Bearbeite Markdown lokal
vim My_Page_Title.md

# 3. Re-publish: Automatisches Update mit korrekter Version
md2cf publish My_Page_Title.md
# Frontmatter wird automatisch aktualisiert
```

**Frontmatter Beispiel:**
```yaml
---
confluence_page_id: "123456"
confluence_space_key: "DEMO"
confluence_title: "My Page"
confluence_version: 5
confluence_parent_id: "654321"
---
# My Page Content

Your markdown here...
```

## REST API

Starte den Web-Service:

```bash
# Docker
docker run -p 8000:8000 md2cf

# Native
uvicorn md2cf.rest_api:app --host 0.0.0.0 --port 8000
```

API Dokumentation: http://localhost:8000/docs

**Wichtige Endpoints:**
- `POST /convert` - Konvertiere Markdown zu Confluence Format
- `POST /publish` - Publiziere zu Confluence (mit Attachments)
- `POST /spaces` - Liste verfügbare Spaces
- `POST /search-pages` - Suche nach Pages

Siehe [REST API Docs](docs/rest-api.md) für Details.

## Unterstützte Markdown Features

| Feature | Markdown | Confluence Output |
|---------|----------|-------------------|
| **Bold** | `**text**` | `<strong>text</strong>` |
| *Italic* | `*text*` | `<em>text</em>` |
| Code | `` `code` `` | `<code>code</code>` |
| Headings | `# H1` | `<h1>H1</h1>` |
| Lists | `- item` | `<ul><li>item</li></ul>` |
| Code Blocks | ` ```python ` | Confluence Code Macro |
| Tables | Markdown Table | HTML Table |
| Links | `[text](url)` | `<a href="url">text</a>` |
| Images | `![alt](url)` | Confluence Image Macro |
| Task Lists | `- [x] Done` | Confluence Task Macro |
| Blockquotes | `> quote` | `<blockquote>` |
| PlantUML | ` ```plantuml ` | Confluence PlantUML Macro |
| Jira Links | `[PROJ-123](jira-url)` | Confluence Jira Macro |

## Umgebungsvariablen

```bash
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_TOKEN="your-personal-access-token"
export CONFLUENCE_SPACE="DEMO"  # Optional: Default Space
export JIRA_URL="https://jira.example.com"  # Optional: Jira Link Conversion
```

## Personal Access Token erstellen

### Confluence Cloud

1. Confluence → **Settings** → **Personal Access Tokens**
2. **Create token**
3. Name eingeben, Ablaufdatum wählen
4. Token kopieren (wird nur einmal angezeigt!)

### Confluence Server/Data Center

1. Confluence → **Settings** → **Personal Access Tokens**
2. **Create token** (Admin-Rechte erforderlich)
3. Token kopieren

## Dokumentation

- 📚 [Quick Start Guide](docs/quickstart.md) - Schnelleinstieg
- 🐳 [Docker Usage](docs/docker.md) - Docker CLI & Compose
- 🌐 [REST API](docs/rest-api.md) - Web Service API
- 🧪 [Testing Guide](docs/testing.md) - Tests ausführen
- 🤝 [Contributing](docs/contributing.md) - Beitragen zum Projekt

## Development

```bash
# Installation
pip install -e ".[dev]"

# Tests ausführen
pytest

# Mit Coverage
pytest --cov=md2cf --cov-report=html

# Code formatieren
black md2cf tests
isort md2cf tests

# Type checking
mypy md2cf
```

Siehe [Testing Guide](docs/testing.md) für Details.

## Troubleshooting

### Authentication Errors

```bash
# PAT überprüfen
echo $CONFLUENCE_TOKEN

# Permissions testen
md2cf publish test.md --space DEMO --title "Test"
```

### SSL Certificate Errors

```bash
md2cf publish document.md --no-verify-ssl
```

### Version Conflicts

```bash
# Download aktuelle Version
md2cf download-source 123456

# Bearbeiten und re-publish
md2cf publish Downloaded_Page.md
```

## Project Structure

```
md2cf/
├── md2cf/                    # Source code
│   ├── api/                  # Confluence API client
│   ├── renderers/            # Confluence renderer
│   ├── utils/                # Utilities (frontmatter)
│   ├── cli.py                # CLI interface
│   ├── converter.py          # Markdown converter
│   └── rest_api.py           # REST API
├── tests/                    # Test suite (149 tests, 77% coverage)
├── docs/                     # Documentation
├── examples/                 # Example files
├── Dockerfile                # Docker image
└── pyproject.toml            # Project configuration
```

## License

MIT License - siehe LICENSE file für Details.

## Acknowledgments

- [Mistune](https://github.com/lepture/mistune) - Markdown Parser
- [FastAPI](https://fastapi.tiangolo.com/) - Web Framework
- [atlassian-python-api](https://github.com/atlassian-api/atlassian-python-api) - Atlassian API

---

**Made with ❤️ using Python, Mistune & FastAPI**
