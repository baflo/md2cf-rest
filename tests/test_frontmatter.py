"""Tests for frontmatter utilities."""

import pytest

from md2cf.utils.frontmatter import (
    FrontmatterMetadata,
    extract_frontmatter,
    add_frontmatter,
    parse_frontmatter_metadata,
)


class TestFrontmatterMetadata:
    """Test FrontmatterMetadata class."""

    def test_init_empty(self):
        """Test initialization with no parameters."""
        metadata = FrontmatterMetadata()
        assert metadata.page_id is None
        assert metadata.space_key is None
        assert metadata.title is None
        assert metadata.version is None
        assert metadata.parent_id is None

    def test_init_with_values(self):
        """Test initialization with all parameters."""
        metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
            title="Test Page",
            version=5,
            parent_id="654321",
        )
        assert metadata.page_id == "123456"
        assert metadata.space_key == "DEMO"
        assert metadata.title == "Test Page"
        assert metadata.version == 5
        assert metadata.parent_id == "654321"

    def test_to_dict_empty(self):
        """Test converting empty metadata to dict."""
        metadata = FrontmatterMetadata()
        result = metadata.to_dict()
        assert result == {}

    def test_to_dict_with_values(self):
        """Test converting metadata with values to dict."""
        metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
            title="Test Page",
            version=5,
            parent_id="654321",
        )
        result = metadata.to_dict()
        assert result == {
            "confluence_page_id": "123456",
            "confluence_space_key": "DEMO",
            "confluence_title": "Test Page",
            "confluence_version": 5,
            "confluence_parent_id": "654321",
        }

    def test_to_dict_partial(self):
        """Test converting partial metadata to dict."""
        metadata = FrontmatterMetadata(
            page_id="123456",
            title="Test Page",
        )
        result = metadata.to_dict()
        assert result == {
            "confluence_page_id": "123456",
            "confluence_title": "Test Page",
        }

    def test_from_dict_empty(self):
        """Test creating metadata from empty dict."""
        metadata = FrontmatterMetadata.from_dict({})
        assert metadata.page_id is None
        assert metadata.space_key is None
        assert metadata.title is None
        assert metadata.version is None
        assert metadata.parent_id is None

    def test_from_dict_with_values(self):
        """Test creating metadata from dict with values."""
        data = {
            "confluence_page_id": "123456",
            "confluence_space_key": "DEMO",
            "confluence_title": "Test Page",
            "confluence_version": 5,
            "confluence_parent_id": "654321",
        }
        metadata = FrontmatterMetadata.from_dict(data)
        assert metadata.page_id == "123456"
        assert metadata.space_key == "DEMO"
        assert metadata.title == "Test Page"
        assert metadata.version == 5
        assert metadata.parent_id == "654321"

    def test_has_metadata_empty(self):
        """Test has_metadata with empty metadata."""
        metadata = FrontmatterMetadata()
        assert not metadata.has_metadata()

    def test_has_metadata_with_page_id(self):
        """Test has_metadata with page_id."""
        metadata = FrontmatterMetadata(page_id="123456")
        assert metadata.has_metadata()

    def test_has_metadata_with_version(self):
        """Test has_metadata with version."""
        metadata = FrontmatterMetadata(version=5)
        assert metadata.has_metadata()


class TestExtractFrontmatter:
    """Test extract_frontmatter function."""

    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        content = "# Hello\n\nThis is content."
        frontmatter, remaining = extract_frontmatter(content)
        assert frontmatter is None
        assert remaining == content

    def test_valid_frontmatter(self):
        """Test content with valid frontmatter."""
        content = """---
confluence_page_id: "123456"
confluence_space_key: "DEMO"
---
# Hello

This is content."""
        frontmatter, remaining = extract_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter["confluence_page_id"] == "123456"
        assert frontmatter["confluence_space_key"] == "DEMO"
        assert remaining == "# Hello\n\nThis is content."

    def test_frontmatter_with_all_fields(self):
        """Test frontmatter with all fields."""
        content = """---
confluence_page_id: "123456"
confluence_space_key: "DEMO"
confluence_title: "Test Page"
confluence_version: 5
confluence_parent_id: "654321"
---
Content here."""
        frontmatter, remaining = extract_frontmatter(content)
        assert frontmatter["confluence_page_id"] == "123456"
        assert frontmatter["confluence_space_key"] == "DEMO"
        assert frontmatter["confluence_title"] == "Test Page"
        assert frontmatter["confluence_version"] == 5
        assert frontmatter["confluence_parent_id"] == "654321"
        assert remaining == "Content here."

    def test_frontmatter_with_extra_fields(self):
        """Test frontmatter with extra non-Confluence fields."""
        content = """---
confluence_page_id: "123456"
author: "John Doe"
date: "2024-01-01"
---
Content."""
        frontmatter, remaining = extract_frontmatter(content)
        assert frontmatter["confluence_page_id"] == "123456"
        assert frontmatter["author"] == "John Doe"
        assert frontmatter["date"] == "2024-01-01"

    def test_invalid_yaml(self):
        """Test content with invalid YAML frontmatter."""
        content = """---
this is: [not valid yaml
---
Content."""
        frontmatter, remaining = extract_frontmatter(content)
        # Should return None and original content on YAML error
        assert frontmatter is None
        assert remaining == content

    def test_frontmatter_not_at_start(self):
        """Test frontmatter not at the beginning."""
        content = """Some content first
---
confluence_page_id: "123456"
---
More content."""
        frontmatter, remaining = extract_frontmatter(content)
        # Should not match frontmatter
        assert frontmatter is None
        assert remaining == content

    def test_empty_frontmatter(self):
        """Test empty frontmatter block."""
        content = """---
---
Content."""
        frontmatter, remaining = extract_frontmatter(content)
        assert frontmatter is None or frontmatter == {}
        assert "Content." in remaining


