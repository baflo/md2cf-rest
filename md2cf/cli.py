"""
Command-line interface for md2cf.

This module provides a CLI for converting Markdown files to Confluence
and publishing them to Confluence spaces.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from md2cf.api.confluence import ConfluenceClient
from md2cf.converter import MarkdownToConfluence


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

        # Initialize converter with base path for resolving image paths
        converter = MarkdownToConfluence(base_path=input_path.parent)

        # Read markdown file
        with open(input_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Convert Markdown to Confluence format and extract image references
        confluence_content = converter.convert(markdown_content, extract_images=True)
        image_references = converter.get_image_references()

        # Determine page title
        if args.title:
            title = args.title
        else:
            # Use filename without extension as title
            title = input_path.stem.replace("-", " ").replace("_", " ").title()

        # Initialize Confluence client
        client = ConfluenceClient(
            url=args.url,
            token=args.token,
            cloud=args.cloud,
            verify_ssl=not args.no_verify_ssl,
        )

        # Verify space exists
        space = client.get_space(args.space)
        if not space:
            logging.error(f"Space '{args.space}' not found")
            return 1

        # Create or update page
        page = client.create_or_update_page(
            space=args.space,
            title=title,
            body=confluence_content,
            parent_id=args.parent_id,
        )

        page_id = page['id']
        logging.info(f"Page created/updated: {page_id}")

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

        # Print success message with URL
        page_url = client.get_page_url(page)
        print(f"Successfully published page: {title}")
        print(f"Page ID: {page_id}")
        print(f"URL: {page_url}")

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

Environment Variables:
  CONFLUENCE_URL       Confluence base URL
  CONFLUENCE_TOKEN     Personal Access Token
  CONFLUENCE_SPACE     Default space key
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
        required=True,
        help="Confluence base URL (e.g., https://yoursite.atlassian.net)",
    )
    publish_parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="Personal Access Token for authentication",
    )
    publish_parser.add_argument(
        "--space",
        type=str,
        required=True,
        help="Confluence space key",
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
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
