"""Tests for the Confluence API client."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from md2cf.api.confluence import ConfluenceClient


@pytest.fixture
def mock_confluence() -> Mock:
    """Create a mock Confluence instance."""
    return MagicMock()


@pytest.fixture
def client(mock_confluence: Mock) -> ConfluenceClient:
    """Create a ConfluenceClient with mocked Confluence."""
    with patch("md2cf.api.confluence.Confluence", return_value=mock_confluence):
        client = ConfluenceClient(
            url="https://test.atlassian.net",
            token="test-token",
            cloud=True,
        )
        client.confluence = mock_confluence
        return client


class TestClientInitialization:
    """Test client initialization."""

    def test_init_cloud(self) -> None:
        """Test initialization for Confluence Cloud."""
        with patch("md2cf.api.confluence.Confluence") as mock_conf:
            client = ConfluenceClient(
                url="https://test.atlassian.net",
                token="test-token",
                cloud=True,
            )
            mock_conf.assert_called_once_with(
                url="https://test.atlassian.net",
                token="test-token",
                cloud=True,
                verify_ssl=True,
            )

    def test_init_server(self) -> None:
        """Test initialization for Confluence Server."""
        with patch("md2cf.api.confluence.Confluence") as mock_conf:
            client = ConfluenceClient(
                url="https://confluence.internal.com",
                token="test-token",
                cloud=False,
            )
            mock_conf.assert_called_once_with(
                url="https://confluence.internal.com",
                token="test-token",
                cloud=False,
                verify_ssl=True,
            )

    def test_init_no_ssl_verify(self) -> None:
        """Test initialization with SSL verification disabled."""
        with patch("md2cf.api.confluence.Confluence") as mock_conf:
            client = ConfluenceClient(
                url="https://test.atlassian.net",
                token="test-token",
                verify_ssl=False,
            )
            mock_conf.assert_called_once_with(
                url="https://test.atlassian.net",
                token="test-token",
                cloud=True,
                verify_ssl=False,
            )


class TestGetPageByTitle:
    """Test getting page by title."""

    def test_get_existing_page(self, client: ConfluenceClient, mock_confluence: Mock) -> None:
        """Test getting an existing page."""
        mock_page = {"id": "12345", "title": "Test Page"}
        mock_confluence.get_page_by_title.return_value = mock_page

        result = client.get_page_by_title("DEMO", "Test Page")

        assert result == mock_page
        mock_confluence.get_page_by_title.assert_called_once_with(
            space="DEMO",
            title="Test Page",
            expand="version,body.storage",
        )

    def test_get_nonexistent_page(self, client: ConfluenceClient, mock_confluence: Mock) -> None:
        """Test getting a non-existent page."""
        mock_confluence.get_page_by_title.return_value = None

        result = client.get_page_by_title("DEMO", "Nonexistent")

        assert result is None

    def test_get_page_with_custom_expand(
        self, client: ConfluenceClient, mock_confluence: Mock
    ) -> None:
        """Test getting page with custom expand parameter."""
        mock_page = {"id": "12345"}
        mock_confluence.get_page_by_title.return_value = mock_page

        client.get_page_by_title("DEMO", "Test", expand="version,ancestors")

        mock_confluence.get_page_by_title.assert_called_once_with(
            space="DEMO",
            title="Test",
            expand="version,ancestors",
        )


class TestCreatePage:
    """Test creating pages."""

    def test_create_page_basic(self, client: ConfluenceClient, mock_confluence: Mock) -> None:
        """Test creating a basic page."""
        mock_result = {"id": "12345", "title": "New Page"}
        mock_confluence.create_page.return_value = mock_result

        result = client.create_page(
            space="DEMO",
            title="New Page",
            body="<p>Content</p>",
        )

        assert result == mock_result
        mock_confluence.create_page.assert_called_once_with(
            space="DEMO",
            title="New Page",
            body="<p>Content</p>",
            parent_id=None,
            type="page",
            representation="storage",
        )

    def test_create_page_with_parent(
        self, client: ConfluenceClient, mock_confluence: Mock
    ) -> None:
        """Test creating a page with parent."""
        mock_result = {"id": "12345"}
        mock_confluence.create_page.return_value = mock_result

        client.create_page(
            space="DEMO",
            title="Child Page",
            body="<p>Content</p>",
            parent_id="99999",
        )

        mock_confluence.create_page.assert_called_once()
        call_args = mock_confluence.create_page.call_args
        assert call_args[1]["parent_id"] == "99999"


class TestUpdatePage:
    """Test updating pages."""

    def test_update_page(self, client: ConfluenceClient, mock_confluence: Mock) -> None:
        """Test updating a page."""
        # Mock get_page_by_id
        mock_current_page = {"id": "12345", "version": {"number": 5}}
        mock_confluence.get_page_by_id.return_value = mock_current_page

        # Mock update_page
        mock_result = {"id": "12345", "version": {"number": 6}}
        mock_confluence.update_page.return_value = mock_result

        result = client.update_page(
            page_id="12345",
            title="Updated Title",
            body="<p>Updated content</p>",
        )

        assert result == mock_result
        mock_confluence.get_page_by_id.assert_called_once_with(
            page_id="12345",
            expand="version",
        )
        mock_confluence.update_page.assert_called_once()


class TestCreateOrUpdatePage:
    """Test create or update page."""

    def test_create_when_not_exists(
        self, client: ConfluenceClient, mock_confluence: Mock
    ) -> None:
        """Test creating page when it doesn't exist."""
        # Page doesn't exist
        mock_confluence.get_page_by_title.return_value = None

        # Mock create
        mock_result = {"id": "12345"}
        mock_confluence.create_page.return_value = mock_result

        result = client.create_or_update_page(
            space="DEMO",
            title="New Page",
            body="<p>Content</p>",
        )

        assert result == mock_result
        mock_confluence.create_page.assert_called_once()

    def test_update_when_exists(self, client: ConfluenceClient, mock_confluence: Mock) -> None:
        """Test updating page when it exists."""
        # Page exists
        existing_page = {"id": "12345", "version": {"number": 3}}
        mock_confluence.get_page_by_title.return_value = existing_page
        mock_confluence.get_page_by_id.return_value = existing_page

        # Mock update
        mock_result = {"id": "12345", "version": {"number": 4}}
        mock_confluence.update_page.return_value = mock_result

        result = client.create_or_update_page(
            space="DEMO",
            title="Existing Page",
            body="<p>Updated</p>",
        )

        assert result == mock_result
        mock_confluence.update_page.assert_called_once()


