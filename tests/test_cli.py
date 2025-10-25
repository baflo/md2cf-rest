"""Tests for CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from md2cf.cli import (
    convert_command,
    publish_command,
    download_attachment_command,
    download_source_command,
    create_parser,
    main,
)


@pytest.fixture
def temp_markdown_file():
    """Create a temporary markdown file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""---
confluence_page_id: "123456"
confluence_space_key: "DEMO"
confluence_title: "Test Page"
confluence_version: 5
---
# Test Title

This is test content with **bold** text.
""")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestConvertCommand:
    """Test convert command."""

    def test_convert_to_stdout(self, temp_markdown_file, capsys):
        """Test converting markdown and outputting to stdout."""
        # Create mock args
        args = MagicMock()
        args.input = temp_markdown_file
        args.output = None

        result = convert_command(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "<h1>Test Title</h1>" in captured.out
        assert "<strong>bold</strong>" in captured.out

    def test_convert_to_file(self, temp_markdown_file):
        """Test converting markdown and saving to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name

        try:
            args = MagicMock()
            args.input = temp_markdown_file
            args.output = output_path

            result = convert_command(args)

            assert result == 0
            assert Path(output_path).exists()

            content = Path(output_path).read_text()
            assert "<h1>Test Title</h1>" in content
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_convert_nonexistent_file(self):
        """Test converting non-existent file."""
        args = MagicMock()
        args.input = "/nonexistent/file.md"
        args.output = None

        result = convert_command(args)

        assert result == 1


class TestPublishCommand:
    """Test publish command."""

    @patch('md2cf.cli.ConfluenceClient')
    def test_publish_new_page(self, mock_client_class, temp_markdown_file):
        """Test publishing a new page."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_space.return_value = {"key": "DEMO", "name": "Demo Space"}
        mock_client.get_page_by_title.return_value = None  # Page doesn't exist
        mock_client.create_or_update_page.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
        }
        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "ancestors": [],
        }
        mock_client.get_page_url.return_value = "https://example.com/page/123456"

        args = MagicMock()
        args.input = temp_markdown_file
        args.url = "https://example.atlassian.net"
        args.token = "test-token"
        args.space = "DEMO"
        args.title = "Test Page"
        args.parent_id = None
        args.cloud = True
        args.no_verify_ssl = False
        args.jira_url = None
        args.no_info_panel = False

        result = publish_command(args)

        assert result == 0
        mock_client.create_or_update_page.assert_called()

    @patch('md2cf.cli.ConfluenceClient')
    def test_publish_with_frontmatter_defaults(self, mock_client_class, temp_markdown_file):
        """Test publishing using frontmatter defaults."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_space.return_value = {"key": "DEMO"}
        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
            "version": {"number": 5},
            "space": {"key": "DEMO"},
            "ancestors": [],
        }
        # Mock get_page_by_title to return None (page lookup by title not needed since we have page_id)
        mock_client.get_page_by_title.return_value = None
        mock_client.create_or_update_page.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 6},
        }
        mock_client.get_page_url.return_value = "https://example.com"

        args = MagicMock()
        args.input = temp_markdown_file
        args.url = "https://example.atlassian.net"
        args.token = "test-token"
        args.space = None  # Should use frontmatter
        args.title = None  # Should use frontmatter
        args.parent_id = None
        args.cloud = True
        args.no_verify_ssl = False
        args.jira_url = None
        args.no_info_panel = False

        result = publish_command(args)

        assert result == 0

    @patch('md2cf.cli.ConfluenceClient')
    def test_publish_version_conflict(self, mock_client_class, temp_markdown_file):
        """Test publishing with version conflict."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_space.return_value = {"key": "DEMO"}
        # Current version is higher than frontmatter version
        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "version": {"number": 10},  # Higher than frontmatter (5)
        }

        args = MagicMock()
        args.input = temp_markdown_file
        args.url = "https://example.atlassian.net"
        args.token = "test-token"
        args.space = None
        args.title = None
        args.parent_id = None
        args.cloud = True
        args.no_verify_ssl = False
        args.jira_url = None
        args.no_info_panel = False

        result = publish_command(args)

        # Should fail due to version conflict
        assert result == 1

    def test_publish_missing_url(self, temp_markdown_file):
        """Test publishing without URL."""
        args = MagicMock()
        args.input = temp_markdown_file
        args.url = None
        args.token = "test-token"
        args.space = "DEMO"
        args.title = "Test"
        args.parent_id = None
        args.cloud = True
        args.no_verify_ssl = False

        result = publish_command(args)

        assert result == 1

    def test_publish_missing_token(self, temp_markdown_file):
        """Test publishing without token."""
        args = MagicMock()
        args.input = temp_markdown_file
        args.url = "https://example.atlassian.net"
        args.token = None
        args.space = "DEMO"
        args.title = "Test"
        args.parent_id = None
        args.cloud = True
        args.no_verify_ssl = False

        result = publish_command(args)

        assert result == 1


class TestDownloadAttachmentCommand:
    """Test download-attachment command."""

    @patch('md2cf.cli.ConfluenceClient')
    def test_download_attachment(self, mock_client_class):
        """Test downloading an attachment."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.download_attachment.return_value = "/tmp/test.md"

        args = MagicMock()
        args.url = "https://example.atlassian.net"
        args.token = "test-token"
        args.page_id = "123456"
        args.filename = "test.md"
        args.output = None
        args.cloud = True
        args.no_verify_ssl = False

        result = download_attachment_command(args)

        assert result == 0
        mock_client.download_attachment.assert_called_once_with(
            page_id="123456",
            filename="test.md",
            output_path="./test.md"
        )

    @patch('md2cf.cli.ConfluenceClient')
    def test_download_attachment_custom_output(self, mock_client_class):
        """Test downloading with custom output path."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.download_attachment.return_value = "/custom/path.md"

        args = MagicMock()
        args.url = "https://example.atlassian.net"
        args.token = "test-token"
        args.page_id = "123456"
        args.filename = "test.md"
        args.output = "/custom/path.md"
        args.cloud = True
        args.no_verify_ssl = False

        result = download_attachment_command(args)

        assert result == 0
        mock_client.download_attachment.assert_called_once_with(
            page_id="123456",
            filename="test.md",
            output_path="/custom/path.md"
        )

    def test_download_attachment_missing_url(self):
        """Test download without URL."""
        args = MagicMock()
        args.url = None
        args.token = "test-token"
        args.page_id = "123456"
        args.filename = "test.md"

        result = download_attachment_command(args)

        assert result == 1


class TestDownloadSourceCommand:
    """Test download-source command."""

    @patch('md2cf.cli.ConfluenceClient')
    @patch('builtins.open', new_callable=mock_open, read_data="# Test Content")
    def test_download_source(self, mock_file, mock_client_class):
        """Test downloading source with frontmatter."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 5},
            "ancestors": [{"id": "111111"}],
        }
        mock_client.download_attachment.return_value = "/tmp/Test_Page.md"

        args = MagicMock()
        args.url = "https://example.atlassian.net"
        args.token = "test-token"
        args.page_id = "123456"
        args.output = None
        args.cloud = True
        args.no_verify_ssl = False

        result = download_source_command(args)

        assert result == 0
        mock_client.get_page_by_id.assert_called_once()
        mock_client.download_attachment.assert_called_once()


