"""Tests for the Markdown to Confluence converter."""

import tempfile
from pathlib import Path

import pytest

from md2cf.converter import MarkdownToConfluence, convert_markdown_to_confluence


@pytest.fixture
def converter() -> MarkdownToConfluence:
    """Create a converter instance for testing."""
    return MarkdownToConfluence()


class TestBasicConversion:
    """Test basic Markdown to Confluence conversion."""

    def test_empty_string(self, converter: MarkdownToConfluence) -> None:
        """Test conversion of empty string."""
        result = converter.convert("")
        assert result == ""

    def test_heading(self, converter: MarkdownToConfluence) -> None:
        """Test heading conversion."""
        result = converter.convert("# Title")
        assert "<h1>Title</h1>" in result

    def test_paragraph(self, converter: MarkdownToConfluence) -> None:
        """Test paragraph conversion."""
        result = converter.convert("This is a paragraph.")
        assert "<p>This is a paragraph.</p>" in result

    def test_bold(self, converter: MarkdownToConfluence) -> None:
        """Test bold text conversion."""
        result = converter.convert("This is **bold** text.")
        assert "<strong>bold</strong>" in result

    def test_italic(self, converter: MarkdownToConfluence) -> None:
        """Test italic text conversion."""
        result = converter.convert("This is *italic* text.")
        assert "<em>italic</em>" in result

    def test_inline_code(self, converter: MarkdownToConfluence) -> None:
        """Test inline code conversion."""
        result = converter.convert("Use `print()` function.")
        assert "<code>print()</code>" in result


class TestCodeBlocks:
    """Test code block conversion."""

    def test_code_block_without_language(self, converter: MarkdownToConfluence) -> None:
        """Test code block without language specification."""
        markdown = "```\nprint('Hello')\n```"
        result = converter.convert(markdown)
        assert '<ac:structured-macro ac:name="code"' in result
        assert "print('Hello')" in result

    def test_code_block_with_language(self, converter: MarkdownToConfluence) -> None:
        """Test code block with language specification."""
        markdown = "```python\nprint('Hello')\n```"
        result = converter.convert(markdown)
        assert '<ac:parameter ac:name="language">python</ac:parameter>' in result
        assert "print('Hello')" in result


class TestLists:
    """Test list conversion."""

    def test_unordered_list(self, converter: MarkdownToConfluence) -> None:
        """Test unordered list conversion."""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        result = converter.convert(markdown)
        assert "<ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<li>Item 2</li>" in result

    def test_ordered_list(self, converter: MarkdownToConfluence) -> None:
        """Test ordered list conversion."""
        markdown = "1. First\n2. Second\n3. Third"
        result = converter.convert(markdown)
        assert "<ol>" in result
        assert "<li>First</li>" in result
        assert "<li>Second</li>" in result


class TestLinks:
    """Test link conversion."""

    def test_link(self, converter: MarkdownToConfluence) -> None:
        """Test link conversion."""
        markdown = "[Link text](https://example.com)"
        result = converter.convert(markdown)
        assert '<a href="https://example.com">Link text</a>' in result

    def test_link_with_title(self, converter: MarkdownToConfluence) -> None:
        """Test link with title conversion."""
        markdown = '[Link](https://example.com "Title")'
        result = converter.convert(markdown)
        assert 'href="https://example.com"' in result
        assert 'title="Title"' in result


class TestImages:
    """Test image conversion."""

    def test_image(self, converter: MarkdownToConfluence) -> None:
        """Test image conversion."""
        markdown = "![Alt text](https://example.com/image.png)"
        result = converter.convert(markdown)
        assert "<ac:image>" in result
        assert "https://example.com/image.png" in result


class TestTables:
    """Test table conversion."""

    def test_simple_table(self, converter: MarkdownToConfluence) -> None:
        """Test simple table conversion."""
        markdown = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""
        result = converter.convert(markdown)
        assert "<table>" in result
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "<th>Header 1</th>" in result
        assert "<td>Cell 1</td>" in result


