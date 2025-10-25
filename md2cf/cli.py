"""
Command-line interface for md2cf.

This module provides a CLI for converting Markdown files to Confluence
and publishing them to Confluence spaces.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from md2cf.api.confluence import ConfluenceClient
from md2cf.converter import MarkdownToConfluence
from md2cf.utils.frontmatter import FrontmatterMetadata, add_frontmatter, parse_frontmatter_metadata


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the CLI.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def convert_command(args: argparse.Namespace) -> int:
    """
    Handle the convert command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        converter = MarkdownToConfluence()
        result = converter.convert_file(args.input)

        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Converted content saved to: {output_path}")
        else:
            print(result)

        return 0
    except Exception as e:
        logging.error(f"Conversion failed: {e}")
        return 1


def download_attachment_command(args: argparse.Namespace) -> int:
    """
    Handle the download-attachment command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Validate required arguments
        if not args.url:
            logging.error("Confluence URL is required (use --url or set CONFLUENCE_URL env var)")
            return 1
        if not args.token:
            logging.error("Confluence token is required (use --token or set CONFLUENCE_TOKEN env var)")
            return 1

        # Initialize Confluence client
        client = ConfluenceClient(
            url=args.url,
            token=args.token,
            cloud=args.cloud,
            verify_ssl=not args.no_verify_ssl,
        )

        # Use filename as output path if not specified
        output_path = args.output if args.output else f"./{args.filename}"

        # Download the attachment
        downloaded_path = client.download_attachment(
            page_id=args.page_id,
            filename=args.filename,
            output_path=output_path,
        )

        print(f"Successfully downloaded attachment")
        print(f"File: {args.filename}")
        print(f"Saved to: {downloaded_path}")

        return 0
    except Exception as e:
        logging.error(f"Download failed: {e}")
        return 1


def download_source_command(args: argparse.Namespace) -> int:
    """
    Handle the download-source command.

    Downloads the original Markdown source file from a Confluence page
    and adds frontmatter with page metadata.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Validate required arguments
        if not args.url:
            logging.error("Confluence URL is required (use --url or set CONFLUENCE_URL env var)")
            return 1
        if not args.token:
            logging.error("Confluence token is required (use --token or set CONFLUENCE_TOKEN env var)")
            return 1

        # Initialize Confluence client
        client = ConfluenceClient(
            url=args.url,
            token=args.token,
            cloud=args.cloud,
            verify_ssl=not args.no_verify_ssl,
        )

        # Get page details to extract metadata
        page = client.get_page_by_id(args.page_id, expand="version,space,ancestors")

        if not page:
            logging.error(f"Page with ID '{args.page_id}' not found")
            return 1

        # Determine the markdown attachment filename from page title
        import re
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', page['title'])
        safe_title = re.sub(r'[_\s]+', '_', safe_title)
        safe_title = safe_title.strip('_')
        markdown_filename = f"{safe_title}.md"

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            output_path = f"./{markdown_filename}"

        # Download the markdown attachment
        downloaded_path = client.download_attachment(
            page_id=args.page_id,
            filename=markdown_filename,
            output_path=output_path,
        )

        # Read the downloaded content
        with open(downloaded_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Extract parent ID if available
        ancestors = page.get('ancestors', [])
        parent_id = ancestors[-1]['id'] if ancestors else None

        # Create frontmatter metadata from page info
        metadata = FrontmatterMetadata(
            page_id=page['id'],
            space_key=page['space']['key'],
            title=page['title'],
            version=page['version']['number'],
            parent_id=parent_id,
        )

        # Add frontmatter to markdown content
        markdown_with_frontmatter = add_frontmatter(markdown_content, metadata)

        # Write back to file
        with open(downloaded_path, 'w', encoding='utf-8') as f:
            f.write(markdown_with_frontmatter)

        print(f"Successfully downloaded source Markdown")
        print(f"File: {markdown_filename}")
        print(f"Saved to: {downloaded_path}")
        print(f"Page ID: {page['id']}")
        print(f"Space: {page['space']['key']}")
        print(f"Version: {page['version']['number']}")

        return 0
    except Exception as e:
        logging.error(f"Download failed: {e}")
        return 1


def publish_command(args: argparse.Namespace) -> int:
    """
    Handle the publish command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        input_path = Path(args.input)

        # Read markdown file first
        with open(input_path, "r", encoding="utf-8") as f:
            markdown_content_raw = f.read()

        # Parse frontmatter metadata
        frontmatter_meta, markdown_content = parse_frontmatter_metadata(markdown_content_raw)

        # Use frontmatter as defaults, CLI args override
        space = args.space or frontmatter_meta.space_key
        title = args.title or frontmatter_meta.title
        parent_id = args.parent_id or frontmatter_meta.parent_id

        # Validate required arguments (after frontmatter defaults)
        if not args.url:
            logging.error("Confluence URL is required (use --url or set CONFLUENCE_URL env var)")
            return 1
        if not args.token:
            logging.error("Confluence token is required (use --token or set CONFLUENCE_TOKEN env var)")
            return 1
        if not space:
            logging.error("Confluence space is required (use --space, set CONFLUENCE_SPACE env var, or include in frontmatter)")
            return 1

        # If title still not set, derive from filename
        if not title:
            title = input_path.stem.replace("-", " ").replace("_", " ").title()

        # Initialize converter with base path for resolving image paths and optional jira_url
        jira_url = getattr(args, 'jira_url', None)
        add_info_panel = not getattr(args, 'no_info_panel', False)

        # Use page title for the markdown attachment filename (sanitized for filesystem)
        import re
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'[_\s]+', '_', safe_title)
        safe_title = safe_title.strip('_')
        markdown_filename = f"{safe_title}.md"

        # Initialize Confluence client
        client = ConfluenceClient(
            url=args.url,
            token=args.token,
            cloud=args.cloud,
            verify_ssl=not args.no_verify_ssl,
        )

        # Verify space exists
        space_info = client.get_space(space)
        if not space_info:
            logging.error(f"Space '{space}' not found")
            return 1

        # Version check: if frontmatter has page_id and version, verify we're not behind
        if frontmatter_meta.page_id and frontmatter_meta.version is not None:
            logging.info(f"Frontmatter indicates page ID: {frontmatter_meta.page_id}, version: {frontmatter_meta.version}")

            # Get current page version from Confluence
            try:
                current_page = client.get_page_by_id(frontmatter_meta.page_id, expand="version")
                if current_page:
                    current_version = current_page['version']['number']

                    if frontmatter_meta.version < current_version:
                        logging.error(
                            f"Version conflict: Local version ({frontmatter_meta.version}) is behind "
                            f"Confluence version ({current_version}). "
                            f"Please download the latest version with 'download-source' before publishing."
                        )
                        return 1

                    logging.info(f"Version check passed: local={frontmatter_meta.version}, remote={current_version}")
            except Exception as e:
                logging.warning(f"Could not verify page version: {e}")

        # Check if page already exists (either from frontmatter or by looking it up)
        existing_page = None
        is_new_page = True

        if frontmatter_meta.page_id:
            # We have a page ID from frontmatter, use it directly
            page_id = frontmatter_meta.page_id
            is_new_page = False
            logging.info(f"Using page ID from frontmatter: {page_id}")
        else:
            # Try to find existing page by title
            existing_page = client.get_page_by_title(space=space, title=title)
            if existing_page:
                page_id = existing_page['id']
                is_new_page = False
                logging.info(f"Found existing page by title: {page_id}")
            else:
                page_id = None
                is_new_page = True
                logging.info("Creating new page")

        # For existing pages: convert with info panel directly
        # For new pages: convert without info panel first, then update
        if is_new_page:
            # Create page without info panel first (we don't have page_id yet)
            converter = MarkdownToConfluence(
                base_path=input_path.parent,
                jira_url=jira_url,
                add_info_panel=False,
                markdown_attachment_name=None
            )
        else:
            # Update existing page with info panel directly
            converter = MarkdownToConfluence(
                base_path=input_path.parent,
                jira_url=jira_url,
                add_info_panel=add_info_panel,
                markdown_attachment_name=markdown_filename if add_info_panel else None,
                page_id=page_id,
                space_key=space,
                page_title=title
            )

        # Convert Markdown to Confluence format and extract image references
        confluence_content = converter.convert(markdown_content, extract_images=True)
        image_references = converter.get_image_references()

        # Create or update page
        page = client.create_or_update_page(
            space=space,
            title=title,
            body=confluence_content,
            parent_id=parent_id,
        )

        page_id = page['id']
        logging.info(f"Page created/updated: {page_id}")

        # For new pages: add info panel now that we have the page_id
        if is_new_page and add_info_panel:
            converter_with_info = MarkdownToConfluence(
                base_path=input_path.parent,
                jira_url=jira_url,
                add_info_panel=True,
                markdown_attachment_name=markdown_filename,
                page_id=page_id,
                space_key=space,
                page_title=title
            )

            # Re-convert with info panel
            confluence_content_with_info = converter_with_info.convert(markdown_content, extract_images=False)

            # Update the page with the info panel
            page = client.update_page(
                page_id=page_id,
                title=title,
                body=confluence_content_with_info,
                parent_id=parent_id,
            )
            logging.info(f"Added info panel to new page: {page_id}")

        # Upload the original markdown file as attachment (if info panel is enabled)
        if add_info_panel:
            try:
                # Create a temporary file with the correct name based on the page title
                # This ensures download-source can find it later
                import tempfile
                temp_dir = tempfile.mkdtemp()
                temp_markdown_path = Path(temp_dir) / markdown_filename

                # Copy content to temp file with correct name
                with open(temp_markdown_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content_raw)

                client.attach_file(
                    page_id=page_id,
                    file_path=str(temp_markdown_path),
                    comment="Original Markdown source file"
                )
                logging.info(f"Uploaded markdown source file: {markdown_filename}")

                # Clean up temp file
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logging.error(f"Failed to upload markdown source file: {e}")

        # Upload attachments
        if image_references:
            logging.info(f"Uploading {len(image_references)} attachments...")
            uploaded_count = 0
            failed_count = 0

            for img_ref in image_references:
                if img_ref['resolved_path']:
                    try:
                        attachment = client.attach_file(
                            page_id=page_id,
                            file_path=img_ref['resolved_path'],
                            comment=f"Uploaded from {img_ref['url']}"
                        )
                        logging.info(f"Uploaded: {img_ref['filename']}")
                        uploaded_count += 1
                    except Exception as e:
                        logging.error(f"Failed to upload {img_ref['filename']}: {e}")
                        failed_count += 1
                else:
                    logging.warning(f"Skipping unresolved image: {img_ref['url']}")
                    failed_count += 1

            if uploaded_count > 0:
                print(f"Uploaded {uploaded_count} attachment(s)")
            if failed_count > 0:
                print(f"Failed to upload {failed_count} attachment(s)")

        # Fetch the updated page to get the new version number
        updated_page = client.get_page_by_id(page_id, expand="version,space,ancestors")

        # Extract parent ID if available
        ancestors = updated_page.get('ancestors', [])
        new_parent_id = ancestors[-1]['id'] if ancestors else None

        # Update frontmatter with new metadata
        updated_metadata = FrontmatterMetadata(
            page_id=updated_page['id'],
            space_key=updated_page['space']['key'],
            title=updated_page['title'],
            version=updated_page['version']['number'],
            parent_id=new_parent_id,
        )

        # Update the local markdown file with new frontmatter
        markdown_with_updated_frontmatter = add_frontmatter(markdown_content, updated_metadata)

        # Write back to the original file
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(markdown_with_updated_frontmatter)

        logging.info(f"Updated frontmatter: version {updated_metadata.version}")

        # Print success message with URL
        page_url = client.get_page_url(page)
        print(f"Successfully published page: {title}")
        print(f"Page ID: {page_id}")
        print(f"Version: {updated_metadata.version}")
        print(f"URL: {page_url}")
        print(f"Local file updated with new frontmatter")

        return 0
    except Exception as e:
        logging.error(f"Publishing failed: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="md2cf",
        description="Convert Markdown to Confluence Storage Format and publish to Confluence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a Markdown file to Confluence format
  md2cf convert README.md

  # Convert and save to file
  md2cf convert README.md -o output.html

  # Publish to Confluence
  md2cf publish README.md --url https://yoursite.atlassian.net \\
      --token YOUR_PAT_TOKEN --space DEMO

  # Publish with custom title and parent page
  md2cf publish docs/api.md --url https://yoursite.atlassian.net \\
      --token YOUR_PAT_TOKEN --space DEMO --title "API Documentation" \\
      --parent-id 123456

  # Download an attachment
  md2cf download-attachment 123456 document.md \\
      --url https://yoursite.atlassian.net \\
      --token YOUR_PAT_TOKEN \\
      -o ./downloads/document.md

Environment Variables:
  CONFLUENCE_URL       Confluence base URL
  CONFLUENCE_TOKEN     Personal Access Token
  CONFLUENCE_SPACE     Default space key
  JIRA_URL             Jira base URL for ticket link conversion
        """,
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert Markdown to Confluence Storage Format",
    )
    convert_parser.add_argument(
        "input",
        type=str,
        help="Input Markdown file path",
    )
    convert_parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path (default: print to stdout)",
    )

    # Publish command
    publish_parser = subparsers.add_parser(
        "publish",
        help="Convert and publish Markdown to Confluence",
    )
    publish_parser.add_argument(
        "input",
        type=str,
        help="Input Markdown file path",
    )
    publish_parser.add_argument(
        "--url",
        type=str,
        default=os.environ.get("CONFLUENCE_URL"),
        help="Confluence base URL (e.g., https://yoursite.atlassian.net) [env: CONFLUENCE_URL]",
    )
    publish_parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("CONFLUENCE_TOKEN"),
        help="Personal Access Token for authentication [env: CONFLUENCE_TOKEN]",
    )
    publish_parser.add_argument(
        "--space",
        type=str,
        default=os.environ.get("CONFLUENCE_SPACE"),
        help="Confluence space key [env: CONFLUENCE_SPACE]",
    )
    publish_parser.add_argument(
        "--title",
        type=str,
        help="Page title (default: derived from filename)",
    )
    publish_parser.add_argument(
        "--parent-id",
        type=str,
        help="Parent page ID",
    )
    publish_parser.add_argument(
        "--cloud",
        action="store_true",
        default=True,
        help="Use Confluence Cloud API (default: True)",
    )
    publish_parser.add_argument(
        "--server",
        action="store_false",
        dest="cloud",
        help="Use Confluence Server/Data Center API",
    )
    publish_parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification",
    )
    publish_parser.add_argument(
        "--jira-url",
        type=str,
        default=os.environ.get("JIRA_URL"),
        help="Base Jira URL for converting Jira ticket links to macros (e.g., https://jira.lvm.de/jira) [env: JIRA_URL]",
    )
    publish_parser.add_argument(
        "--no-info-panel",
        action="store_true",
        help="Disable the info panel at the top of the page that indicates it was generated from Markdown",
    )

    # Download-attachment command
    download_parser = subparsers.add_parser(
        "download-attachment",
        help="Download an attachment from a Confluence page",
    )
    download_parser.add_argument(
        "page_id",
        type=str,
        help="Page ID containing the attachment",
    )
    download_parser.add_argument(
        "filename",
        type=str,
        help="Name of the attachment to download",
    )
    download_parser.add_argument(
        "-o", "--output",
        type=str,
        required=False,
        help="Output path where to save the downloaded file (default: ./<filename>)",
    )
    download_parser.add_argument(
        "--url",
        type=str,
        default=os.environ.get("CONFLUENCE_URL"),
        help="Confluence base URL (e.g., https://yoursite.atlassian.net) [env: CONFLUENCE_URL]",
    )
    download_parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("CONFLUENCE_TOKEN"),
        help="Personal Access Token for authentication [env: CONFLUENCE_TOKEN]",
    )
    download_parser.add_argument(
        "--cloud",
        action="store_true",
        default=True,
        help="Use Confluence Cloud API (default: True)",
    )
    download_parser.add_argument(
        "--server",
        action="store_false",
        dest="cloud",
        help="Use Confluence Server/Data Center API",
    )
    download_parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification",
    )

    # Download-source command
    download_source_parser = subparsers.add_parser(
        "download-source",
        help="Download the original Markdown source file from a Confluence page with frontmatter metadata",
    )
    download_source_parser.add_argument(
        "page_id",
        type=str,
        help="Page ID containing the Markdown source",
    )
    download_source_parser.add_argument(
        "-o", "--output",
        type=str,
        required=False,
        help="Output path where to save the file (default: ./<page_title>.md)",
    )
    download_source_parser.add_argument(
        "--url",
        type=str,
        default=os.environ.get("CONFLUENCE_URL"),
        help="Confluence base URL (e.g., https://yoursite.atlassian.net) [env: CONFLUENCE_URL]",
    )
    download_source_parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("CONFLUENCE_TOKEN"),
        help="Personal Access Token for authentication [env: CONFLUENCE_TOKEN]",
    )
    download_source_parser.add_argument(
        "--cloud",
        action="store_true",
        default=True,
        help="Use Confluence Cloud API (default: True)",
    )
    download_source_parser.add_argument(
        "--server",
        action="store_false",
        dest="cloud",
        help="Use Confluence Server/Data Center API",
    )
    download_source_parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification",
    )

    return parser


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "convert":
        return convert_command(args)
    elif args.command == "publish":
        return publish_command(args)
    elif args.command == "download-attachment":
        return download_attachment_command(args)
    elif args.command == "download-source":
        return download_source_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