class TestAddFrontmatter:
    """Test add_frontmatter function."""

    def test_add_to_content_without_frontmatter(self):
        """Test adding frontmatter to content without existing frontmatter."""
        content = "# Hello\n\nContent here."
        metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
            title="Test Page",
        )
        result = add_frontmatter(content, metadata)

        assert result.startswith("---\n")
        assert "confluence_page_id: '123456'" in result
        assert "confluence_space_key: DEMO" in result
        assert "confluence_title: Test Page" in result
        assert "# Hello\n\nContent here." in result

    def test_add_to_content_with_existing_frontmatter(self):
        """Test adding frontmatter to content with existing frontmatter."""
        content = """---
author: "John Doe"
---
# Hello"""
        metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
        )
        result = add_frontmatter(content, metadata)

        # Should merge frontmatter
        assert "confluence_page_id: '123456'" in result
        assert "author: John Doe" in result
        assert "# Hello" in result

    def test_update_existing_confluence_metadata(self):
        """Test updating existing Confluence metadata."""
        content = """---
confluence_page_id: "111111"
confluence_version: 3
author: "John Doe"
---
Content"""
        metadata = FrontmatterMetadata(
            page_id="123456",
            version=5,
        )
        result = add_frontmatter(content, metadata)

        # Confluence metadata should be updated
        assert "confluence_page_id: '123456'" in result
        assert "confluence_version: 5" in result
        # Other metadata should be preserved
        assert "author: John Doe" in result

    def test_empty_metadata(self):
        """Test adding empty metadata."""
        content = "# Content"
        metadata = FrontmatterMetadata()
        result = add_frontmatter(content, metadata)

        # Should return content unchanged
        assert result == content

    def test_metadata_with_all_fields(self):
        """Test adding metadata with all fields."""
        content = "Content"
        metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
            title="Test Page",
            version=5,
            parent_id="654321",
        )
        result = add_frontmatter(content, metadata)

        assert "confluence_page_id: '123456'" in result
        assert "confluence_space_key: DEMO" in result
        assert "confluence_title: Test Page" in result
        assert "confluence_version: 5" in result
        assert "confluence_parent_id: '654321'" in result


class TestParseFrontmatterMetadata:
    """Test parse_frontmatter_metadata function."""

    def test_parse_content_without_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "# Hello\n\nContent"
        metadata, remaining = parse_frontmatter_metadata(content)

        assert isinstance(metadata, FrontmatterMetadata)
        assert not metadata.has_metadata()
        assert remaining == content

    def test_parse_content_with_frontmatter(self):
        """Test parsing content with frontmatter."""
        content = """---
confluence_page_id: "123456"
confluence_space_key: "DEMO"
confluence_title: "Test Page"
confluence_version: 5
confluence_parent_id: "654321"
---
# Content"""
        metadata, remaining = parse_frontmatter_metadata(content)

        assert metadata.page_id == "123456"
        assert metadata.space_key == "DEMO"
        assert metadata.title == "Test Page"
        assert metadata.version == 5
        assert metadata.parent_id == "654321"
        assert remaining == "# Content"

    def test_parse_partial_frontmatter(self):
        """Test parsing content with partial frontmatter."""
        content = """---
confluence_page_id: "123456"
confluence_title: "Test"
---
Content"""
        metadata, remaining = parse_frontmatter_metadata(content)

        assert metadata.page_id == "123456"
        assert metadata.title == "Test"
        assert metadata.space_key is None
        assert metadata.version is None
        assert metadata.parent_id is None

    def test_parse_frontmatter_with_extra_fields(self):
        """Test parsing frontmatter with non-Confluence fields."""
        content = """---
confluence_page_id: "123456"
author: "John Doe"
tags:
  - tag1
  - tag2
---
Content"""
        metadata, remaining = parse_frontmatter_metadata(content)

        # Should only extract Confluence fields
        assert metadata.page_id == "123456"
        assert metadata.space_key is None

    def test_roundtrip_conversion(self):
        """Test roundtrip: add frontmatter then parse it back."""
        original_content = "# Test Content"
        original_metadata = FrontmatterMetadata(
            page_id="123456",
            space_key="DEMO",
            title="Test Page",
            version=5,
            parent_id="654321",
        )

        # Add frontmatter
        with_frontmatter = add_frontmatter(original_content, original_metadata)

        # Parse it back
        parsed_metadata, parsed_content = parse_frontmatter_metadata(with_frontmatter)

        # Check metadata matches
        assert parsed_metadata.page_id == original_metadata.page_id
        assert parsed_metadata.space_key == original_metadata.space_key
        assert parsed_metadata.title == original_metadata.title
        assert parsed_metadata.version == original_metadata.version
        assert parsed_metadata.parent_id == original_metadata.parent_id

        # Check content matches
        assert parsed_content == original_content
