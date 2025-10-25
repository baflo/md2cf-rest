"""Integration tests for end-to-end workflows."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from md2cf.converter import MarkdownToConfluence
from md2cf.utils.frontmatter import FrontmatterMetadata, add_frontmatter, parse_frontmatter_metadata


class TestFrontmatterWorkflow:
    """Test complete frontmatter workflow (download -> edit -> publish)."""

    def test_roundtrip_workflow(self):
        """Test complete roundtrip: create frontmatter, save, load, parse."""
        # Step 1: Create markdown with frontmatter
        original_content = """# Test Document

This is a test document with **formatting**.

## Section 1

- Item 1
- Item 2

```python
def test():
    print("Hello")
```
"""
        metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
            title="Test Document",
            version=5,
            parent_id="654321",
        )

        # Add frontmatter
        content_with_frontmatter = add_frontmatter(original_content, metadata)

        # Step 2: Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content_with_frontmatter)
            temp_file = f.name

        try:
            # Step 3: Load from file and parse
            with open(temp_file, 'r') as f:
                loaded_content = f.read()

            parsed_metadata, parsed_content = parse_frontmatter_metadata(loaded_content)

            # Verify metadata
            assert parsed_metadata.page_id == "123456"
            assert parsed_metadata.space_key == "DEMO"
            assert parsed_metadata.title == "Test Document"
            assert parsed_metadata.version == 5
            assert parsed_metadata.parent_id == "654321"

            # Verify content
            assert parsed_content == original_content

            # Step 4: Convert to Confluence format
            converter = MarkdownToConfluence()
            confluence_html = converter.convert(parsed_content)

            # Verify conversion
            assert "<h1>Test Document</h1>" in confluence_html
            assert "<strong>formatting</strong>" in confluence_html
            assert "<h2>Section 1</h2>" in confluence_html
            assert '<ac:structured-macro ac:name="code"' in confluence_html

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_update_frontmatter_after_publish(self):
        """Test updating frontmatter after publishing (version increment)."""
        content = "# Test"
        metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
            version=5,
        )

        # Initial frontmatter
        with_frontmatter = add_frontmatter(content, metadata)

        # Simulate publish: update version
        updated_metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
            version=6,  # Incremented
        )

        # Update frontmatter
        updated_frontmatter = add_frontmatter(content, updated_metadata)

        # Parse and verify
        parsed, _ = parse_frontmatter_metadata(updated_frontmatter)
        assert parsed.version == 6


class TestConversionWorkflow:
    """Test complete conversion workflows."""

    def test_markdown_to_confluence_with_images(self):
        """Test converting markdown with images."""
        import tempfile

        # Create temporary directory with test images
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create two test image files
            (base_path / "image1.png").write_bytes(b"fake image 1")
            (base_path / "image2.png").write_bytes(b"fake image 2")

            markdown = """# Document with Images

Here's an image:

![Alt text](image1.png)

And another:

![Another](image2.png)
"""
            converter = MarkdownToConfluence(base_path=base_path)
            result = converter.convert(markdown, extract_images=True)

            # Check image macros
            assert "<ac:image>" in result
            assert result.count("<ac:image>") == 2

            # Check image references were extracted
            images = converter.get_image_references()
            assert len(images) == 2
            assert images[0]["filename"] == "image1.png"
            assert images[1]["filename"] == "image2.png"

    def test_markdown_with_jira_links(self):
        """Test converting markdown with Jira issue links."""
        # Jira links only work with actual markdown links, not plain text mentions
        markdown = """# Document

