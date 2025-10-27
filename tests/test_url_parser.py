"""
Tests for URL parsing utilities.
"""

import pytest

from md2cf.utils.url_parser import extract_page_id_from_url


class TestExtractPageIdFromUrl:
    """Tests for extract_page_id_from_url function."""

    def test_direct_page_id(self):
        """Test with direct page ID."""
        assert extract_page_id_from_url("123456") == "123456"
        assert extract_page_id_from_url("  789  ") == "789"

    def test_cloud_url_with_title(self):
        """Test Confluence Cloud URL with page title."""
        url = "https://mysite.atlassian.net/wiki/spaces/DEMO/pages/123456/My+Page+Title"
        assert extract_page_id_from_url(url) == "123456"

    def test_cloud_url_without_title(self):
        """Test Confluence Cloud URL without page title."""
        url = "https://mysite.atlassian.net/wiki/spaces/DEMO/pages/987654"
        assert extract_page_id_from_url(url) == "987654"

    def test_server_url_with_pageid_param(self):
        """Test Confluence Server URL with pageId query parameter."""
        url = "https://confluence.example.com/display/DEMO/Page+Title?pageId=555666"
        assert extract_page_id_from_url(url) == "555666"

    def test_viewpage_action_url(self):
        """Test viewpage.action URL format."""
        url = "https://confluence.example.com/pages/viewpage.action?pageId=111222"
        assert extract_page_id_from_url(url) == "111222"

    def test_url_with_additional_params(self):
        """Test URL with additional query parameters."""
        url = "https://confluence.example.com/display/SPACE/Page?pageId=333444&focusedCommentId=123"
        assert extract_page_id_from_url(url) == "333444"

    def test_url_with_encoded_title(self):
        """Test URL with URL-encoded title."""
        url = "https://mysite.atlassian.net/wiki/spaces/DEMO/pages/456789/Some%20Page%20Title"
        assert extract_page_id_from_url(url) == "456789"

    def test_invalid_url_no_page_id(self):
        """Test with URL that doesn't contain a page ID."""
        with pytest.raises(ValueError) as exc_info:
            extract_page_id_from_url("https://mysite.atlassian.net/wiki/spaces/DEMO")
        assert "Could not extract page ID" in str(exc_info.value)

    def test_invalid_url_format(self):
        """Test with invalid URL format."""
        with pytest.raises(ValueError) as exc_info:
            extract_page_id_from_url("not-a-valid-url-or-id")
        assert "Could not extract page ID" in str(exc_info.value)

    def test_empty_string(self):
        """Test with empty string."""
        with pytest.raises(ValueError) as exc_info:
            extract_page_id_from_url("")
        assert "Could not extract page ID" in str(exc_info.value)

    def test_url_with_hash(self):
        """Test URL with hash/fragment."""
        url = "https://mysite.atlassian.net/wiki/spaces/DEMO/pages/777888/Title#section"
        assert extract_page_id_from_url(url) == "777888"

    def test_server_url_without_wiki_prefix(self):
        """Test Server URL without /wiki prefix."""
        url = "https://confluence.example.com/pages/123456789"
        assert extract_page_id_from_url(url) == "123456789"

    def test_url_with_trailing_slash(self):
        """Test URL with trailing slash."""
        url = "https://mysite.atlassian.net/wiki/spaces/DEMO/pages/999000/"
        assert extract_page_id_from_url(url) == "999000"

    def test_multiple_digit_segments(self):
        """Test URL with multiple numeric segments (should extract from /pages/ path)."""
        url = "https://mysite.atlassian.net/wiki/spaces/123/pages/456789/Title"
        # Should extract the page ID after /pages/, not the space ID
        assert extract_page_id_from_url(url) == "456789"
