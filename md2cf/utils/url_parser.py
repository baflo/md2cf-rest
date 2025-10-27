"""
URL parsing utilities for extracting Confluence page IDs from URLs.

This module provides functions to extract page IDs from various Confluence URL formats.
"""

import re
from typing import Optional
from urllib.parse import parse_qs, urlparse


def extract_page_id_from_url(url_or_id: str) -> str:
    """
    Extract page ID from a Confluence URL or return the ID if already provided.

    Supports multiple Confluence URL formats:
    - https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
    - https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456
    - https://domain.atlassian.net/wiki/display/SPACE/Page+Title?pageId=123456
    - https://confluence.domain.com/display/SPACE/Page+Title?pageId=123456
    - https://confluence.domain.com/pages/viewpage.action?pageId=123456
    - Direct page ID: 123456

    Args:
        url_or_id: Confluence page URL or page ID

    Returns:
        Extracted page ID as string

    Raises:
        ValueError: If no page ID could be extracted from the URL

    Examples:
        >>> extract_page_id_from_url("123456")
        '123456'
        >>> extract_page_id_from_url("https://site.atlassian.net/wiki/spaces/DEMO/pages/123456/Title")
        '123456'
        >>> extract_page_id_from_url("https://confluence.com/display/DEMO/Title?pageId=123456")
        '123456'
    """
    # If it's already just a numeric ID, return it
    if url_or_id.strip().isdigit():
        return url_or_id.strip()

    # Parse the URL
    parsed = urlparse(url_or_id)

    # Try to extract from query parameters (e.g., ?pageId=123456)
    if parsed.query:
        query_params = parse_qs(parsed.query)
        if 'pageId' in query_params:
            page_id = query_params['pageId'][0]
            if page_id.isdigit():
                return page_id

    # Try to extract from path patterns
    path = parsed.path

    # Pattern 1: /wiki/spaces/SPACE/pages/123456/Page+Title
    # Pattern 2: /wiki/spaces/SPACE/pages/123456
    match = re.search(r'/pages/(\d+)(?:/|$)', path)
    if match:
        return match.group(1)

    # Pattern 3: /display/SPACE/Page+Title with pageId in fragment
    # Some URLs might have pageId in the fragment
    if parsed.fragment:
        match = re.search(r'pageId[=:](\d+)', parsed.fragment)
        if match:
            return match.group(1)

    # If we couldn't extract an ID, raise an error
    raise ValueError(
        f"Could not extract page ID from: {url_or_id}\n"
        f"Expected formats:\n"
        f"  - Direct ID: 123456\n"
        f"  - /wiki/spaces/SPACE/pages/123456/Title\n"
        f"  - /display/SPACE/Title?pageId=123456\n"
        f"  - /pages/viewpage.action?pageId=123456"
    )