class TestTaskLists:
    """Test task list conversion."""

    def test_task_list_checked(self, converter: MarkdownToConfluence) -> None:
        """Test checked task list item conversion."""
        markdown = "- [x] Completed task"
        result = converter.convert(markdown)
        assert '<li class="task-list-item">' in result
        assert 'type="checkbox"' in result
        assert 'checked="checked"' in result
        # Ensure no HTML5-style boolean attributes (which cause XHTML parse errors)
        assert 'checked/>' not in result
        assert 'disabled/>' not in result

    def test_task_list_unchecked(self, converter: MarkdownToConfluence) -> None:
        """Test unchecked task list item conversion."""
        markdown = "- [ ] Incomplete task"
        result = converter.convert(markdown)
        assert '<li class="task-list-item">' in result
        assert 'type="checkbox"' in result
        assert 'disabled="disabled"' in result
        # Should not have checked attribute
        assert 'checked="checked"' not in result

    def test_task_list_multiple_items(self, converter: MarkdownToConfluence) -> None:
        """Test multiple task list items."""
        markdown = """
- [x] Task 1
- [ ] Task 2
- [x] Task 3
"""
        result = converter.convert(markdown)
        # Should have 3 checkboxes
        assert result.count('type="checkbox"') == 3
        # Should have 2 checked items
        assert result.count('checked="checked"') == 2
        # All should use valid XHTML boolean attribute syntax
        assert 'checked/>' not in result
        assert 'disabled/>' not in result


class TestBlockquotes:
    """Test blockquote conversion."""

    def test_simple_blockquote(self, converter: MarkdownToConfluence) -> None:
        """Test simple blockquote conversion."""
        markdown = "> This is a blockquote."
        result = converter.convert(markdown)
        assert "<blockquote>" in result
        assert "<p>This is a blockquote.</p>" in result
        assert "</blockquote>" in result

    def test_multiline_blockquote(self, converter: MarkdownToConfluence) -> None:
        """Test multiline blockquote conversion."""
        markdown = """> This is a blockquote.
> It can span multiple lines."""
        result = converter.convert(markdown)
        assert "<blockquote>" in result
        assert "This is a blockquote." in result
        assert "It can span multiple lines." in result

    def test_blockquote_with_formatting(self, converter: MarkdownToConfluence) -> None:
        """Test blockquote with formatting inside."""
        markdown = "> **Important Note:**\n> You can include *formatting* inside."
        result = converter.convert(markdown)
        assert "<blockquote>" in result
        assert "<strong>Important Note:</strong>" in result
        assert "<em>formatting</em>" in result


class TestComplexDocument:
    """Test complex document conversion."""

    def test_comprehensive_document(self, converter: MarkdownToConfluence) -> None:
        """Test conversion of a comprehensive document."""
        markdown = """
# Main Title

This is a paragraph with **bold** and *italic* text.

## Subsection

Here's a list:
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
        result = converter.convert(markdown)

        # Check all elements are present
        assert "<h1>Main Title</h1>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "<h2>Subsection</h2>" in result
        assert "<ul>" in result
        assert '<ac:parameter ac:name="language">python</ac:parameter>' in result
        assert '<a href="https://example.com">this link</a>' in result
        assert '<blockquote>' in result


class TestFileConversion:
    """Test file-based conversion."""

    def test_convert_file(self, converter: MarkdownToConfluence) -> None:
        """Test converting a markdown file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n\nThis is a test.")
            temp_path = f.name

        try:
            result = converter.convert_file(temp_path)
            assert "<h1>Test</h1>" in result
            assert "<p>This is a test.</p>" in result
        finally:
            Path(temp_path).unlink()

    def test_convert_file_not_found(self, converter: MarkdownToConfluence) -> None:
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            converter.convert_file("/nonexistent/file.md")

    def test_convert_and_save(self, converter: MarkdownToConfluence) -> None:
        """Test converting and saving to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input file
            input_file = Path(tmpdir) / "input.md"
            input_file.write_text("# Test\n\nContent")

            # Convert and save
            output_file = converter.convert_and_save(input_file)

            # Check output file was created
            assert output_file.exists()
            assert output_file.suffix == ".html"

            # Check content
            content = output_file.read_text()
            assert "<h1>Test</h1>" in content

    def test_convert_and_save_custom_output(self, converter: MarkdownToConfluence) -> None:
        """Test converting and saving with custom output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input file
            input_file = Path(tmpdir) / "input.md"
            input_file.write_text("# Test")

            # Convert with custom output
            output_file = Path(tmpdir) / "custom_output.html"
            result = converter.convert_and_save(input_file, output_file)

            assert result == output_file
            assert output_file.exists()


class TestConvenienceFunction:
    """Test the convenience function."""

    def test_convert_markdown_to_confluence(self) -> None:
        """Test the convenience function."""
        result = convert_markdown_to_confluence("# Title\n\nParagraph")
        assert "<h1>Title</h1>" in result
        assert "<p>Paragraph</p>" in result
