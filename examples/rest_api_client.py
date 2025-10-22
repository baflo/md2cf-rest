#!/usr/bin/env python3
"""
Example REST API client for md2cf.

This script demonstrates how to use the md2cf REST API from Python.
"""

import os
import requests
from typing import Optional


class Md2cfClient:
    """Simple client for md2cf REST API."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize the client.

        Args:
            api_url: Base URL of the md2cf REST API
        """
        self.api_url = api_url.rstrip("/")
        self.session = requests.Session()

    def health_check(self) -> dict:
        """Check if the API is running.

        Returns:
            Health status dictionary
        """
        response = self.session.get(f"{self.api_url}/health")
        response.raise_for_status()
        return response.json()

    def convert(self, markdown: str) -> str:
        """Convert Markdown to Confluence Storage Format.

        Args:
            markdown: Markdown content to convert

        Returns:
            Confluence Storage Format (XHTML)
        """
        response = self.session.post(
            f"{self.api_url}/convert",
            json={"markdown": markdown}
        )
        response.raise_for_status()
        data = response.json()
        return data["confluence_storage_format"]

    def publish(
        self,
        markdown: str,
        confluence_url: str,
        token: str,
        space: str,
        title: str,
        parent_id: Optional[str] = None,
        cloud: bool = True,
        attachments: Optional[list] = None
    ) -> dict:
        """Convert and publish Markdown to Confluence with optional attachments.

        Args:
            markdown: Markdown content
            confluence_url: Confluence base URL
            token: Personal Access Token or API token
            space: Space key
            title: Page title
            parent_id: Optional parent page ID
            cloud: Whether this is Confluence Cloud (vs Server)
            attachments: Optional list of file paths to upload as attachments

        Returns:
            Published page information including attachment upload status
        """
        # Prepare form data
        data = {
            "markdown": markdown,
            "confluence_url": confluence_url,
            "token": token,
            "space": space,
            "title": title,
            "cloud": str(cloud).lower()
        }

        if parent_id:
            data["parent_id"] = parent_id

        # Prepare files for upload (if any)
        files = []
        file_handles = []

        if attachments:
            for file_path in attachments:
                f = open(file_path, "rb")
                file_handles.append(f)
                files.append(("attachments", (os.path.basename(file_path), f)))

        try:
            response = self.session.post(
                f"{self.api_url}/publish",
                data=data,
                files=files if files else None
            )
            response.raise_for_status()
            return response.json()
        finally:
            # Close all file handles
            for f in file_handles:
                f.close()


def example_health_check():
    """Example 1: Health check."""
    print("=" * 60)
    print("Example 1: Health Check")
    print("=" * 60)

    client = Md2cfClient()
    try:
        health = client.health_check()
        print(f"Status: {health['status']}")
        print(f"Version: {health['version']}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API. Is the server running?")
        print("Start it with: python -m md2cf.rest_api")
    print()


def example_convert():
    """Example 2: Convert Markdown."""
    print("=" * 60)
    print("Example 2: Convert Markdown")
    print("=" * 60)

    client = Md2cfClient()

    markdown = """
# Hello World

This is a **bold** statement.

## Features

- Feature 1
- Feature 2
- Feature 3

```python
print("Hello, Confluence!")
```

> This is a quote.
"""

    try:
        result = client.convert(markdown)
        print("Converted successfully!")
        print(f"Output length: {len(result)} characters")
        print("\nFirst 200 characters:")
        print(result[:200])
    except Exception as e:
        print(f"ERROR: {e}")
    print()


def example_convert_file():
    """Example 3: Convert Markdown file."""
    print("=" * 60)
    print("Example 3: Convert Markdown File")
    print("=" * 60)

    client = Md2cfClient()

    # Read sample file
    sample_file = os.path.join(
        os.path.dirname(__file__),
        "sample.md"
    )

    if not os.path.exists(sample_file):
        print(f"Sample file not found: {sample_file}")
        return

    with open(sample_file, "r") as f:
        markdown = f.read()

    try:
        result = client.convert(markdown)
        print(f"Converted {sample_file}")
        print(f"Output length: {len(result)} characters")
    except Exception as e:
        print(f"ERROR: {e}")
    print()


