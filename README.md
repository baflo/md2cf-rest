# md2cf - Markdown to Confluence Converter

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Convert Markdown files to Confluence Storage Format and publish them directly to Confluence using the REST API with Personal Access Token (PAT) authentication.

## Features

- **Custom Mistune Renderer**: Converts Markdown to Confluence Storage Format (XHTML)
- **PAT Authentication**: Secure authentication using Personal Access Tokens
- **Full Markdown Support**: Headings, lists, code blocks, tables, links, images, and more
- **CLI Interface**: Easy-to-use command-line interface
- **Python API**: Use as a library in your own projects
- **Type Hints**: Fully typed with mypy support
- **Comprehensive Tests**: Extensive test coverage with pytest

## Installation

### From Source

```bash
git clone https://github.com/yourusername/md2cf.git
cd md2cf
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### Option 1: Docker (Empfohlen)

```bash
# Umgebungsvariablen setzen
export CONFLUENCE_URL="https://yoursite.atlassian.net/wiki"
export CONFLUENCE_TOKEN="YOUR_PAT_TOKEN"

# Dokument publizieren
docker run --rm -v $(pwd):/workspace \
  -e CONFLUENCE_URL -e CONFLUENCE_TOKEN \
  md2cf \
  md2cf publish /workspace/README.md --space DEMO --title "Documentation"
```

**Siehe auch:**
- Linux/macOS: [DOCKER_CLI_QUICK_REFERENCE.md](DOCKER_CLI_QUICK_REFERENCE.md)
- Windows PowerShell: [POWERSHELL_USAGE.md](POWERSHELL_USAGE.md)

### Option 2: Native Installation

#### Convert Markdown to Confluence Format

```bash
# Convert to stdout
md2cf convert README.md

# Convert and save to file
md2cf convert README.md -o output.html
```

#### Publish to Confluence

```bash
md2cf publish README.md \
  --url https://yoursite.atlassian.net \
  --token YOUR_PAT_TOKEN \
  --space DEMO \
  --title "My Documentation"
```

## Usage

### Command-Line Interface

#### Convert Command

Convert Markdown files to Confluence Storage Format:

```bash
# Basic conversion
md2cf convert document.md

# Save to file
md2cf convert document.md -o confluence.html

# Verbose output
md2cf convert document.md -v
```

#### Publish Command

Publish Markdown files directly to Confluence:

```bash
md2cf publish document.md \
  --url https://yoursite.atlassian.net \
  --token YOUR_PAT_TOKEN \
  --space MYSPACE \
  --title "Page Title"
```

**Options:**

- `--url`: Confluence base URL
- `--token`: Personal Access Token
- `--space`: Confluence space key
- `--title`: Page title (optional, defaults to filename)
- `--parent-id`: Parent page ID (optional)
- `--cloud`: Use Confluence Cloud API (default)
- `--server`: Use Confluence Server/Data Center API
- `--no-verify-ssl`: Disable SSL certificate verification

### Python API

#### Basic Conversion

```python
from md2cf import MarkdownToConfluence

# Create converter
converter = MarkdownToConfluence()

# Convert string
markdown = "# Hello\n\nThis is **bold** text."
confluence_html = converter.convert(markdown)
print(confluence_html)

# Convert file
result = converter.convert_file("README.md")

# Convert and save
output_path = converter.convert_and_save("README.md", "output.html")
```

#### Publish to Confluence

```python
from md2cf import MarkdownToConfluence
from md2cf.api.confluence import ConfluenceClient

# Convert Markdown
converter = MarkdownToConfluence()
content = converter.convert_file("documentation.md")

# Initialize Confluence client
client = ConfluenceClient(
    url="https://yoursite.atlassian.net",
    token="YOUR_PAT_TOKEN",
    cloud=True,
)

# Create or update page
page = client.create_or_update_page(
    space="DEMO",
    title="My Documentation",
    body=content,
)

print(f"Page published: {client.get_page_url(page)}")
```

#### Advanced Usage

```python
from md2cf.api.confluence import ConfluenceClient

client = ConfluenceClient(
    url="https://yoursite.atlassian.net",
    token="YOUR_PAT_TOKEN",
)

# Get existing page
page = client.get_page_by_title("DEMO", "Existing Page")
if page:
    print(f"Page ID: {page['id']}")

# Create page with parent
page = client.create_page(
    space="DEMO",
    title="Child Page",
    body="<p>Content</p>",
    parent_id="123456",
)

