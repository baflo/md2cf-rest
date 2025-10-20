"""
Confluence API Client with PAT Authentication.

This module provides a client for interacting with Confluence REST API
using Personal Access Token (PAT) authentication.
"""

import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from atlassian import Confluence


logger = logging.getLogger(__name__)


class ConfluenceClient:
    """
    Client for Confluence REST API with PAT authentication.

    This class wraps the atlassian-python-api library and provides
    additional functionality for page management.
    """

    def __init__(
        self,
        url: str,
        token: str,
        cloud: bool = True,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize Confluence client.

        Args:
            url: Confluence base URL (e.g., https://yoursite.atlassian.net)
            token: Personal Access Token for authentication
            cloud: Whether using Confluence Cloud (True) or Server/Data Center (False)
            verify_ssl: Whether to verify SSL certificates

        Example:
            >>> client = ConfluenceClient(
            ...     url="https://yoursite.atlassian.net",
            ...     token="your-pat-token",
            ...     cloud=True
            ... )
        """
        self.url = url.rstrip("/")
        self.token = token
        self.cloud = cloud
        self.verify_ssl = verify_ssl

        # Initialize atlassian-python-api Confluence client
        self.confluence = Confluence(
            url=self.url,
            token=self.token,
            cloud=self.cloud,
            verify_ssl=self.verify_ssl,
        )

        logger.info(f"Initialized Confluence client for {self.url}")

    def get_page_by_title(
        self,
        space: str,
        title: str,
        expand: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a page by title in a specific space.

        Args:
            space: Space key
            title: Page title
            expand: Optional comma-separated list of properties to expand

        Returns:
            Page data dictionary or None if not found

        Example:
            >>> page = client.get_page_by_title("DEMO", "My Page")
            >>> if page:
            ...     print(f"Page ID: {page['id']}")
        """
        try:
            result = self.confluence.get_page_by_title(
                space=space,
                title=title,
                expand=expand or "version,body.storage",
            )
            if result:
                logger.info(f"Found page '{title}' in space '{space}' (ID: {result['id']})")
                return result
            logger.warning(f"Page '{title}' not found in space '{space}'")
            return None
        except Exception as e:
            logger.error(f"Error getting page '{title}': {e}")
            raise

    def create_page(
        self,
        space: str,
        title: str,
        body: str,
        parent_id: Optional[str] = None,
        representation: str = "storage",
    ) -> Dict[str, Any]:
        """
        Create a new page in Confluence.

        Args:
            space: Space key
            title: Page title
            body: Page content in storage format
            parent_id: Optional parent page ID
            representation: Content representation (default: "storage")

        Returns:
            Created page data dictionary

        Example:
            >>> page = client.create_page(
            ...     space="DEMO",
            ...     title="My New Page",
            ...     body="<p>Hello World</p>"
            ... )
            >>> print(f"Created page with ID: {page['id']}")
        """
        try:
            result = self.confluence.create_page(
                space=space,
                title=title,
                body=body,
                parent_id=parent_id,
                type="page",
                representation=representation,
            )
            logger.info(f"Created page '{title}' in space '{space}' (ID: {result['id']})")
            return result
        except Exception as e:
            logger.error(f"Error creating page '{title}': {e}")
            raise

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        parent_id: Optional[str] = None,
        representation: str = "storage",
        minor_edit: bool = False,
    ) -> Dict[str, Any]:
        """
        Update an existing page in Confluence.

        Args:
            page_id: Page ID to update
            title: New page title
            body: New page content in storage format
            parent_id: Optional parent page ID
            representation: Content representation (default: "storage")
            minor_edit: Whether this is a minor edit

        Returns:
            Updated page data dictionary

        Example:
            >>> page = client.update_page(
            ...     page_id="123456",
            ...     title="Updated Title",
            ...     body="<p>Updated content</p>"
            ... )
        """
        try:
            # Get current page version
            current_page = self.confluence.get_page_by_id(
                page_id=page_id,
                expand="version",
            )
            current_version = current_page["version"]["number"]

            result = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=body,
                parent_id=parent_id,
                type="page",
                representation=representation,
                minor_edit=minor_edit,
                version_comment=f"Updated from markdown (v{current_version} -> v{current_version + 1})",
            )
            logger.info(f"Updated page '{title}' (ID: {page_id})")
            return result
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {e}")
            raise

    def create_or_update_page(
        self,
        space: str,
        title: str,
        body: str,
        parent_id: Optional[str] = None,
        representation: str = "storage",
    ) -> Dict[str, Any]:
        """
        Create a new page or update if it already exists.

        Args:
            space: Space key
            title: Page title
            body: Page content in storage format
            parent_id: Optional parent page ID
            representation: Content representation (default: "storage")

        Returns:
            Page data dictionary (created or updated)

        Example:
            >>> page = client.create_or_update_page(
            ...     space="DEMO",
            ...     title="My Page",
            ...     body="<p>Content</p>"
            ... )
            >>> print(f"Page URL: {page['_links']['base'] + page['_links']['webui']}")
        """
        existing_page = self.get_page_by_title(space=space, title=title)

        if existing_page:
            logger.info(f"Page '{title}' exists, updating...")
            return self.update_page(
                page_id=existing_page["id"],
                title=title,
                body=body,
                parent_id=parent_id,
                representation=representation,
            )
        else:
            logger.info(f"Page '{title}' does not exist, creating...")
            return self.create_page(
                space=space,
                title=title,
                body=body,
                parent_id=parent_id,
                representation=representation,
            )

    def get_page_url(self, page: Dict[str, Any]) -> str:
        """
        Get the full URL for a page.

        Args:
            page: Page data dictionary

        Returns:
            Full page URL

        Example:
            >>> page = client.get_page_by_title("DEMO", "My Page")
            >>> url = client.get_page_url(page)
            >>> print(f"View at: {url}")
        """
        base_url = page.get("_links", {}).get("base", self.url)
        web_ui = page.get("_links", {}).get("webui", "")
        return urljoin(base_url, web_ui)

    def delete_page(self, page_id: str) -> None:
        """
        Delete a page from Confluence.

        Args:
            page_id: Page ID to delete

        Example:
            >>> client.delete_page("123456")
        """
        try:
            self.confluence.remove_page(page_id=page_id)
            logger.info(f"Deleted page with ID: {page_id}")
        except Exception as e:
            logger.error(f"Error deleting page {page_id}: {e}")
            raise

    def get_space(self, space_key: str) -> Optional[Dict[str, Any]]:
        """
        Get space information.

        Args:
            space_key: Space key

        Returns:
            Space data dictionary or None if not found

        Example:
            >>> space = client.get_space("DEMO")
            >>> if space:
            ...     print(f"Space name: {space['name']}")
        """
        try:
            result = self.confluence.get_space(space_key=space_key)
            if result:
                logger.info(f"Found space '{space_key}'")
                return result
            return None
        except Exception as e:
            logger.error(f"Error getting space '{space_key}': {e}")
            raise
