"""
Frontmatter utilities for md2cf.

This module provides utilities for handling YAML frontmatter in Markdown files.
Frontmatter is used to store metadata about Confluence pages.
"""

import re
from typing import Dict, Any, Tuple, Optional
import yaml
import logging

logger = logging.getLogger(__name__)


class FrontmatterMetadata:
    """Container for Confluence page metadata stored in frontmatter."""

    def __init__(
        self,
        page_id: Optional[str] = None,
        space_key: Optional[str] = None,
        title: Optional[str] = None,
        version: Optional[int] = None,
        parent_id: Optional[str] = None,
    ):
        """
        Initialize frontmatter metadata.

        Args:
            page_id: Confluence page ID
            space_key: Confluence space key
            title: Page title
            version: Page version number
            parent_id: Parent page ID
        """
        self.page_id = page_id
        self.space_key = space_key
        self.title = title
        self.version = version
        self.parent_id = parent_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for YAML serialization."""
        result = {}
        if self.page_id:
            result['confluence_page_id'] = self.page_id
        if self.space_key:
            result['confluence_space_key'] = self.space_key
        if self.title:
            result['confluence_title'] = self.title
        if self.version is not None:
            result['confluence_version'] = self.version
        if self.parent_id:
            result['confluence_parent_id'] = self.parent_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FrontmatterMetadata':
        """Create metadata from dictionary."""
        return cls(
            page_id=data.get('confluence_page_id'),
            space_key=data.get('confluence_space_key'),
            title=data.get('confluence_title'),
            version=data.get('confluence_version'),
            parent_id=data.get('confluence_parent_id'),
        )

    def has_metadata(self) -> bool:
        """Check if any metadata is present."""
        return any([
            self.page_id,
            self.space_key,
            self.title,
            self.version is not None,
            self.parent_id,
        ])


def extract_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Extract YAML frontmatter from Markdown content.

    Frontmatter is expected to be at the beginning of the file, delimited by '---'.

    Example:
        ---
        confluence_page_id: "123456"
        confluence_space_key: "DEMO"
        confluence_title: "My Page"
        confluence_version: 5
        ---
        # Page Content

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        Tuple of (frontmatter dict or None, content without frontmatter)
    """
    # Pattern to match frontmatter: starts with ---, contains YAML, ends with ---
    pattern = r'^---\s*\n(.*?\n)---\s*\n'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return None, content

    try:
        # Extract and parse YAML
        yaml_content = match.group(1)
        frontmatter = yaml.safe_load(yaml_content)

        # Remove frontmatter from content
        content_without_frontmatter = content[match.end():]

        logger.debug(f"Extracted frontmatter: {frontmatter}")
        return frontmatter, content_without_frontmatter

    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse frontmatter YAML: {e}")
        return None, content


def add_frontmatter(content: str, metadata: FrontmatterMetadata) -> str:
    """
    Add or update YAML frontmatter in Markdown content.

    If frontmatter already exists, it will be replaced with new metadata.
    Confluence-specific metadata will be added/updated while preserving
    other frontmatter fields.

    Args:
        content: Markdown content
        metadata: Confluence page metadata to add

    Returns:
        Content with frontmatter
    """
    # Extract existing frontmatter if present
    existing_frontmatter, content_without_frontmatter = extract_frontmatter(content)

    # Merge with existing frontmatter (Confluence metadata takes precedence)
    if existing_frontmatter:
        frontmatter_dict = existing_frontmatter.copy()
    else:
        frontmatter_dict = {}

    # Update with new Confluence metadata
    frontmatter_dict.update(metadata.to_dict())

    # Generate YAML frontmatter
    if frontmatter_dict:
        yaml_str = yaml.safe_dump(
            frontmatter_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )
        frontmatter_block = f"---\n{yaml_str}---\n\n"
        return frontmatter_block + content_without_frontmatter

    return content


def parse_frontmatter_metadata(content: str) -> Tuple[FrontmatterMetadata, str]:
    """
    Parse Confluence metadata from frontmatter.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        Tuple of (FrontmatterMetadata, content without frontmatter)
    """
    frontmatter, content_without_frontmatter = extract_frontmatter(content)

    if frontmatter:
        metadata = FrontmatterMetadata.from_dict(frontmatter)
    else:
        metadata = FrontmatterMetadata()

    return metadata, content_without_frontmatter