class TestCreateParser:
    """Test argument parser creation."""

    def test_parser_has_commands(self):
        """Test that parser has all expected commands."""
        parser = create_parser()

        # Test with valid commands
        args = parser.parse_args(['convert', 'test.md'])
        assert args.command == 'convert'

        args = parser.parse_args(['publish', 'test.md', '--space', 'DEMO'])
        assert args.command == 'publish'

        args = parser.parse_args(['download-attachment', '123456', 'file.md'])
        assert args.command == 'download-attachment'

        args = parser.parse_args(['download-source', '123456'])
        assert args.command == 'download-source'

    def test_publish_parser_arguments(self):
        """Test publish command arguments."""
        parser = create_parser()
        args = parser.parse_args([
            'publish', 'test.md',
            '--url', 'https://example.com',
            '--token', 'token123',
            '--space', 'DEMO',
            '--title', 'Test Title',
            '--parent-id', '654321',
        ])

        assert args.command == 'publish'
        assert args.input == 'test.md'
        assert args.url == 'https://example.com'
        assert args.token == 'token123'
        assert args.space == 'DEMO'
        assert args.title == 'Test Title'
        assert args.parent_id == '654321'

    def test_convert_parser_arguments(self):
        """Test convert command arguments."""
        parser = create_parser()
        args = parser.parse_args([
            'convert', 'input.md',
            '-o', 'output.html'
        ])

        assert args.command == 'convert'
        assert args.input == 'input.md'
        assert args.output == 'output.html'


class TestMain:
    """Test main entry point."""

    def test_main_no_command(self):
        """Test main with no command."""
        result = main([])
        assert result == 1

    @patch('md2cf.cli.convert_command')
    def test_main_convert_command(self, mock_convert):
        """Test main with convert command."""
        mock_convert.return_value = 0

        result = main(['convert', 'test.md'])

        assert result == 0
        mock_convert.assert_called_once()

    @patch('md2cf.cli.publish_command')
    def test_main_publish_command(self, mock_publish):
        """Test main with publish command."""
        mock_publish.return_value = 0

        result = main(['publish', 'test.md', '--space', 'DEMO'])

        assert result == 0
        mock_publish.assert_called_once()

    def test_main_invalid_command(self):
        """Test main with invalid command."""
        # argparse exits with SystemExit when given invalid command
        with pytest.raises(SystemExit) as exc_info:
            main(['invalid-command'])
        # argparse exits with code 2 for invalid arguments
        assert exc_info.value.code == 2
