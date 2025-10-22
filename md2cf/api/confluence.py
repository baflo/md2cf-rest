"""
Confluence API Client with PAT Authentication.

This module provides a client for interacting with Confluence REST API
using Personal Access Token (PAT) authentication.
"""

import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

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

    def get_page_by_id(
        self,
        page_id: str,
        expand: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a page by ID.

        Args:
            page_id: Page ID
            expand: Optional comma-separated list of properties to expand

        Returns:
            Page data dictionary or None if not found

        Example:
            >>> page = client.get_page_by_id("123456")
            >>> if page:
            ...     print(f"Page title: {page['title']}")
        """
        try:
            result = self.confluence.get_page_by_id(
                page_id=page_id,
                expand=expand or "version,space,ancestors,history",
            )
            if result:
                logger.info(f"Found page with ID {page_id}: '{result.get('title')}'")
                return result
            logger.warning(f"Page with ID {page_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting page by ID {page_id}: {e}")
            raise

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
                # parent_id=parent_id,
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
        base_url = page.get("_links", {}).get("base", self.url) + "/"
        web_ui = "./" + page.get("_links", {}).get("webui", "")
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

    def get_spaces(
        self,
        search_query: Optional[str] = None,
        limit: int = 25,
    ) -> list[Dict[str, Any]]:
        """
        Get list of spaces accessible to the user.

        Args:
            search_query: Optional search filter for space name or key
            limit: Maximum number of spaces to return

        Returns:
            List of space data dictionaries

        Example:
            >>> spaces = client.get_spaces(search_query="DEMO", limit=10)
            >>> for space in spaces:
            ...     print(f"{space['key']}: {space['name']}")
        """
        try:
            # Build params dict only if search_query is provided
            params = {'query': search_query} if search_query else {}
            all_spaces = self.confluence.get("/rest/spacedirectory/1/search", None, None, params)

            if not all_spaces or "spaces" not in all_spaces:
                logger.warning("No spaces found")
                return []

            spaces = all_spaces["spaces"]

            logger.info(f"Found {len(spaces)} spaces")
            return spaces[:limit]

        except Exception as e:
            logger.error(f"Error getting spaces: {e}")
            raise

    def search_pages(
        self,
        query: str,
        space: Optional[str] = None,
        limit: int = 25,
    ) -> list[Dict[str, Any]]:
        """
        Search for pages using CQL (Confluence Query Language).

        Args:
            query: Search query (title or text search)
            space: Optional space key to restrict search
            limit: Maximum number of results to return

        Returns:
            List of page data dictionaries

        Example:
            >>> pages = client.search_pages("documentation", space="DEMO", limit=10)
            >>> for page in pages:
            ...     print(f"{page['title']} (ID: {page['id']})")
        """
        try:
            # Build CQL query
            cql_parts = [f'type=page']

            # Add text search for title or content
            if query:
                # Escape special characters in CQL
                escaped_query = query.replace('"', '\\"')
                cql_parts.append(f'({" OR ".join(filter(str.strip, (
                    f'title ~ "{escaped_query}"',
                    f'title ~ "{escaped_query}*"',
                    f'text ~ "{escaped_query}"',
                    f'text ~ "{escaped_query}*"',
                    escaped_query.isdigit() and f'id = {escaped_query}' or '',
                    )))})')

            # Add space restriction if provided
            if space:
                cql_parts.append(f'space="{space}"')

            cql = ' AND '.join(cql_parts)

            logger.info(f"Searching pages with CQL: {cql}")

            # Use Confluence search API
            result = self.confluence.cql(
                cql=cql,
                limit=limit,
                expand="space,version,body.view"
            )

            pages = result.get("results", [])
            logger.info(f"Found {len(pages)} pages")

            return pages

        except Exception as e:
            logger.error(f"Error searching pages: {e}")
            raise

    def attach_file(
        self,
        page_id: str,
        file_path: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Attach a file to a Confluence page.

        Args:
            page_id: Page ID to attach file to
            file_path: Path to the file to attach
            comment: Optional comment for the attachment

        Returns:
            Attachment data dictionary

        Example:
            >>> attachment = client.attach_file(
            ...     page_id="123456",
            ...     file_path="/path/to/image.png",
            ...     comment="Updated diagram"
            ... )
            >>> print(f"Attached: {attachment['title']}")
        """
        try:
            from pathlib import Path
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            filename = path.name

            result = self.confluence.attach_file(
                filename=str(path),
                page_id=page_id,
                comment=comment,
            )

            logger.info(f"Attached file '{filename}' to page {page_id}")
            return result
        except Exception as e:
            logger.error(f"Error attaching file {file_path} to page {page_id}: {e}")
            raise

    def get_attachments(
        self,
        page_id: str,
    ) -> list[Dict[str, Any]]:
        """
        Get all attachments for a page.

        Args:
            page_id: Page ID

        Returns:
            List of attachment data dictionaries

        Example:
            >>> attachments = client.get_attachments("123456")
            >>> for att in attachments:
            ...     print(f"{att['title']} - {att['id']}")
        """
        try:
            result = self.confluence.get_attachments_from_content(
                page_id=page_id,
            )
            attachments = result.get("results", [])
            logger.info(f"Found {len(attachments)} attachments for page {page_id}")
            return attachments
        except Exception as e:
            logger.error(f"Error getting attachments for page {page_id}: {e}")
            raise

    def delete_attachment(
        self,
        page_id: str,
        attachment_id: str,
    ) -> None:
        """
        Delete an attachment from a page.

        Args:
            page_id: Page ID
            attachment_id: Attachment ID to delete

        Example:
            >>> client.delete_attachment("123456", "att_789")
        """
        try:
            self.confluence.delete_attachment(
                page_id=page_id,
                attachment_id=attachment_id,
            )
            logger.info(f"Deleted attachment {attachment_id} from page {page_id}")
        except Exception as e:
            logger.error(f"Error deleting attachment {attachment_id}: {e}")
            raise
