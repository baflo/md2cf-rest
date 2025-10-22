#!/usr/bin/env python3
"""
Example script demonstrating md2cf API usage.

This script shows various ways to use md2cf programmatically.
"""

import os
from pathlib import Path

from md2cf import MarkdownToConfluence
from md2cf.api.confluence import ConfluenceClient


def example_basic_conversion() -> None:
    """Example 1: Basic Markdown to Confluence conversion."""
    print("=" * 60)
    print("Example 1: Basic Conversion")
    print("=" * 60)

    converter = MarkdownToConfluence()

    markdown = """
# Hello World

This is a **simple** example with *formatting*.

## Features

- Item 1
- Item 2
- Item 3

```python
print("Hello, Confluence!")
```
"""

    result = converter.convert(markdown)
    print(result)
    print()


def example_file_conversion() -> None:
    """Example 2: Convert a Markdown file."""
    print("=" * 60)
    print("Example 2: File Conversion")
    print("=" * 60)

    converter = MarkdownToConfluence()

    # Convert the sample file
    sample_file = Path(__file__).parent / "sample.md"
    if sample_file.exists():
        result = converter.convert_file(sample_file)
        print(f"Converted {sample_file.name}")
        print(f"Output length: {len(result)} characters")
    else:
        print(f"Sample file not found: {sample_file}")
    print()


def example_convert_and_save() -> None:
    """Example 3: Convert and save to file."""
    print("=" * 60)
    print("Example 3: Convert and Save")
    print("=" * 60)

    converter = MarkdownToConfluence()

    # Create a temporary markdown file
    temp_md = Path("/tmp/test.md")
    temp_md.write_text("# Test Document\n\nThis is a test.")

    # Convert and save
    output_file = converter.convert_and_save(temp_md)
    print(f"Saved to: {output_file}")

    # Read and display
    content = output_file.read_text()
    print(f"Content:\n{content}")

    # Cleanup
    temp_md.unlink()
    output_file.unlink()
    print()


def example_confluence_api() -> None:
    """Example 4: Use Confluence API (requires credentials)."""
    print("=" * 60)
    print("Example 4: Confluence API")
    print("=" * 60)

    # Read credentials from environment
    url = os.getenv("CONFLUENCE_URL")
    token = os.getenv("CONFLUENCE_TOKEN")
    space = os.getenv("CONFLUENCE_SPACE", "DEMO")

    if not url or not token:
        print("Skipping - Set CONFLUENCE_URL and CONFLUENCE_TOKEN environment variables")
        print()
        return

    try:
        # Initialize client
        client = ConfluenceClient(url=url, token=token, cloud=True)

        # Check if space exists
        space_info = client.get_space(space)
        if space_info:
            print(f"Space '{space}' found: {space_info['name']}")
        else:
            print(f"Space '{space}' not found")
            return

        # Convert markdown
        converter = MarkdownToConfluence()
        markdown = """
# API Test Page

This page was created programmatically using md2cf.

## Features

- Automatic conversion
- PAT authentication
- Easy integration

```python
from md2cf import MarkdownToConfluence
converter = MarkdownToConfluence()
result = converter.convert("# Hello")
```
"""
        content = converter.convert(markdown)

        # Create or update page
        page = client.create_or_update_page(
            space=space,
            title="md2cf API Test",
            body=content,
        )

        print(f"Page created/updated: {page['id']}")
        print(f"URL: {client.get_page_url(page)}")

    except Exception as e:
        print(f"Error: {e}")

    print()


def example_publish_with_attachments() -> None:
    """Example 5: Publish with attachments (requires credentials)."""
    print("=" * 60)
    print("Example 5: Publish with Attachments")
    print("=" * 60)

    # Read credentials from environment
    url = os.getenv("CONFLUENCE_URL")
    token = os.getenv("CONFLUENCE_TOKEN")
    space = os.getenv("CONFLUENCE_SPACE", "DEMO")

    if not url or not token:
        print("Skipping - Set CONFLUENCE_URL and CONFLUENCE_TOKEN environment variables")
        print()
        return

    try:
        # Initialize client
        client = ConfluenceClient(url=url, token=token, cloud=True)

        # Check if space exists
        space_info = client.get_space(space)
        if not space_info:
            print(f"Space '{space}' not found")
            return

        # Create converter with base path
        base_path = Path(__file__).parent
        converter = MarkdownToConfluence(base_path=base_path)

        # Markdown with image references
        markdown = """
# Page with Images

This page demonstrates attachment upload.

## Local Image
![Diagram](./diagram.png)

## External Image
![Logo](https://example.com/logo.png)
"""

        # Convert and extract image references
        content = converter.convert(markdown, extract_images=True)
        image_refs = converter.get_image_references()

        # Create or update page
        page = client.create_or_update_page(
            space=space,
            title="md2cf Attachment Test",
            body=content,
        )

        page_id = page['id']
        print(f"Page created/updated: {page_id}")

        # Upload attachments
        if image_refs:
            print(f"Found {len(image_refs)} image references")
            for img_ref in image_refs:
                if img_ref['resolved_path']:
                    try:
                        client.attach_file(
                            page_id=page_id,
                            file_path=img_ref['resolved_path'],
                            comment=f"Uploaded from {img_ref['url']}"
                        )
                        print(f"Uploaded: {img_ref['filename']}")
                    except Exception as e:
                        print(f"Failed to upload {img_ref['filename']}: {e}")

        print(f"URL: {client.get_page_url(page)}")

    except Exception as e:
        print(f"Error: {e}")

    print()


def example_advanced_usage() -> None:
    """Example 6: Advanced usage with custom processing."""
    print("=" * 60)
    print("Example 6: Advanced Usage")
    print("=" * 60)

    converter = MarkdownToConfluence()

    # Process multiple files
    markdown_files = [
        ("Introduction", "# Introduction\n\nWelcome to our docs."),
        ("Installation", "# Installation\n\n```bash\npip install md2cf\n```"),
        ("Usage", "# Usage\n\nSimple and easy."),
    ]

    results = {}
    for title, content in markdown_files:
        result = converter.convert(content)
        results[title] = result
        print(f"Converted: {title} ({len(result)} chars)")

    print(f"\nTotal files processed: {len(results)}")
    print()


def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 60)
    print("md2cf API Usage Examples")
    print("=" * 60 + "\n")

    # Run examples
    example_basic_conversion()
    example_file_conversion()
    example_convert_and_save()
    example_confluence_api()
    example_publish_with_attachments()
    example_advanced_usage()

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
