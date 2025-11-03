"""
Markdown to Confluence Converter.

This module provides the main conversion functionality from Markdown
to Confluence Storage Format.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

import mistune

from md2cf.renderers.confluence import ConfluenceStorageFormatRenderer


logger = logging.getLogger(__name__)


class ConfluenceMacroParser:
    """
    Parser for Confluence macro syntax in Markdown.

    Supports two syntaxes:
    1. Fenced macro blocks:
       :::macro{name="info" title="Important"}
       Content here
       :::

    2. Inline macro shorthand:
       ::macro{name="status" color="green"}Success::
    """

    def __init__(self):
        self.macro_counter = 0
        self.macro_map = {}  # Maps placeholder to macro definition

    def preprocess(self, markdown_text: str) -> str:
        """
        Preprocess markdown to extract macro definitions and replace with placeholders.

        Args:
            markdown_text: Markdown text potentially containing macro syntax

        Returns:
            Markdown with macros replaced by HTML comment placeholders
        """
        # Reset state
        self.macro_counter = 0
        self.macro_map = {}

        # Process fenced macro blocks first (:::macro{...}...:::)
        result = self._process_fenced_macros(markdown_text)

        # Process inline macros (::macro{...}content::)
        result = self._process_inline_macros(result)

        return result

    def _process_fenced_macros(self, text: str) -> str:
        """
        Process fenced macro blocks: :::macro{params}...:::
        """
        # Pattern: :::macro{name="x" param="y"}
        #          content
        #          :::
        pattern = r':::macro\{([^}]+)\}\s*\n(.*?)^:::\s*$'

        def replace_macro(match):
            params_str = match.group(1)
            content = match.group(2).rstrip()

            params = self._parse_params(params_str)
            macro_name = params.pop('name', 'info')

            # Determine body type based on macro and content
            body_type = self._determine_body_type(macro_name, content, params)

            macro_html = self._generate_macro_html(macro_name, params, content, body_type)

            # Create placeholder
            placeholder = self._create_placeholder(macro_html)
            return placeholder

        return re.sub(pattern, replace_macro, text, flags=re.MULTILINE | re.DOTALL)

    def _process_inline_macros(self, text: str) -> str:
        """
        Process inline macros: ::macro{params}content::
        """
        # Pattern: ::macro{name="status" color="green"}Success::
        pattern = r'::macro\{([^}]+)\}(.*?)::(?!\:)'

        def replace_macro(match):
            params_str = match.group(1)
            content = match.group(2)

            params = self._parse_params(params_str)
            macro_name = params.pop('name', 'status')

            # Inline macros typically use plain-text-body
            body_type = 'plain-text-body'

            macro_html = self._generate_macro_html(macro_name, params, content, body_type)

            # For inline macros, return HTML directly (no placeholder needed)
            placeholder = self._create_placeholder(macro_html)
            return placeholder

        return re.sub(pattern, replace_macro, text, flags=re.DOTALL)

    def _parse_params(self, params_str: str) -> Dict[str, str]:
        """
        Parse parameter string like: name="info" title="Important" color="blue"

        Args:
            params_str: String containing parameters

        Returns:
            Dictionary of parameters
        """
        params = {}
        # Pattern: key="value" or key='value' or key=value
        pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|(\S+))'

        for match in re.finditer(pattern, params_str):
            key = match.group(1)
            # Get value from whichever group matched (quoted or unquoted)
            value = match.group(2) or match.group(3) or match.group(4)
            params[key] = value

        return params

    def _determine_body_type(self, macro_name: str, content: str, params: Dict[str, str]) -> str:
        """
        Determine the appropriate body type for a macro.

        Args:
            macro_name: Name of the macro
            content: Content of the macro
            params: Macro parameters

        Returns:
            Body type: 'rich-text-body', 'plain-text-body', or 'plain-text-link-body'
        """
        # Macros that typically use plain-text-body (no HTML/formatting)
        plain_text_macros = {
            'code', 'noformat', 'sql', 'json', 'xml', 'yaml',
            'plantuml', 'drawio', 'latex'
        }

        # Macros that use plain-text-link-body (URLs)
        link_macros = {
            'widget', 'iframe', 'viewpdf'
        }

        # If explicit body_type parameter is provided, use it
        if 'body_type' in params:
            return params.pop('body_type')

        if macro_name.lower() in plain_text_macros:
            return 'plain-text-body'
        elif macro_name.lower() in link_macros:
            return 'plain-text-link-body'
        else:
            # Default: rich-text-body (allows HTML/formatting)
            return 'rich-text-body'

    def _generate_macro_html(self, name: str, params: Dict[str, str],
                           content: str, body_type: str) -> str:
        """
        Generate Confluence macro HTML.

        Args:
            name: Macro name
            params: Macro parameters
            content: Macro content
            body_type: Type of macro body

        Returns:
            Confluence macro HTML
        """
        from html import escape

        # Build parameter elements
        param_elements = []
        for key, value in params.items():
            # Escape parameter values
            value_escaped = escape(value, quote=False)
            param_elements.append(
                f'<ac:parameter ac:name="{escape(key, quote=False)}">{value_escaped}</ac:parameter>'
            )

        params_html = ''.join(param_elements)

        # Build body element based on type
        if body_type == 'plain-text-body':
            # Use CDATA for plain text (no escaping needed)
            body_html = f'<ac:plain-text-body><![CDATA[{content}]]></ac:plain-text-body>'
        elif body_type == 'plain-text-link-body':
            # Escape for URL/link content
            body_html = f'<ac:plain-text-link-body><![CDATA[{content}]]></ac:plain-text-link-body>'
        else:  # rich-text-body
            # Content will be processed as Markdown, so don't escape
            body_html = f'<ac:rich-text-body>{content}</ac:rich-text-body>'

        # Assemble complete macro
        macro_html = (
            f'<ac:structured-macro ac:name="{escape(name, quote=False)}" ac:schema-version="1">'
            f'{params_html}'
            f'{body_html}'
            f'</ac:structured-macro>'
        )

        return macro_html

    def _create_placeholder(self, macro_html: str) -> str:
        """
        Create a placeholder for the macro HTML.

        Args:
            macro_html: Generated macro HTML

        Returns:
            Placeholder string
        """
        self.macro_counter += 1
        placeholder = f'<!--CONFLUENCE_MACRO_{self.macro_counter}-->'
        self.macro_map[placeholder] = macro_html
        return placeholder

    def postprocess(self, html: str) -> str:
        """
        Replace placeholders with actual macro HTML.

        Args:
            html: HTML with placeholders

        Returns:
            HTML with macros restored
        """
        result = html
        for placeholder, macro_html in self.macro_map.items():
            result = result.replace(placeholder, macro_html)
        return result


class ImageAttributesParser:
    """
    Parser for image attributes like {:width 200, :height 100}.

    Stores attributes separately and provides them to the renderer.
    """
    def __init__(self):
        self.attributes = {}  # Maps URL to {width, height}

    def preprocess(self, markdown_text: str) -> str:
        """
        Preprocess markdown to extract image attributes and remove metadata.

        Finds patterns like ![alt](url){:width X, :height Y}
        and stores the attributes separately.

        Also removes metadata lines like:
        - id:: value
        - property:: value
        """
        # Pattern to match image with attributes
        pattern = r'!\[([^\]]*)\]\(([^\)]+)\)\s*\{([^}]+)\}'

        def replace_image(match):
            alt = match.group(1)
            url = match.group(2).strip()
            attrs_str = match.group(3)

            # Parse width and height
            attrs = {}
            width_match = re.search(r':width\s+["\']?(\d+(?:px)?)["\']?', attrs_str)
            height_match = re.search(r':height\s+["\']?(\d+(?:px)?)["\']?', attrs_str)

            if width_match:
                attrs['width'] = width_match.group(1).rstrip('px')
            if height_match:
                attrs['height'] = height_match.group(1).rstrip('px')

            # Store attributes using URL as key
            self.attributes[url] = attrs

            # Return standard markdown image syntax (without attributes)
            return f'![{alt}]({url})'

        result = re.sub(pattern, replace_image, markdown_text)

        # Remove metadata lines (property:: value format, typically from Logseq/Obsidian)
        # Matches lines like: id:: value, property:: value, etc.
        result = re.sub(r'^\s*\w+::\s+[^\n]+$', '', result, flags=re.MULTILINE)

        # Remove LOGBOOK blocks (from Logseq/Org-mode)
        # Matches blocks like:
        # :LOGBOOK:
        # CLOCK: [timestamp]
        # :END:
        result = re.sub(r'^\s*:LOGBOOK:.*?:END:\s*$', '', result, flags=re.MULTILINE | re.DOTALL)

        return result

    def get_attributes(self, url: str) -> dict:
        """Get stored attributes for a given URL."""
        return self.attributes.get(url, {})


class MarkdownToConfluence:
    """
    Converter for transforming Markdown to Confluence Storage Format.

    This class uses Mistune with a custom renderer to convert Markdown
    content into Confluence-compatible XHTML.
    """

    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        jira_url: Optional[str] = None,
        add_info_panel: bool = True,
        markdown_attachment_name: Optional[str] = None,
        page_id: Optional[str] = None,
        space_key: Optional[str] = None,
        page_title: Optional[str] = None
    ) -> None:
        """
        Initialize the converter with Confluence renderer.

        Args:
            base_path: Base path for resolving relative image paths (optional)
            jira_url: Base Jira URL for detecting Jira ticket links (optional)
                     e.g., "https://jira.lvm.de/jira/"
            add_info_panel: Whether to add an info panel indicating the page was
                           generated from Markdown (default: True)
            markdown_attachment_name: Filename of the markdown attachment to link in
                                     the info panel (optional, e.g., "document.md")
            page_id: Confluence page ID for the CLI example (optional)
            space_key: Confluence space key for the CLI example (optional)
            page_title: Page title for the CLI example (optional)
        """
        self.renderer = ConfluenceStorageFormatRenderer()
        self.macro_parser = ConfluenceMacroParser()
        self.image_attrs_parser = ImageAttributesParser()
        self.jira_url = jira_url.rstrip('/') if jira_url else None
        self.add_info_panel = add_info_panel
        self.markdown_attachment_name = markdown_attachment_name
        self.page_id = page_id
        self.space_key = space_key
        self.page_title = page_title
        self.markdown = mistune.create_markdown(
            renderer=self.renderer,
            plugins=[
                "strikethrough",
                "table",
                "url",
                "task_lists",
            ],
        )
        self.base_path = Path(base_path) if base_path else None
        self.image_references: List[Dict[str, str]] = []
        logger.debug("Initialized MarkdownToConfluence converter")
        if self.jira_url:
            logger.debug(f"Jira URL configured: {self.jira_url}")
        if self.markdown_attachment_name:
            logger.debug(f"Markdown attachment name: {self.markdown_attachment_name}")

    def convert(self, markdown_content: str, extract_images: bool = False) -> str:
        """
        Convert Markdown string to Confluence Storage Format.

        Args:
            markdown_content: Markdown text to convert
            extract_images: Whether to extract and track image references

        Returns:
            Confluence Storage Format (XHTML) string

        Example:
            >>> converter = MarkdownToConfluence()
            >>> result = converter.convert("# Hello\\n\\nThis is **bold**")
            >>> print(result)
            <h1>Hello</h1>
            <p>This is <strong>bold</strong></p>
        """
        if not markdown_content:
            logger.warning("Empty markdown content provided")
            return ""

        # Preprocess to extract macros
        preprocessed = self.macro_parser.preprocess(markdown_content)

        # Preprocess to extract image attributes
        preprocessed = self.image_attrs_parser.preprocess(preprocessed)

        # Reset image references before conversion
        if extract_images:
            self.image_references.clear()
            self.renderer.set_converter(self)

        # Pass the parser to renderer so it can access attributes
        self.renderer.set_image_attrs_parser(self.image_attrs_parser)

        # Pass jira_url to renderer for Jira link detection
        self.renderer.set_jira_url(self.jira_url)

        logger.debug(f"Converting {len(markdown_content)} characters of Markdown")
        result = self.markdown(preprocessed)

        if isinstance(result, str):
            # Restore macros from placeholders
            result = self.macro_parser.postprocess(result)

            logger.debug(f"Converted to {len(result)} characters of Confluence format")
            if extract_images and self.image_references:
                logger.info(f"Extracted {len(self.image_references)} image references")

            # Wrap the main content (excluding info panel) with excerpt macro
            result = (
                '<ac:structured-macro ac:name="excerpt" ac:schema-version="1">'
                '<ac:rich-text-body>'
                f'{result}'
                '</ac:rich-text-body>'
                '</ac:structured-macro>\n'
            )

            # Add info panel at the top if enabled
            if self.add_info_panel:
                info_panel = self._generate_info_panel()
                result = info_panel + result

            return result
        else:
            logger.error(f"Unexpected conversion result type: {type(result)}")
            return str(result)

    def _generate_info_panel(self) -> str:
        """
        Generate an info panel indicating the page was generated from Markdown.

        If markdown_attachment_name is set, includes a link to the markdown attachment
        and a CLI example for downloading and re-publishing.

        Returns:
            Confluence info macro markup
        """
        if self.markdown_attachment_name:
            # Include link to markdown attachment with CLI example
            from html import escape
            filename_escaped = escape(self.markdown_attachment_name, quote=False)

            # Use actual values if available, otherwise use placeholders
            page_id_value = self.page_id if self.page_id else "PAGE_ID"
            space_key_value = self.space_key if self.space_key else "SPACE_KEY"

            # For title, escape quotes for use in command line
            if self.page_title:
                title_value = self.page_title.replace('"', '\\"')
            else:
                title_value = "TITLE"

            # Create CLI example (simplified - assumes env vars are set)
            cli_example = (
                f'# Download:<br/>'
                f'md2cf source {page_id_value}<br/><br/>'
                f'# Nach Änderungen re-publish:<br/>'
                f'md2cf publish ./{filename_escaped} --space {space_key_value} --title "{title_value}"'
            )

            # Wrap info panel in expand macro
            return (
                '<ac:structured-macro ac:name="expand" ac:schema-version="1">'
                '<ac:parameter ac:name="title">ℹ️ Diese Seite wurde aus Markdown generiert</ac:parameter>'
                '<ac:rich-text-body>'
                '<ac:structured-macro ac:name="info" ac:schema-version="1">'
                '<ac:rich-text-body>'
                '<p>Diese Seite wurde mit <a href="https://bitbucket.lvm.de/bitbucket/users/m63119/repos/md2cf/browse">md2cf</a> automatisch aus Markdown generiert. '
                'Original-Datei: '
                '<ac:link>'
                f'<ri:attachment ri:filename="{filename_escaped}" />'
                '</ac:link>'
                '</p>'
                '<p><strong>CLI-Beispiel:</strong></p>'
                f'<pre>{cli_example}</pre>'
                '</ac:rich-text-body>'
                '</ac:structured-macro>'
                '</ac:rich-text-body>'
                '</ac:structured-macro>\n'
            )
        else:
            # No attachment link - also wrap in expand macro
            return (
                '<ac:structured-macro ac:name="expand" ac:schema-version="1">'
                '<ac:parameter ac:name="title">ℹ️ Diese Seite wurde aus Markdown generiert</ac:parameter>'
                '<ac:rich-text-body>'
                '<ac:structured-macro ac:name="info" ac:schema-version="1">'
                '<ac:rich-text-body>'
                '<p>Diese Seite wurde mit <a href="https://bitbucket.lvm.de/bitbucket/users/m63119/repos/md2cf/browse">md2cf</a> automatisch aus Markdown generiert.</p>'
                '</ac:rich-text-body>'
                '</ac:structured-macro>'
                '</ac:rich-text-body>'
                '</ac:structured-macro>\n'
            )

    def get_image_references(self) -> List[Dict[str, str]]:
        """
        Get list of image references found during conversion.

        Returns:
            List of dictionaries with 'url' and 'resolved_path' keys

        Example:
            >>> converter = MarkdownToConfluence(base_path="/docs")
            >>> result = converter.convert("![alt](image.png)", extract_images=True)
            >>> images = converter.get_image_references()
            >>> for img in images:
            ...     print(f"Image: {img['url']} -> {img['resolved_path']}")
        """
        return self.image_references.copy()

    def add_image_reference(self, url: str) -> None:
        """
        Add an image reference during conversion.

        Args:
            url: Image URL from markdown

        Note:
            This method is called internally by the renderer during conversion.
        """
        # Skip external URLs (http://, https://, etc.)
        if url.startswith(('http://', 'https://', '//', 'data:')):
            logger.debug(f"Skipping external/data URL: {url}")
            return

        # Resolve relative path if base_path is set
        resolved_path = None
        if self.base_path:
            img_path = self.base_path / url
            if img_path.exists():
                resolved_path = str(img_path.resolve())
                logger.debug(f"Resolved image path: {url} -> {resolved_path}")
            else:
                logger.warning(f"Image file not found: {img_path}")
        else:
            # Try to resolve relative to current directory
            img_path = Path(url)
            if img_path.exists():
                resolved_path = str(img_path.resolve())
                logger.debug(f"Resolved image path: {url} -> {resolved_path}")
            else:
                logger.warning(f"Image file not found: {url} (no base_path set)")

        self.image_references.append({
            'url': url,
            'resolved_path': resolved_path,
            'filename': Path(url).name
        })

    def convert_file(self, file_path: Union[str, Path]) -> str:
        """
        Convert a Markdown file to Confluence Storage Format.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Confluence Storage Format (XHTML) string

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file

        Example:
            >>> converter = MarkdownToConfluence()
            >>> result = converter.convert_file("README.md")
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"Markdown file not found: {path}")

        if not path.is_file():
            logger.error(f"Path is not a file: {path}")
            raise IOError(f"Path is not a file: {path}")

        logger.info(f"Converting file: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            return self.convert(markdown_content)
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise IOError(f"Error reading file {path}: {e}")

    def convert_and_save(
        self,
        markdown_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Convert a Markdown file and save the result to a file.

        Args:
            markdown_file: Path to the Markdown file
            output_file: Path to save the output (default: same name with .html extension)

        Returns:
            Path to the output file

        Example:
            >>> converter = MarkdownToConfluence()
            >>> output = converter.convert_and_save("README.md", "output.html")
            >>> print(f"Saved to: {output}")
        """
        markdown_path = Path(markdown_file)
        result = self.convert_file(markdown_path)

        if output_file is None:
            output_path = markdown_path.with_suffix(".html")
        else:
            output_path = Path(output_file)

        logger.info(f"Saving converted content to: {output_path}")

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
            logger.info(f"Successfully saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error writing to file {output_path}: {e}")
            raise IOError(f"Error writing to file {output_path}: {e}")


def convert_markdown_to_confluence(markdown_content: str) -> str:
    """
    Convenience function to convert Markdown to Confluence Storage Format.

    Args:
        markdown_content: Markdown text to convert

    Returns:
        Confluence Storage Format (XHTML) string

    Example:
        >>> from md2cf import convert_markdown_to_confluence
        >>> result = convert_markdown_to_confluence("# Title\\n\\nParagraph")
    """
    converter = MarkdownToConfluence()
    return converter.convert(markdown_content)
