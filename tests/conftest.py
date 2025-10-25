"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "api: mark test as API test")
    config.addinivalue_line("markers", "cli: mark test as CLI test")


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown() -> str:
    """Return sample markdown content for testing."""
    return """# Test Document

This is a test document with **bold** and *italic* text.

## Section 1

- Item 1
- Item 2
- Item 3

### Code Example

```python
def hello():
    print("Hello, World!")
```

Check out [this link](https://example.com).

> This is a quote.
"""


@pytest.fixture
def sample_markdown_with_frontmatter() -> str:
    """Return sample markdown with frontmatter for testing."""
    return """---
confluence_page_id: "123456"
confluence_space_key: "DEMO"
confluence_title: "Test Page"
confluence_version: 5
confluence_parent_id: "654321"
---
# Test Document

Content here.
"""


@pytest.fixture
def sample_confluence_html() -> str:
    """Return sample Confluence HTML for testing."""
    return """<h1>Test Document</h1>
<p>This is a test.</p>
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:plain-text-body><![CDATA[print("Hello")]]></ac:plain-text-body>
</ac:structured-macro>"""


@pytest.fixture
def mock_confluence_client() -> MagicMock:
    """Create a mock Confluence client for testing."""
    client = MagicMock()

    # Default mock responses
    client.get_space.return_value = {
        "key": "DEMO",
        "name": "Demo Space",
        "type": "global",
    }

    client.get_page_by_id.return_value = {
        "id": "123456",
        "title": "Test Page",
        "space": {"key": "DEMO"},
        "version": {"number": 5},
        "ancestors": [{"id": "654321"}],
    }

    client.get_page_by_title.return_value = None  # Page doesn't exist by default

    client.create_or_update_page.return_value = {
        "id": "123456",
        "title": "Test Page",
        "space": {"key": "DEMO"},
        "version": {"number": 1},
    }

    client.get_page_url.return_value = "https://example.com/page/123456"

    return client


@pytest.fixture
def mock_confluence_page() -> dict:
    """Return a mock Confluence page object."""
    return {
        "id": "123456",
        "title": "Test Page",
        "space": {
            "key": "DEMO",
            "name": "Demo Space",
        },
        "version": {
            "number": 5,
            "when": "2024-01-01T00:00:00.000Z",
            "by": {
                "displayName": "John Doe",
                "email": "john.doe@example.com",
            },
        },
        "ancestors": [
            {"id": "654321", "title": "Parent Page"}
        ],
        "_links": {
            "base": "https://example.atlassian.net",
            "webui": "/spaces/DEMO/pages/123456/Test+Page",
        },
    }


@pytest.fixture
def temp_markdown_file(temp_dir: Path, sample_markdown: str) -> Path:
    """Create a temporary markdown file for testing."""
    file_path = temp_dir / "test.md"
    file_path.write_text(sample_markdown)
    return file_path


@pytest.fixture
def temp_markdown_file_with_frontmatter(
    temp_dir: Path,
    sample_markdown_with_frontmatter: str
) -> Path:
    """Create a temporary markdown file with frontmatter for testing."""
    file_path = temp_dir / "test_with_frontmatter.md"
    file_path.write_text(sample_markdown_with_frontmatter)
    return file_path
