"""
Markdown to Confluence Converter.

This module provides the main conversion functionality from Markdown
to Confluence Storage Format.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

import mistune

from md2cf.renderers.confluence import ConfluenceStorageFormatRenderer


logger = logging.getLogger(__name__)


class ImageAttributesParser:
    """
    Parser for image attributes like {:width 200, :height 100}.

    Stores attributes separately and provides them to the renderer.
    """
    def __init__(self):
        self.attributes = {}  # Maps URL to {width, height}

    def preprocess(self, markdown_text: str) -> str:
        """
        Preprocess markdown to extract image attributes and remove metadata.

        Finds patterns like ![alt](url){:width X, :height Y}
        and stores the attributes separately.

        Also removes metadata lines like:
        - id:: value
        - property:: value
        """
        # Pattern to match image with attributes
        pattern = r'!\[([^\]]*)\]\(([^\)]+)\)\s*\{([^}]+)\}'

        def replace_image(match):
            alt = match.group(1)
            url = match.group(2).strip()
            attrs_str = match.group(3)

            # Parse width and height
            attrs = {}
            width_match = re.search(r':width\s+["\']?(\d+(?:px)?)["\']?', attrs_str)
            height_match = re.search(r':height\s+["\']?(\d+(?:px)?)["\']?', attrs_str)

            if width_match:
                attrs['width'] = width_match.group(1).rstrip('px')
            if height_match:
                attrs['height'] = height_match.group(1).rstrip('px')

            # Store attributes using URL as key
            self.attributes[url] = attrs

            # Return standard markdown image syntax (without attributes)
            return f'![{alt}]({url})'

        result = re.sub(pattern, replace_image, markdown_text)

        # Remove metadata lines (property:: value format, typically from Logseq/Obsidian)
        # Matches lines like: id:: value, property:: value, etc.
        result = re.sub(r'^\s*\w+::\s+[^\n]+$', '', result, flags=re.MULTILINE)

        # Remove LOGBOOK blocks (from Logseq/Org-mode)
        # Matches blocks like:
        # :LOGBOOK:
        # CLOCK: [timestamp]
        # :END:
        result = re.sub(r'^\s*:LOGBOOK:.*?:END:\s*$', '', result, flags=re.MULTILINE | re.DOTALL)

        return result

    def get_attributes(self, url: str) -> dict:
        """Get stored attributes for a given URL."""
        return self.attributes.get(url, {})


class MarkdownToConfluence:
    """
    Converter for transforming Markdown to Confluence Storage Format.

    This class uses Mistune with a custom renderer to convert Markdown
    content into Confluence-compatible XHTML.
    """

    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        jira_url: Optional[str] = None,
        add_info_panel: bool = True,
        markdown_attachment_name: Optional[str] = None,
        page_id: Optional[str] = None,
        space_key: Optional[str] = None,
        page_title: Optional[str] = None
    ) -> None:
        """
        Initialize the converter with Confluence renderer.

        Args:
            base_path: Base path for resolving relative image paths (optional)
            jira_url: Base Jira URL for detecting Jira ticket links (optional)
                     e.g., "https://jira.lvm.de/jira/"
            add_info_panel: Whether to add an info panel indicating the page was
                           generated from Markdown (default: True)
            markdown_attachment_name: Filename of the markdown attachment to link in
                                     the info panel (optional, e.g., "document.md")
            page_id: Confluence page ID for the CLI example (optional)
            space_key: Confluence space key for the CLI example (optional)
            page_title: Page title for the CLI example (optional)
        """
        self.renderer = ConfluenceStorageFormatRenderer()
        self.image_attrs_parser = ImageAttributesParser()
        self.jira_url = jira_url.rstrip('/') if jira_url else None
        self.add_info_panel = add_info_panel
        self.markdown_attachment_name = markdown_attachment_name
        self.page_id = page_id
        self.space_key = space_key
        self.page_title = page_title
        self.markdown = mistune.create_markdown(
            renderer=self.renderer,
            plugins=[
                "strikethrough",
                "table",
                "url",
                "task_lists",
            ],
        )
        self.base_path = Path(base_path) if base_path else None
        self.image_references: List[Dict[str, str]] = []
        logger.debug("Initialized MarkdownToConfluence converter")
        if self.jira_url:
            logger.debug(f"Jira URL configured: {self.jira_url}")
        if self.markdown_attachment_name:
            logger.debug(f"Markdown attachment name: {self.markdown_attachment_name}")

    def convert(self, markdown_content: str, extract_images: bool = False) -> str:
        """
        Convert Markdown string to Confluence Storage Format.

        Args:
            markdown_content: Markdown text to convert
            extract_images: Whether to extract and track image references

        Returns:
            Confluence Storage Format (XHTML) string

        Example:
            >>> converter = MarkdownToConfluence()
            >>> result = converter.convert("# Hello\\n\\nThis is **bold**")
            >>> print(result)
            <h1>Hello</h1>
            <p>This is <strong>bold</strong></p>
        """
        if not markdown_content:
            logger.warning("Empty markdown content provided")
            return ""

        # Preprocess to extract image attributes
        preprocessed = self.image_attrs_parser.preprocess(markdown_content)

        # Reset image references before conversion
        if extract_images:
            self.image_references.clear()
            self.renderer.set_converter(self)

        # Pass the parser to renderer so it can access attributes
        self.renderer.set_image_attrs_parser(self.image_attrs_parser)

        # Pass jira_url to renderer for Jira link detection
        self.renderer.set_jira_url(self.jira_url)

        logger.debug(f"Converting {len(markdown_content)} characters of Markdown")
        result = self.markdown(preprocessed)

        if isinstance(result, str):
            logger.debug(f"Converted to {len(result)} characters of Confluence format")
            if extract_images and self.image_references:
                logger.info(f"Extracted {len(self.image_references)} image references")

            # Add info panel at the top if enabled
            if self.add_info_panel:
                info_panel = self._generate_info_panel()
                result = info_panel + result

            return result
        else:
            logger.error(f"Unexpected conversion result type: {type(result)}")
            return str(result)

    def _generate_info_panel(self) -> str:
        """
        Generate an info panel indicating the page was generated from Markdown.

        If markdown_attachment_name is set, includes a link to the markdown attachment
        and a CLI example for downloading and re-publishing.

        Returns:
            Confluence info macro markup
        """
        if self.markdown_attachment_name:
            # Include link to markdown attachment with CLI example
            from html import escape
            filename_escaped = escape(self.markdown_attachment_name, quote=False)

            # Use actual values if available, otherwise use placeholders
            page_id_value = self.page_id if self.page_id else "PAGE_ID"
            space_key_value = self.space_key if self.space_key else "SPACE_KEY"

            # For title, escape quotes for use in command line
            if self.page_title:
                title_value = self.page_title.replace('"', '\\"')
            else:
                title_value = "TITLE"

            # Create CLI example (simplified - assumes env vars are set)
            cli_example = (
                f'# Download:<br/>'
                f'md2cf source {page_id_value}<br/><br/>'
                f'# Nach Änderungen re-publish:<br/>'
                f'md2cf publish ./{filename_escaped} --space {space_key_value} --title "{title_value}"'
            )

            return (
                '<ac:structured-macro ac:name="info" ac:schema-version="1">'
                '<ac:rich-text-body>'
                '<p>Diese Seite wurde mit <a href="https://bitbucket.lvm.de/bitbucket/users/m63119/repos/md2cf/browse">md2cf</a> automatisch aus Markdown generiert. '
                'Original-Datei: '
                '<ac:link>'
                f'<ri:attachment ri:filename="{filename_escaped}" />'
                '</ac:link>'
                '</p>'
                '<p><strong>CLI-Beispiel:</strong></p>'
                f'<pre>{cli_example}</pre>'
                '</ac:rich-text-body>'
                '</ac:structured-macro>\n'
            )
        else:
            # No attachment link
            return (
                '<ac:structured-macro ac:name="info" ac:schema-version="1">'
                '<ac:rich-text-body>'
                '<p>Diese Seite wurde mit <a href="https://bitbucket.lvm.de/bitbucket/users/m63119/repos/md2cf/browse">md2cf</a> automatisch aus Markdown generiert.</p>'
                '</ac:rich-text-body>'
                '</ac:structured-macro>\n'
            )

    def get_image_references(self) -> List[Dict[str, str]]:
        """
        Get list of image references found during conversion.

        Returns:
            List of dictionaries with 'url' and 'resolved_path' keys

        Example:
            >>> converter = MarkdownToConfluence(base_path="/docs")
            >>> result = converter.convert("![alt](image.png)", extract_images=True)
            >>> images = converter.get_image_references()
            >>> for img in images:
            ...     print(f"Image: {img['url']} -> {img['resolved_path']}")
        """
        return self.image_references.copy()

    def add_image_reference(self, url: str) -> None:
        """
        Add an image reference during conversion.

        Args:
            url: Image URL from markdown

        Note:
            This method is called internally by the renderer during conversion.
        """
        # Skip external URLs (http://, https://, etc.)
        if url.startswith(('http://', 'https://', '//', 'data:')):
            logger.debug(f"Skipping external/data URL: {url}")
            return

        # Resolve relative path if base_path is set
        resolved_path = None
        if self.base_path:
            img_path = self.base_path / url
            if img_path.exists():
                resolved_path = str(img_path.resolve())
                logger.debug(f"Resolved image path: {url} -> {resolved_path}")
            else:
                logger.warning(f"Image file not found: {img_path}")
        else:
            # Try to resolve relative to current directory
            img_path = Path(url)
            if img_path.exists():
                resolved_path = str(img_path.resolve())
                logger.debug(f"Resolved image path: {url} -> {resolved_path}")
            else:
                logger.warning(f"Image file not found: {url} (no base_path set)")

        self.image_references.append({
            'url': url,
            'resolved_path': resolved_path,
            'filename': Path(url).name
        })

    def convert_file(self, file_path: Union[str, Path]) -> str:
        """
        Convert a Markdown file to Confluence Storage Format.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Confluence Storage Format (XHTML) string

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file

        Example:
            >>> converter = MarkdownToConfluence()
            >>> result = converter.convert_file("README.md")
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"Markdown file not found: {path}")

        if not path.is_file():
            logger.error(f"Path is not a file: {path}")
            raise IOError(f"Path is not a file: {path}")

        logger.info(f"Converting file: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            return self.convert(markdown_content)
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise IOError(f"Error reading file {path}: {e}")

    def convert_and_save(
        self,
        markdown_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Convert a Markdown file and save the result to a file.

        Args:
            markdown_file: Path to the Markdown file
            output_file: Path to save the output (default: same name with .html extension)

        Returns:
            Path to the output file

        Example:
            >>> converter = MarkdownToConfluence()
            >>> output = converter.convert_and_save("README.md", "output.html")
            >>> print(f"Saved to: {output}")
        """
        markdown_path = Path(markdown_file)
        result = self.convert_file(markdown_path)

        if output_file is None:
            output_path = markdown_path.with_suffix(".html")
        else:
            output_path = Path(output_file)

        logger.info(f"Saving converted content to: {output_path}")

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
            logger.info(f"Successfully saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error writing to file {output_path}: {e}")
            raise IOError(f"Error writing to file {output_path}: {e}")


def convert_markdown_to_confluence(markdown_content: str) -> str:
    """
    Convenience function to convert Markdown to Confluence Storage Format.

    Args:
        markdown_content: Markdown text to convert

    Returns:
        Confluence Storage Format (XHTML) string

    Example:
        >>> from md2cf import convert_markdown_to_confluence
        >>> result = convert_markdown_to_confluence("# Title\\n\\nParagraph")
    """
    converter = MarkdownToConfluence()
    return converter.convert(markdown_content)
