"""
md2cf - Convert Markdown to Confluence Storage Format

A Python library and CLI tool to convert Markdown files to Confluence Storage Format
and publish them to Confluence using the REST API with PAT authentication.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from md2cf.converter import MarkdownToConfluence
from md2cf.renderers.confluence import ConfluenceStorageFormatRenderer

__all__ = ["MarkdownToConfluence", "ConfluenceStorageFormatRenderer"]
