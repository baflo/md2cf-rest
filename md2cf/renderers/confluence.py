"""
Confluence Storage Format Renderer for Mistune.

This module provides a custom renderer that converts Markdown AST to
Confluence Storage Format (XHTML-based format used by Confluence).
"""

from typing import Any, Dict, List, Optional
from html import escape

import mistune


class ConfluenceStorageFormatRenderer(mistune.HTMLRenderer):
    """
    Custom Mistune renderer for Confluence Storage Format.

    Converts Markdown elements to Confluence-specific XHTML markup.
    Supports headings, lists, code blocks, tables, links, images, and more.
    """

    def __init__(self) -> None:
        """Initialize the Confluence Storage Format renderer."""
        super().__init__(escape=False)
        self._list_depth = 0
        self._converter = None  # Reference to the converter for tracking images
        self._image_attrs_parser = None  # Reference to image attributes parser
        self._in_task_list = False  # Track if we're in a task list
        self._task_counter = 0  # Counter for generating unique task IDs

    def set_converter(self, converter: Any) -> None:
        """
        Set the converter instance for image tracking.

        Args:
            converter: MarkdownToConfluence instance
        """
        self._converter = converter

    def set_image_attrs_parser(self, parser: Any) -> None:
        """
        Set the image attributes parser.

        Args:
            parser: ImageAttributesParser instance
        """
        self._image_attrs_parser = parser

    def heading(self, text: str, level: int, **attrs: Any) -> str:
        """
        Render heading element.

        Args:
            text: The heading text
            level: Heading level (1-6)
            **attrs: Additional attributes

        Returns:
            Confluence heading markup
        """
        return f"<h{level}>{text}</h{level}>\n"

    def paragraph(self, text: str, **attrs: Any) -> str:
        """
        Render paragraph element.

        Args:
            text: The paragraph text
            **attrs: Additional attributes

        Returns:
            Confluence paragraph markup
        """
        return f"<p>{text}</p>\n"

    def block_code(self, code: str, info: Optional[str] = None, **attrs: Any) -> str:
        """
        Render code block.

        Special handling for PlantUML: renders as PlantUML macro instead of code macro.

        Args:
            code: The code content
            info: Language identifier (optional)
            **attrs: Additional attributes

        Returns:
            Confluence code macro or PlantUML macro
        """
        # Don't escape code in CDATA sections - they're already protected
        code = code.rstrip()
        language = info.strip().lower() if info else "none"

        # Special handling for PlantUML (supports plantuml, puml, and plant-uml)
        if language in ("plantuml", "puml", "plant-uml"):
            return (
                f'<ac:structured-macro ac:name="plantuml" ac:schema-version="1">'
                f'<ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body>'
                f'</ac:structured-macro>\n'
            )

        # Regular code block
        language_escaped = escape(language)
        return (
            f'<ac:structured-macro ac:name="code" ac:schema-version="1">'
            f'<ac:parameter ac:name="language">{language_escaped}</ac:parameter>'
            f'<ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body>'
            f'</ac:structured-macro>\n'
        )

    def block_quote(self, text: str, **attrs: Any) -> str:
        """
        Render blockquote element.

        Args:
            text: The quote content
            **attrs: Additional attributes

        Returns:
            Confluence blockquote markup
        """
        return f"<blockquote>{text}</blockquote>\n"

    def list(self, text: str, ordered: bool, **attrs: Any) -> str:
        """
        Render list element.

        Args:
            text: The list content
            ordered: Whether the list is ordered
            **attrs: Additional attributes

        Returns:
            Confluence list markup or task list
        """
        # Check if this is a task list by looking for <ac:task> elements
        is_task_list = '<ac:task>' in text

        if is_task_list:
            # Wrap task items in ac:task-list
            return f"<ac:task-list>\n{text}</ac:task-list>\n"
        else:
            # Regular list
            tag = "ol" if ordered else "ul"
            return f"<{tag}>\n{text}</{tag}>\n"

    def list_item(self, text: str, **attrs: Any) -> str:
        """
        Render list item.

        Args:
            text: The item content
            **attrs: Additional attributes

        Returns:
            Confluence list item markup
        """
        return f"<li>{text}</li>\n"

    def strong(self, text: str, **attrs: Any) -> str:
        """
        Render strong/bold text.

        Args:
            text: The text content
            **attrs: Additional attributes

        Returns:
            Confluence bold markup
        """
        return f"<strong>{text}</strong>"

    def emphasis(self, text: str, **attrs: Any) -> str:
        """
        Render emphasis/italic text.

        Args:
            text: The text content
            **attrs: Additional attributes

        Returns:
            Confluence italic markup
        """
        return f"<em>{text}</em>"

    def codespan(self, text: str, **attrs: Any) -> str:
        """
        Render inline code.

        Args:
            text: The code content
            **attrs: Additional attributes

        Returns:
            Confluence inline code markup
        """
        # Escape special characters in inline code
        text = escape(text, quote=False)
        return f"<code>{text}</code>"

    def linebreak(self, **attrs: Any) -> str:
        """
        Render line break.

        Args:
            **attrs: Additional attributes

        Returns:
            Confluence line break markup
        """
        return "<br/>"

    def link(self, text: str, url: str, title: Optional[str] = None, **attrs: Any) -> str:
        """
        Render hyperlink.

        Args:
            text: The link text
            url: The URL
            title: Optional title attribute
            **attrs: Additional attributes

        Returns:
            Confluence link markup
        """
        # Escape URL but preserve already-encoded entities
        url = escape(url, quote=False)
        if title:
            title = escape(title, quote=False)
            return f'<a href="{url}" title="{title}">{text}</a>'
        return f'<a href="{url}">{text}</a>'

    def image(self, alt: str, url: str, title: Optional[str] = None, **attrs: Any) -> str:
        """
        Render image with optional width/height attributes.

        Args:
            alt: Alt text
            url: Image URL
            title: Optional title
            **attrs: Additional attributes

        Returns:
            Confluence image macro

        Supports attribute syntax via preprocessor:
            - ![alt](url){:height 34, :width 123}
            - ![alt](url){:width "200px"}
        """
        # Get width and height from image attributes parser
        width = None
        height = None
        if self._image_attrs_parser:
            img_attrs = self._image_attrs_parser.get_attributes(url)
            width = img_attrs.get('width')
            height = img_attrs.get('height')

        # Track image reference if converter is set
        if self._converter:
            self._converter.add_image_reference(url)

        # Escape URL but preserve already-encoded entities
        url_escaped = escape(url, quote=False)

        # Check if this is a local file that will be uploaded as attachment
        is_local = not url.startswith(('http://', 'https://', '//', 'data:'))

        # Build image attributes and parameters
        # Confluence supports both ac:width/ac:height attributes and ac:parameter elements
        image_attrs = []
        if width:
            image_attrs.append(f'ac:width="{escape(str(width), quote=False)}"')
        if height:
            image_attrs.append(f'ac:height="{escape(str(height), quote=False)}"')

        attrs_str = ' ' + ' '.join(image_attrs) if image_attrs else ''

        if is_local:
            # For local files, use attachment reference
            # Extract filename from path
            from pathlib import Path
            filename = Path(url).name
            filename_escaped = escape(filename, quote=False)

            return (
                f'<ac:image{attrs_str}>'
                f'<ri:attachment ri:filename="{filename_escaped}" />'
                f'</ac:image>'
            )
        else:
            # For external URLs, use URL reference
            return (
                f'<ac:image{attrs_str}>'
                f'<ri:url ri:value="{url_escaped}" />'
                f'</ac:image>'
            )

    def table(self, text: str, **attrs: Any) -> str:
        """
        Render table.

        Args:
            text: The table content
            **attrs: Additional attributes

        Returns:
            Confluence table markup
        """
        return f"<table>\n{text}</table>\n"

    def table_head(self, text: str, **attrs: Any) -> str:
        """
        Render table head.

        Args:
            text: The table head content
            **attrs: Additional attributes

        Returns:
            Confluence table head markup
        """
        return f"<thead>\n{text}</thead>\n"

    def table_body(self, text: str, **attrs: Any) -> str:
        """
        Render table body.

        Args:
            text: The table body content
            **attrs: Additional attributes

        Returns:
            Confluence table body markup
        """
        return f"<tbody>\n{text}</tbody>\n"

    def table_row(self, text: str, **attrs: Any) -> str:
        """
        Render table row.

        Args:
            text: The row content
            **attrs: Additional attributes

        Returns:
            Confluence table row markup
        """
        return f"<tr>\n{text}</tr>\n"

    def table_cell(self, text: str, align: Optional[str] = None, head: bool = False,
                   **attrs: Any) -> str:
        """
        Render table cell.

        Args:
            text: The cell content
            align: Text alignment (left, center, right)
            head: Whether this is a header cell
            **attrs: Additional attributes

        Returns:
            Confluence table cell markup
        """
        tag = "th" if head else "td"
        if align:
            return f'<{tag} style="text-align: {align};">{text}</{tag}>\n'
        return f"<{tag}>{text}</{tag}>\n"

    def thematic_break(self, **attrs: Any) -> str:
        """
        Render thematic break (horizontal rule).

        Args:
            **attrs: Additional attributes

        Returns:
            Confluence horizontal rule markup
        """
        return "<hr/>\n"

    def strikethrough(self, text: str, **attrs: Any) -> str:
        """
        Render strikethrough text.

        Args:
            text: The text content
            **attrs: Additional attributes

        Returns:
            Confluence strikethrough markup
        """
        return f"<del>{text}</del>"

    def task_list_item(self, text: str, checked: bool = False, **attrs: Any) -> str:
        """
        Render task list item as Confluence Action Item.

        Args:
            text: The item content
            checked: Whether the checkbox is checked
            **attrs: Additional attributes

        Returns:
            Confluence Action Item macro
        """
        # Generate unique task ID
        self._task_counter += 1
        task_id = self._task_counter

        # Use Confluence's task macro for proper action items
        # ac:task-status: "complete" for checked items, "incomplete" for unchecked
        status = "complete" if checked else "incomplete"

        # Strip surrounding <p> tags if present, as task bodies should be inline
        # If there are multiple paragraphs, keep them but strip the outer ones
        task_text = text.strip()

        # Remove single outer paragraph tags for simple cases
        if task_text.startswith('<p>') and task_text.endswith('</p>\n'):
            # Check if this is a single paragraph (no other </p> in between)
            inner_content = task_text[3:-5]
            if '</p>' not in inner_content:
                task_text = inner_content
            else:
                # Multiple paragraphs - remove only the outer wrapper
                task_text = task_text[3:-5]
        elif task_text.startswith('<p>') and task_text.endswith('</p>'):
            inner_content = task_text[3:-4]
            if '</p>' not in inner_content:
                task_text = inner_content
            else:
                task_text = task_text[3:-4]

        return (
            f'<ac:task>'
            f'<ac:task-id>{task_id}</ac:task-id>'
            f'<ac:task-status>{status}</ac:task-status>'
            f'<ac:task-body><span class="placeholder-inline-tasks">{task_text}</span></ac:task-body>'
            f'</ac:task>\n'
        )

    def text(self, text: str, **attrs: Any) -> str:
        """
        Render plain text.

        Args:
            text: The text content
            **attrs: Additional attributes

        Returns:
            Escaped text
        """
        # Escape special XML/HTML characters but not quotes in text content
        return escape(text, quote=False)