See ticket [PROJ-123](https://jira.example.com/browse/PROJ-123) for details.

Also check [PROJ-456](https://jira.example.com/browse/PROJ-456).
"""
        converter = MarkdownToConfluence(jira_url="https://jira.example.com")
        result = converter.convert(markdown)

        # Check Jira macros were created
        assert '<ac:structured-macro ac:name="jira"' in result
        assert '<ac:parameter ac:name="key">PROJ-123</ac:parameter>' in result
        assert '<ac:parameter ac:name="key">PROJ-456</ac:parameter>' in result

    def test_markdown_with_info_panel(self):
        """Test converting with info panel."""
        markdown = "# Test"
        converter = MarkdownToConfluence(
            add_info_panel=True,
            page_id="123456",
            space_key="DEMO",
            page_title="Test Page",
            markdown_attachment_name="Test.md"
        )
        result = converter.convert(markdown)

        # Check info panel macro
        assert '<ac:structured-macro ac:name="info"' in result
        # Info panel text is in German
        assert "aus Markdown generiert" in result
        # Check for attachment link
        assert '<ri:attachment ri:filename="Test.md"' in result

    def test_plantuml_conversion(self):
        """Test converting PlantUML diagrams."""
        markdown = """# Diagram

```plantuml
@startuml
Alice -> Bob: Hello
@enduml
```
"""
        converter = MarkdownToConfluence()
        result = converter.convert(markdown)

        # Check PlantUML macro
        assert '<ac:structured-macro ac:name="plantuml"' in result
        assert "@startuml" in result
        assert "Alice -> Bob" in result


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    @patch('md2cf.cli.ConfluenceClient')
    def test_full_publish_workflow(self, mock_client_class):
        """Test full publish workflow from file to Confluence."""
        from md2cf.cli import publish_command

        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_space.return_value = {"key": "DEMO"}
        mock_client.get_page_by_title.return_value = None
        mock_client.create_or_update_page.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
        }
        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "ancestors": [],
        }
        mock_client.get_page_url.return_value = "https://example.com"

        # Create test file
        markdown_content = """# Test Page

This is test content with:
- Lists
- **Bold text**
- `code`

```python
def test():
    pass
```
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(markdown_content)
            temp_file = f.name

        try:
            # Create args
            args = MagicMock()
            args.input = temp_file
            args.url = "https://example.atlassian.net"
            args.token = "test-token"
            args.space = "DEMO"
            args.title = "Test Page"
            args.parent_id = None
            args.cloud = True
            args.no_verify_ssl = False
            args.jira_url = None
            args.no_info_panel = False

            # Run publish command
            result = publish_command(args)

            assert result == 0
            mock_client.create_or_update_page.assert_called()

            # Verify frontmatter was added to file
            with open(temp_file, 'r') as f:
                updated_content = f.read()

            assert "---" in updated_content
            assert "confluence_page_id" in updated_content

        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestRESTAPIIntegration:
    """Test REST API integration scenarios."""

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_publish_with_multiple_attachments(self, mock_client_class):
        """Test publishing with multiple attachments via REST API."""
        from fastapi.testclient import TestClient
        from md2cf.rest_api import app

        client = TestClient(app)

        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_space.return_value = {"key": "DEMO"}
        mock_client.get_page_by_title.return_value = None
        mock_client.create_or_update_page.return_value = {
            "id": "123456",
            "title": "Test",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
        }
        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test",
            "space": {"key": "DEMO"},
            "version": {"number": 1, "when": "2024-01-01"},
        }
        mock_client.get_page_url.return_value = "https://example.com"

        # Create request with multiple attachments
        markdown = """# Test

![Image 1](image1.png)
![Image 2](image2.png)
"""

        from io import BytesIO

        files = [
            ("attachments", ("image1.png", BytesIO(b"image1 data"), "image/png")),
            ("attachments", ("image2.png", BytesIO(b"image2 data"), "image/png")),
        ]

        data = {
            "markdown": markdown,
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
            "space": "DEMO",
            "title": "Test",
        }

        response = client.post("/publish", data=data, files=files)

        assert response.status_code == 201
        # Both attachments should have been uploaded
        assert mock_client.attach_file.call_count >= 2


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_invalid_frontmatter_handling(self):
        """Test handling of invalid YAML in frontmatter."""
        content = """---
invalid: [yaml
---
# Content"""

        # Should not crash, should return None for frontmatter
        metadata, remaining = parse_frontmatter_metadata(content)

        assert not metadata.has_metadata()
        # Original content should be preserved
        assert "# Content" in remaining or "invalid:" in remaining

    @patch('md2cf.cli.ConfluenceClient')
    def test_network_error_handling(self, mock_client_class):
        """Test handling of network errors during publish."""
        from md2cf.cli import publish_command

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Simulate network error
        mock_client.get_space.side_effect = Exception("Network error")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test")
            temp_file = f.name

        try:
            args = MagicMock()
            args.input = temp_file
            args.url = "https://example.atlassian.net"
            args.token = "test-token"
            args.space = "DEMO"
            args.title = "Test"
            args.parent_id = None
            args.cloud = True
            args.no_verify_ssl = False
            args.jira_url = None
            args.no_info_panel = False

            result = publish_command(args)

            # Should return error code
            assert result == 1

        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestComplexDocuments:
    """Test handling of complex real-world documents."""

    def test_comprehensive_markdown_document(self):
        """Test converting a comprehensive markdown document."""
        markdown = """# Main Title

## Introduction

This is a comprehensive document with various Markdown features.

### Text Formatting

You can use **bold**, *italic*, and `inline code`.

### Lists

Ordered list:
1. First item
2. Second item
3. Third item

Unordered list:
- Item A
- Item B
  - Nested item
  - Another nested

### Code Blocks

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
```

### Tables

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

### Links and Images

Check out [this link](https://example.com).

![Sample Image](image.png)

### Blockquotes

> This is a quote.
> It can span multiple lines.

### Task Lists

- [x] Completed task
- [ ] Pending task
- [x] Another completed task

## Conclusion

That's all folks!
"""
        converter = MarkdownToConfluence()
        result = converter.convert(markdown, extract_images=True)

        # Verify all elements are present
        assert "<h1>Main Title</h1>" in result
        assert "<h2>Introduction</h2>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "<code>inline code</code>" in result
        assert "<ol>" in result
        assert "<ul>" in result
        assert '<ac:structured-macro ac:name="code"' in result
        assert "python" in result
        assert "<table>" in result
        assert '<a href="https://example.com"' in result
        assert "<ac:image>" in result
        assert "<blockquote>" in result
        # Task lists use Confluence macros, not HTML checkboxes
        assert '<ac:task-list>' in result
        assert '<ac:task>' in result

        # Check image extraction
        images = converter.get_image_references()
        assert len(images) == 1
        assert images[0]["filename"] == "image.png"