class TestPageURL:
    """Test getting page URL."""

    def test_get_page_url(self, client: ConfluenceClient) -> None:
        """Test getting page URL."""
        page = {
            "_links": {
                "base": "https://test.atlassian.net",
                "webui": "/wiki/spaces/DEMO/pages/12345/Test+Page",
            }
        }

        url = client.get_page_url(page)

        assert url == "https://test.atlassian.net/wiki/spaces/DEMO/pages/12345/Test+Page"

    def test_get_page_url_fallback(self, client: ConfluenceClient) -> None:
        """Test getting page URL with fallback to client URL."""
        page = {
            "_links": {
                "webui": "/wiki/spaces/DEMO/pages/12345/Test+Page",
            }
        }

        url = client.get_page_url(page)

        assert "https://test.atlassian.net" in url


class TestDeletePage:
    """Test deleting pages."""

    def test_delete_page(self, client: ConfluenceClient, mock_confluence: Mock) -> None:
        """Test deleting a page."""
        client.delete_page("12345")

        mock_confluence.remove_page.assert_called_once_with(page_id="12345")


class TestGetSpace:
    """Test getting space information."""

    def test_get_existing_space(self, client: ConfluenceClient, mock_confluence: Mock) -> None:
        """Test getting an existing space."""
        mock_space = {"key": "DEMO", "name": "Demo Space"}
        mock_confluence.get_space.return_value = mock_space

        result = client.get_space("DEMO")

        assert result == mock_space
        mock_confluence.get_space.assert_called_once_with(space_key="DEMO")

    def test_get_nonexistent_space(
        self, client: ConfluenceClient, mock_confluence: Mock
    ) -> None:
        """Test getting a non-existent space."""
        mock_confluence.get_space.return_value = None

        result = client.get_space("NONEXISTENT")

        assert result is None