def example_publish():
    """Example 4: Publish to Confluence."""
    print("=" * 60)
    print("Example 4: Publish to Confluence")
    print("=" * 60)

    # Read credentials from environment
    confluence_url = os.getenv("CONFLUENCE_URL")
    token = os.getenv("CONFLUENCE_TOKEN")
    space = os.getenv("CONFLUENCE_SPACE", "DEMO")

    if not confluence_url or not token:
        print("Skipping - Set CONFLUENCE_URL and CONFLUENCE_TOKEN environment variables")
        print()
        return

    client = Md2cfClient()

    markdown = """
# REST API Test Page

This page was created using the md2cf REST API.

## Features

- ✅ Markdown conversion
- ✅ REST API
- ✅ Easy integration

## Code Example

```python
from md2cf_client import Md2cfClient

client = Md2cfClient()
result = client.convert("# Hello World")
print(result)
```

## Next Steps

- [ ] Add more content
- [ ] Test all features
- [ ] Deploy to production
"""

    try:
        result = client.publish(
            markdown=markdown,
            confluence_url=confluence_url,
            token=token,
            space=space,
            title="REST API Test Page",
            cloud=True
        )

        print("Page published successfully!")
        print(f"Page ID: {result['page_id']}")
        print(f"Title: {result['title']}")
        print(f"Space: {result['space']}")
        print(f"Version: {result['version']}")
        print(f"URL: {result['page_url']}")

    except Exception as e:
        print(f"ERROR: {e}")
    print()


def example_publish_with_attachments():
    """Example 5: Publish to Confluence with attachments."""
    print("=" * 60)
    print("Example 5: Publish with Attachments")
    print("=" * 60)

    # Read credentials from environment
    confluence_url = os.getenv("CONFLUENCE_URL")
    token = os.getenv("CONFLUENCE_TOKEN")
    space = os.getenv("CONFLUENCE_SPACE", "DEMO")

    if not confluence_url or not token:
        print("Skipping - Set CONFLUENCE_URL and CONFLUENCE_TOKEN environment variables")
        print()
        return

    client = Md2cfClient()

    markdown = """
# Page with Attachments

This page demonstrates uploading attachments via REST API.

## Local Image

![Diagram](diagram.png)

## Documentation

See the attached document for more details.

## External Image (not uploaded)

![Logo](https://example.com/logo.png)
"""

    # Example attachment files (adjust paths as needed)
    attachments = []
    example_files = [
        os.path.join(os.path.dirname(__file__), "diagram.png"),
        os.path.join(os.path.dirname(__file__), "document.pdf"),
    ]

    # Only include files that exist
    for file_path in example_files:
        if os.path.exists(file_path):
            attachments.append(file_path)

    if not attachments:
        print("No attachment files found. Create some example files to test:")
        print("  - diagram.png")
        print("  - document.pdf")
        print()
        return

    try:
        result = client.publish(
            markdown=markdown,
            confluence_url=confluence_url,
            token=token,
            space=space,
            title="REST API Attachment Test",
            cloud=True,
            attachments=attachments
        )

        print("Page published successfully with attachments!")
        print(f"Page ID: {result['page_id']}")
        print(f"Title: {result['title']}")
        print(f"Space: {result['space']}")
        print(f"Version: {result['version']}")
        print(f"Attachments uploaded: {result['attachments_uploaded']}")
        print(f"Attachments failed: {result['attachments_failed']}")
        print(f"URL: {result['page_url']}")

    except Exception as e:
        print(f"ERROR: {e}")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("md2cf REST API Client Examples")
    print("=" * 60 + "\n")

    example_health_check()
    example_convert()
    example_convert_file()
    example_publish()
    example_publish_with_attachments()

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