# Update existing page
client.update_page(
    page_id="123456",
    title="Updated Title",
    body="<p>New content</p>",
)

# Delete page
client.delete_page("123456")
```

## Supported Markdown Features

### Text Formatting

```markdown
**bold text**
*italic text*
~~strikethrough~~
`inline code`
```

### Headings

```markdown
# H1 Heading
## H2 Heading
### H3 Heading
```

### Lists

```markdown
- Unordered list item 1
- Unordered list item 2

1. Ordered list item 1
2. Ordered list item 2
```

### Code Blocks

````markdown
```python
def hello():
    print("Hello, World!")
```
````

### Links and Images

```markdown
[Link text](https://example.com)
![Alt text](https://example.com/image.png)
```

### Tables

```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
```

### Blockquotes

```markdown
> This is a quote
```

## Creating a Personal Access Token

### Confluence Cloud

1. Log in to your Confluence Cloud instance
2. Click on your profile picture → **Settings**
3. Select **Personal Access Tokens**
4. Click **Create token**
5. Enter a name and expiration date
6. Click **Create**
7. Copy the token (you won't be able to see it again)

### Confluence Server/Data Center

1. Log in to your Confluence instance
2. Click on your profile picture → **Settings**
3. Select **Personal Access Tokens** (may require admin privileges)
4. Click **Create token**
5. Copy the token

## Environment Variables

You can use environment variables instead of command-line arguments:

```bash
export CONFLUENCE_URL="https://yoursite.atlassian.net"
export CONFLUENCE_TOKEN="YOUR_PAT_TOKEN"
export CONFLUENCE_SPACE="DEMO"
export JIRA_URL="https://jira.lvm.de/jira"  # Optional, for Jira link conversion

md2cf publish document.md
```

Supported environment variables:
- `CONFLUENCE_URL` - Confluence base URL
- `CONFLUENCE_TOKEN` - Personal Access Token
- `CONFLUENCE_SPACE` - Default space key (optional)
- `JIRA_URL` - Jira base URL for automatic Jira ticket link conversion (optional)

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/md2cf.git
cd md2cf

# Install in development mode
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=md2cf --cov-report=html

# Run specific test file
pytest tests/test_converter.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black md2cf tests

# Sort imports with isort
isort md2cf tests

# Type checking with mypy
mypy md2cf

# Lint with ruff
ruff check md2cf tests
```

## Project Structure

```
md2cf/
├── md2cf/
│   ├── __init__.py
│   ├── converter.py          # Main converter class
│   ├── cli.py                # Command-line interface
│   ├── api/
│   │   ├── __init__.py
│   │   └── confluence.py     # Confluence API client
│   ├── renderers/
│   │   ├── __init__.py
│   │   └── confluence.py     # Confluence renderer
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_renderer.py
│   ├── test_converter.py
│   └── test_confluence_api.py
├── examples/
│   └── sample.md
├── pyproject.toml
├── README.md
└── .gitignore
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write tests for new features
- Update documentation as needed
- Run tests and linting before submitting

## Troubleshooting

### Authentication Errors

If you receive authentication errors:

1. Verify your PAT is correct and not expired
2. Check that your PAT has the necessary permissions
3. Ensure you're using the correct Confluence URL

### SSL Certificate Errors

If you encounter SSL certificate errors:

```bash
md2cf publish document.md --no-verify-ssl \
  --url https://yoursite.atlassian.net \
  --token YOUR_TOKEN --space DEMO
```

### Page Not Found

If the space or page is not found:

1. Verify the space key is correct (case-sensitive)
2. Ensure you have access to the space
3. Check that the page title is exact (for updates)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Mistune](https://github.com/lepture/mistune) - Fast Markdown parser
- [atlassian-python-api](https://github.com/atlassian-api/atlassian-python-api) - Atlassian API wrapper

## Changelog

### Version 0.1.0 (Initial Release)

- Markdown to Confluence Storage Format conversion
- PAT authentication support
- CLI interface for convert and publish commands
- Python API for programmatic usage
- Comprehensive test suite
- Full type hints support

## Support

For bugs and feature requests, please [open an issue](https://github.com/yourusername/md2cf/issues).

## Related Projects

- [mark](https://github.com/kovetskiy/mark) - Go-based Markdown to Confluence converter
- [confluence-publisher](https://github.com/confluence-publisher/confluence-publisher) - Java-based publisher

---

Made with Python and Mistune
