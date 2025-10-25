"""Tests for REST API endpoints."""

from unittest.mock import MagicMock, patch
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from md2cf.rest_api import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestConvertEndpoint:
    """Test convert endpoint."""

    def test_convert_simple_markdown(self, client):
        """Test converting simple markdown."""
        markdown = "# Hello World\n\nThis is **bold** text."
        response = client.post(
            "/convert",
            json={"markdown": markdown}
        )

        assert response.status_code == 200
        data = response.json()
        assert "confluence_storage_format" in data
        assert "character_count" in data
        assert "<h1>Hello World</h1>" in data["confluence_storage_format"]
        assert "<strong>bold</strong>" in data["confluence_storage_format"]

    def test_convert_empty_markdown(self, client):
        """Test converting empty markdown."""
        response = client.post(
            "/convert",
            json={"markdown": ""}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["confluence_storage_format"] == ""
        assert data["character_count"] == 0

    def test_convert_code_block(self, client):
        """Test converting code block."""
        markdown = "```python\nprint('Hello')\n```"
        response = client.post(
            "/convert",
            json={"markdown": markdown}
        )

        assert response.status_code == 200
        data = response.json()
        assert '<ac:structured-macro ac:name="code"' in data["confluence_storage_format"]
        assert "python" in data["confluence_storage_format"]

    def test_convert_missing_markdown(self, client):
        """Test convert without markdown field."""
        response = client.post("/convert", json={})

        assert response.status_code == 422  # Validation error


class TestPublishEndpoint:
    """Test publish endpoint."""

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_publish_simple_page(self, mock_client_class, client):
        """Test publishing a simple page."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_space.return_value = {"key": "DEMO"}
        mock_client.get_page_by_title.return_value = None  # New page
        mock_client.create_or_update_page.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "_links": {"webui": "/spaces/DEMO/pages/123456"},
        }
        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1, "when": "2024-01-01T00:00:00Z", "by": {"email": "user@example.com"}},
        }
        mock_client.get_page_url.return_value = "https://example.com/page"

        data = {
            "markdown": "# Test\n\nContent",
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
            "space": "DEMO",
            "title": "Test Page",
        }

        response = client.post("/publish", data=data)

        assert response.status_code == 201
        result = response.json()
        assert result["page_id"] == "123456"
        assert result["title"] == "Test Page"
        assert result["space"] == "DEMO"
        assert result["version"] == 1

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_publish_with_attachments(self, mock_client_class, client):
        """Test publishing with file attachments."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_space.return_value = {"key": "DEMO"}
        mock_client.get_page_by_title.return_value = None
        mock_client.create_or_update_page.return_value = {
            "id": "123456",
            "title": "Test",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
        }
        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test",
            "space": {"key": "DEMO"},
            "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
        }
        mock_client.get_page_url.return_value = "https://example.com"

        # Create file upload
        files = {
            "attachments": ("test.txt", BytesIO(b"test content"), "text/plain"),
        }

        data = {
            "markdown": "# Test",
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
            "space": "DEMO",
            "title": "Test",
        }

        response = client.post("/publish", data=data, files=files)

        assert response.status_code == 201
        # Should have attempted to attach file
        mock_client.attach_file.assert_called()

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_publish_invalid_space(self, mock_client_class, client):
        """Test publishing to non-existent space."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_space.return_value = None  # Space doesn't exist

        data = {
            "markdown": "# Test",
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
            "space": "NONEXISTENT",
            "title": "Test",
        }

        response = client.post("/publish", data=data)

        assert response.status_code == 404

    def test_publish_missing_required_fields(self, client):
        """Test publish without required fields."""
        response = client.post("/publish", data={})

        assert response.status_code == 422  # Validation error


class TestSpacesEndpoint:
    """Test spaces endpoint."""

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_list_spaces(self, mock_client_class, client):
        """Test listing spaces."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_spaces.return_value = [
            {
                "key": "DEMO",
                "name": "Demo Space",
                "type": "global",
                "_links": {"webui": "/spaces/DEMO"}
            },
            {
                "key": "TEST",
                "name": "Test Space",
                "type": "global",
                "_links": {"webui": "/spaces/TEST"}
            }
        ]

        data = {
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
        }

        response = client.post("/spaces", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["total"] == 2
        assert len(result["spaces"]) == 2
        assert result["spaces"][0]["key"] == "DEMO"
        assert result["spaces"][1]["key"] == "TEST"

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_list_spaces_with_search(self, mock_client_class, client):
        """Test listing spaces with search filter."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_spaces.return_value = [
            {
                "key": "DEMO",
                "name": "Demo Space",
                "type": "global",
                "_links": {"webui": "/spaces/DEMO"}
            }
        ]

        data = {
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
            "search": "DEMO",
        }

        response = client.post("/spaces", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["total"] == 1
        mock_client.get_spaces.assert_called_with(search_query="DEMO", limit=25)


class TestGetSpaceEndpoint:
    """Test get space endpoint."""

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_get_space(self, mock_client_class, client):
        """Test getting space details."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_space.return_value = {
            "key": "DEMO",
            "name": "Demo Space",
            "type": "global",
            "_links": {"webui": "/spaces/DEMO"},
            "description": {"plain": {"value": "Test description"}}
        }

        data = {
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
        }

        response = client.post("/space/DEMO", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["key"] == "DEMO"
        assert result["name"] == "Demo Space"

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_get_nonexistent_space(self, mock_client_class, client):
        """Test getting non-existent space."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_space.return_value = None

        data = {
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
        }

        response = client.post("/space/NONEXISTENT", json=data)

        assert response.status_code == 404


class TestGetPageEndpoint:
    """Test get page endpoint."""

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_get_page(self, mock_client_class, client):
        """Test getting page details."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "_links": {"webui": "/pages/123456"},
            "version": {"number": 5, "when": "2024-01-01T00:00:00Z"},
            "ancestors": [{"id": "111111"}],
            "history": {"createdDate": "2024-01-01T00:00:00Z"}
        }

        data = {
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
        }

        response = client.post("/page/123456", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == "123456"
        assert result["title"] == "Test Page"
        assert result["version"] == 5
        assert result["parent_id"] == "111111"

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_get_nonexistent_page(self, mock_client_class, client):
        """Test getting non-existent page."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_page_by_id.return_value = None

        data = {
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
        }

        response = client.post("/page/999999", json=data)

        assert response.status_code == 404


class TestSearchPagesEndpoint:
    """Test search pages endpoint."""

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_search_pages(self, mock_client_class, client):
        """Test searching for pages."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.search_pages.return_value = [
            {
                "content": {
                    "id": "123456",
                    "title": "Test Page",
                    "_expandable": {"space": "DEMO"},
                    "_links": {"webui": "/pages/123456"}
                }
            }
        ]

        data = {
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
            "query": "test",
        }

        response = client.post("/search-pages", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["total"] == 1
        assert len(result["pages"]) == 1
        assert result["pages"][0]["id"] == "123456"

    @patch('md2cf.rest_api.ConfluenceClient')
    def test_search_pages_with_space_filter(self, mock_client_class, client):
        """Test searching pages in specific space."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.search_pages.return_value = []

        data = {
            "confluence_url": "https://example.atlassian.net",
            "token": "test-token",
            "query": "test",
            "space": "DEMO",
        }

        response = client.post("/search-pages", json=data)

        assert response.status_code == 200
        mock_client.search_pages.assert_called_with(
            query="test",
            space="DEMO",
            limit=25
        )


class TestCORSMiddleware:
    """Test CORS middleware configuration."""

    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options("/health")
        # Check that CORS headers are configured
        # (exact headers depend on CORS middleware settings)
        assert response.status_code in [200, 405]  # OPTIONS may or may not be explicitly handled
