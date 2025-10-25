"""Tests for the Confluence Storage Format Renderer."""

import pytest

from md2cf.renderers.confluence import ConfluenceStorageFormatRenderer


@pytest.fixture
def renderer() -> ConfluenceStorageFormatRenderer:
    """Create a renderer instance for testing."""
    return ConfluenceStorageFormatRenderer()


class TestHeadings:
    """Test heading rendering."""

    def test_h1(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test H1 heading rendering."""
        result = renderer.heading("Title", 1)
        assert result == "<h1>Title</h1>\n"

    def test_h2(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test H2 heading rendering."""
        result = renderer.heading("Subtitle", 2)
        assert result == "<h2>Subtitle</h2>\n"

    def test_h6(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test H6 heading rendering."""
        result = renderer.heading("Small heading", 6)
        assert result == "<h6>Small heading</h6>\n"


class TestTextFormatting:
    """Test text formatting."""

    def test_paragraph(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test paragraph rendering."""
        result = renderer.paragraph("This is a paragraph")
        assert result == "<p>This is a paragraph</p>\n"

    def test_strong(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test bold text rendering."""
        result = renderer.strong("bold text")
        assert result == "<strong>bold text</strong>"

    def test_emphasis(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test italic text rendering."""
        result = renderer.emphasis("italic text")
        assert result == "<em>italic text</em>"

    def test_strikethrough(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test strikethrough text rendering."""
        result = renderer.strikethrough("deleted text")
        assert result == "<del>deleted text</del>"

    def test_codespan(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test inline code rendering."""
        result = renderer.codespan("code")
        assert result == "<code>code</code>"

    def test_codespan_escaping(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test inline code with special characters."""
        result = renderer.codespan("<tag>")
        assert result == "<code>&lt;tag&gt;</code>"


class TestCodeBlocks:
    """Test code block rendering."""

    def test_code_block_plain(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test code block without language."""
        result = renderer.block_code("print('Hello')")
        assert '<ac:structured-macro ac:name="code"' in result
        assert '<ac:parameter ac:name="language">none</ac:parameter>' in result
        assert "print('Hello')" in result

    def test_code_block_with_language(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test code block with language specification."""
        result = renderer.block_code("print('Hello')", "python")
        assert '<ac:parameter ac:name="language">python</ac:parameter>' in result
        assert "print('Hello')" in result

    def test_code_block_escaping(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test code block with special characters."""
        result = renderer.block_code("<html>", "html")
        # Code is wrapped in CDATA, so it's not HTML-escaped
        assert "<![CDATA[<html>]]>" in result


class TestLists:
    """Test list rendering."""

    def test_unordered_list(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test unordered list rendering."""
        result = renderer.list("<li>Item 1</li>\n<li>Item 2</li>\n", ordered=False)
        assert result == "<ul>\n<li>Item 1</li>\n<li>Item 2</li>\n</ul>\n"

    def test_ordered_list(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test ordered list rendering."""
        result = renderer.list("<li>First</li>\n<li>Second</li>\n", ordered=True)
        assert result == "<ol>\n<li>First</li>\n<li>Second</li>\n</ol>\n"

    def test_list_item(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test list item rendering."""
        result = renderer.list_item("Item text")
        assert result == "<li>Item text</li>\n"


class TestLinks:
    """Test link rendering."""

    def test_link_basic(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test basic link rendering."""
        result = renderer.link("Link text", "https://example.com")
        assert result == '<a href="https://example.com">Link text</a>'

    def test_link_with_title(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test link with title attribute."""
        result = renderer.link("Link", "https://example.com", "Example Site")
        assert 'title="Example Site"' in result
        assert 'href="https://example.com"' in result

    def test_link_escaping(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test link with special characters."""
        result = renderer.link("Text", "https://example.com?a=1&b=2")
        assert "&amp;" in result


class TestImages:
    """Test image rendering."""

    def test_image_basic(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test basic image rendering."""
        result = renderer.image("Alt text", "https://example.com/image.png")
        assert "<ac:image>" in result
        assert '<ri:url ri:value="https://example.com/image.png" />' in result

    def test_image_escaping(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test image URL escaping."""
        result = renderer.image("Alt", "https://example.com/img?v=1&t=2")
        assert "&amp;" in result


class TestBlockQuote:
    """Test blockquote rendering."""

    def test_blockquote(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test blockquote rendering."""
        result = renderer.block_quote("<p>Quote text</p>\n")
        # Confluence uses simple blockquote tags, not quote macros
        assert "<blockquote>" in result
        assert "<p>Quote text</p>" in result
        assert "</blockquote>" in result


class TestTables:
    """Test table rendering."""

    def test_table(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test table rendering."""
        result = renderer.table("<tbody><tr><td>Cell</td></tr></tbody>")
        assert result == "<table>\n<tbody><tr><td>Cell</td></tr></tbody></table>\n"

    def test_table_head(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test table head rendering."""
        result = renderer.table_head("<tr><th>Header</th></tr>")
        assert result == "<thead>\n<tr><th>Header</th></tr></thead>\n"

    def test_table_body(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test table body rendering."""
        result = renderer.table_body("<tr><td>Cell</td></tr>")
        assert result == "<tbody>\n<tr><td>Cell</td></tr></tbody>\n"

    def test_table_row(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test table row rendering."""
        result = renderer.table_row("<td>Cell</td>")
        assert result == "<tr>\n<td>Cell</td></tr>\n"

    def test_table_cell(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test table cell rendering."""
        result = renderer.table_cell("Content", head=False)
        assert result == "<td>Content</td>\n"

    def test_table_header_cell(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test table header cell rendering."""
        result = renderer.table_cell("Header", head=True)
        assert result == "<th>Header</th>\n"

    def test_table_cell_aligned(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test table cell with alignment."""
        result = renderer.table_cell("Content", align="center")
        assert 'style="text-align: center;"' in result


class TestMisc:
    """Test miscellaneous elements."""

    def test_linebreak(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test line break rendering."""
        result = renderer.linebreak()
        assert result == "<br/>"

    def test_thematic_break(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test thematic break (horizontal rule) rendering."""
        result = renderer.thematic_break()
        assert result == "<hr/>\n"

    def test_text_escaping(self, renderer: ConfluenceStorageFormatRenderer) -> None:
        """Test plain text escaping."""
        result = renderer.text("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
