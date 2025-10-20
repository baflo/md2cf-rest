"""
Markdown to Confluence Converter.

This module provides the main conversion functionality from Markdown
to Confluence Storage Format.
"""

import logging
from pathlib import Path
from typing import Optional, Union

import mistune

from md2cf.renderers.confluence import ConfluenceStorageFormatRenderer


logger = logging.getLogger(__name__)


class MarkdownToConfluence:
    """
    Converter for transforming Markdown to Confluence Storage Format.

    This class uses Mistune with a custom renderer to convert Markdown
    content into Confluence-compatible XHTML.
    """

    def __init__(self) -> None:
        """Initialize the converter with Confluence renderer."""
        self.renderer = ConfluenceStorageFormatRenderer()
        self.markdown = mistune.create_markdown(
            renderer=self.renderer,
            plugins=[
                "strikethrough",
                "table",
                "url",
                "task_lists",
            ],
        )
        logger.debug("Initialized MarkdownToConfluence converter")

    def convert(self, markdown_content: str) -> str:
        """
        Convert Markdown string to Confluence Storage Format.

        Args:
            markdown_content: Markdown text to convert

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

        logger.debug(f"Converting {len(markdown_content)} characters of Markdown")
        result = self.markdown(markdown_content)

        if isinstance(result, str):
            logger.debug(f"Converted to {len(result)} characters of Confluence format")
            return result
        else:
            logger.error(f"Unexpected conversion result type: {type(result)}")
            return str(result)

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
