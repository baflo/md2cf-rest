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

    Supports Confluence HTML comment syntax with four variants:
    1. Self-closing: <!--confluence:toc param="value"/-->
    2. Confluence-only: <!--confluence:html--><mark>text</mark><!--/confluence-->
    3. Separate content: <!--confluence:info\n<p>CF</p>\n-->\nMD\n<!--/confluence-->
    4. Shared content: <!--confluence:info title="Note"-->\nShared\n<!--/confluence-->
    """

    def __init__(self):
        self.macro_counter = 0
        self.macro_map = {}  # Maps placeholder to macro definition
        self.markdown_content_map = {}  # Maps marker to markdown content for conversion

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
        self.markdown_content_map = {}

        # Process Confluence comment macros (<!--confluence:...-->)
        result = self._process_confluence_comments(markdown_text)

        # Process admonitions (!!! note, !!! warning, etc.)
        result = self._process_admonitions(result)

        return result

    def _convert_named_colors_to_hex(self, html_content: str) -> str:
        """
        Convert named CSS colors to saturated hex codes.

        Args:
            html_content: HTML content with potential named colors

        Returns:
            HTML content with hex color codes
        """
        # Saturated color palette mapping
        color_mapping = {
            'red': '#d04437',
            'yellow': '#f6c342',
            'green': '#14892c',
            'blue': '#4a6785',
            'grey': '#707070',
            'gray': '#707070',
            'orange': '#f79232',
            'purple': '#8b5a99',
        }

        result = html_content
        for color_name, hex_code in color_mapping.items():
            # Replace background-color: colorname patterns
            result = re.sub(
                rf'background-color:\s*{color_name}\s*([;"\'\\)])',
                rf'background-color: {hex_code}\1',
                result,
                flags=re.IGNORECASE
            )

        return result

    def _process_confluence_comments(self, text: str) -> str:
        """
        Process Confluence comment syntax: <!--confluence:MACRO...-->

        Supports four variants:
        1. Self-closing: <!--confluence:toc param="value"/-->
        2. Confluence-only: <!--confluence:html--><mark>text</mark><!--/confluence-->
           (Content can start immediately or after newline/whitespace)
        3. Separate content: <!--confluence:info\n<p>CF</p>\n-->\nMD\n<!--/confluence-->
        4. Shared content: <!--confluence:info title="Hinweis"-->\nShared\n<!--/confluence-->
        """
        # Pattern for all variants
        pattern = (
            r'<!--\s*confluence:(?P<cf_name>\w+)(?P<cf_params>[^\n>]*?)'
            r'(?:'
            # Variant 1: Self-closing /-->
            r'(?P<cf_blank_close>/\s*-->)|'
            # Variant 2: Confluence-only content (content can start immediately or after newline)
            r'(?:-->(?P<cf_only>.*?)<!--\s*/confluence\s*-->)|'
            # Variant 3+4: With closing --> and markdown content
            r'(?:(?:\n(?P<cf_with_md>.*?)|(?P<cf_shared>))-->\n?'
            r'(?P<md_content>.*?)'
            r'^<!--\s*/confluence\s*-->)'
            r')'
        )

        def replace_confluence_macro(match):
            name = match.group('cf_name')
            params_str = match.group('cf_params').strip() if match.group('cf_params') else ''
            params = self._parse_params(params_str)

            cf_content = None
            shared_content = None
            md_fallback = None

            # Determine variant
            if match.group('cf_blank_close'):
                # Variant 1: Self-closing
                pass
            elif match.group('cf_only'):
                # Variant 2: Confluence-only
                cf_content = match.group('cf_only').strip()
            elif match.group('cf_with_md'):
                # Variant 3: Separate content (has CF content before -->)
                cf_content = match.group('cf_with_md').strip()
                md_fallback = match.group('md_content').strip() if match.group('md_content') else ''
            elif match.group('cf_shared') is not None:
                # Variant 4: Shared content (no CF content before -->)
                shared_content = match.group('md_content').strip() if match.group('md_content') else ''

            # Determine body type
            if name.lower() in ('code', 'noformat', 'sql', 'json', 'xml', 'yaml', 'plantuml'):
                body_type = 'plain-text-body'
            elif name.lower() == 'html':
                body_type = 'plain-text-body'
            else:
                body_type = 'rich-text-body'

            # Use shared_content or cf_content for the macro
            content = cf_content or shared_content or ''

            # Convert named colors to hex codes for HTML macros
            if name.lower() == 'html' and content:
                content = self._convert_named_colors_to_hex(content)
            macro_html = self._generate_macro_html(name, params, content, body_type, convert_markdown=True)
            placeholder = self._create_placeholder(macro_html)

            # Return placeholder + markdown fallback (if any)
            if md_fallback:
                return placeholder + '\n' + md_fallback
            else:
                return placeholder

        return re.sub(pattern, replace_confluence_macro, text, flags=re.MULTILINE | re.DOTALL)

    def _process_admonitions(self, text: str) -> str:
        """
        Process Markdown admonitions using GitHub-style blockquote syntax.

        Supports syntax like:
        > [!NOTE]
        > Content here

        > [!INFO]
        > Content here

        The content continues until the next [!TYPE] or end of section.
        Converts to Confluence info/warning/note/tip macros.
        """
        # Pattern: ![TYPE] followed by content until next ![TYPE] or double newline
        # Matches: ![NOTE], ![INFO], ![WARNING], ![TIP], etc.
        pattern = r'^(?P<indent>[ \t]*)> \[\!(?P<label>[A-Z]+)\]\r?\n(?P<content>(?:^(?P=indent)> .*(?:\r?\n)?)+)'

        def replace_admonition(match):
            admonition_type = match.group('label').lower()
            content = match.group('content')

            # Map admonition types to Confluence macro names
            type_mapping = {
                'note': 'note',
                'info': 'info',
                'warning': 'warning',
                'danger': 'warning',
                'error': 'warning',
                'tip': 'tip',
                'hint': 'tip',
                'important': 'info',
                'caution': 'warning',
                'attention': 'note',
            }

            macro_name = type_mapping.get(admonition_type, 'info')

            # Build parameters
            params = {}

            # Use rich-text-body for admonitions to allow markdown formatting
            body_type = 'rich-text-body'

            # Replace single newlines with <br> to preserve line breaks,
            # but only if the line before the newline has actual content (not just whitespace)
            # This prevents adding <br> after empty lines like "> "
            content = re.sub(r'(\S)\n(?!\n)', r'\1<br>\n', content)

            # Mark content for markdown conversion
            macro_html = self._generate_macro_html(macro_name, params, content, body_type, convert_markdown=True)

            # Create placeholder
            placeholder = self._create_placeholder(macro_html)
            return placeholder + '\n'

        return re.sub(pattern, replace_admonition, text, flags=re.MULTILINE)

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

    def _generate_macro_html(self, name: str, params: Dict[str, str],
                           content: str, body_type: str,
                           convert_markdown: bool = False) -> str:
        """
        Generate Confluence macro HTML.

        Args:
            name: Macro name
            params: Macro parameters
            content: Macro content
            body_type: Type of macro body
            convert_markdown: If True and body_type is rich-text-body,
                             content will be marked for later markdown conversion

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
            # If convert_markdown is True, mark content for conversion
            # We use a special marker that will be replaced during postprocessing
            if convert_markdown:
                # Store content with a unique marker
                marker = f'<!--MARKDOWN_CONTENT_{self.macro_counter}-->'
                self.markdown_content_map = getattr(self, 'markdown_content_map', {})
                self.markdown_content_map[marker] = content
                body_html = f'<ac:rich-text-body>{marker}</ac:rich-text-body>'
            else:
                # Content is already processed or doesn't need conversion
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

    def postprocess(self, html: str, converter_instance=None) -> str:
        """
        Replace placeholders with actual macro HTML and convert markdown content.

        Args:
            html: HTML with placeholders
            converter_instance: MarkdownToConfluence instance for converting markdown content

        Returns:
            HTML with macros restored and markdown content converted
        """
        result = html

        # First, replace placeholders with macro HTML (add two newlines after each macro)
        for placeholder, macro_html in self.macro_map.items():
            result = result.replace(placeholder, macro_html + '\n\n')

        # Then, convert any markdown content markers
        if converter_instance and self.markdown_content_map:
            for marker, markdown_content in self.markdown_content_map.items():
                # Convert the markdown content to HTML using a temporary converter
                # to avoid infinite recursion
                import mistune
                from md2cf.renderers.confluence import ConfluenceStorageFormatRenderer

                temp_renderer = ConfluenceStorageFormatRenderer()
                temp_renderer.set_jira_url(getattr(converter_instance, 'jira_url', None))
                temp_markdown = mistune.create_markdown(
                    renderer=temp_renderer,
                    plugins=[
                        "strikethrough",
                        "table",
                        "url",
                        "task_lists",
                    ],
                )

                # Convert markdown to HTML (without the wrapper info panels)
                converted_content = temp_markdown(markdown_content)
                if isinstance(converted_content, str):
                    # Strip the outer paragraph tags if it's a single paragraph
                    # to avoid double-wrapping
                    converted_content = converted_content.strip()
                    result = result.replace(marker, converted_content)

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
            # Restore macros from placeholders and convert markdown content
            result = self.macro_parser.postprocess(result, converter_instance=self)

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


class MarkdownToJira:
    """
    Converter for transforming Markdown to Jira Wiki Markup.

    This class uses Mistune with a custom renderer to convert Markdown
    content into Jira Wiki Markup format used for Jira issue descriptions.
    """

    def __init__(self) -> None:
        """
        Initialize the converter with Jira Wiki Markup renderer.
        """
        from md2cf.renderers.jira import JiraWikiMarkupRenderer

        self.renderer = JiraWikiMarkupRenderer()
        self.markdown = mistune.create_markdown(
            renderer=self.renderer,
            plugins=[
                "strikethrough",
                "table",
                "url",
                "task_lists",
            ],
        )
        logger.debug("Initialized MarkdownToJira converter")

    def convert(self, markdown_content: str) -> str:
        """
        Convert Markdown string to Jira Wiki Markup.

        Args:
            markdown_content: Markdown text to convert

        Returns:
            Jira Wiki Markup string

        Example:
            >>> converter = MarkdownToJira()
            >>> result = converter.convert("# Hello\\n\\nThis is **bold**")
            >>> print(result)
            h1. Hello

            This is *bold*
        """
        if not markdown_content:
            logger.warning("Empty markdown content provided")
            return ""

        logger.debug(f"Converting {len(markdown_content)} characters of Markdown to Jira")
        result = self.markdown(markdown_content)

        if isinstance(result, str):
            logger.debug(f"Converted to {len(result)} characters of Jira Wiki Markup")
            return result.rstrip() + '\n'
        else:
            logger.error(f"Unexpected conversion result type: {type(result)}")
            return str(result)

    def convert_file(self, file_path: Union[str, Path]) -> str:
        """
        Convert a Markdown file to Jira Wiki Markup.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Jira Wiki Markup string

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file

        Example:
            >>> converter = MarkdownToJira()
            >>> result = converter.convert_file("README.md")
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"Markdown file not found: {path}")

        if not path.is_file():
            logger.error(f"Path is not a file: {path}")
            raise IOError(f"Path is not a file: {path}")

        logger.info(f"Converting file to Jira Wiki Markup: {path}")

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
            output_file: Path to save the output (default: same name with .jira extension)

        Returns:
            Path to the output file

        Example:
            >>> converter = MarkdownToJira()
            >>> output = converter.convert_and_save("README.md", "output.jira")
            >>> print(f"Saved to: {output}")
        """
        markdown_path = Path(markdown_file)
        result = self.convert_file(markdown_path)

        if output_file is None:
            output_path = markdown_path.with_suffix(".jira")
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


def convert_markdown_to_jira(markdown_content: str) -> str:
    """
    Convenience function to convert Markdown to Jira Wiki Markup.

    Args:
        markdown_content: Markdown text to convert

    Returns:
        Jira Wiki Markup string

    Example:
        >>> from md2cf import convert_markdown_to_jira
        >>> result = convert_markdown_to_jira("# Title\\n\\nParagraph")
    """
    converter = MarkdownToJira()
    return converter.convert(markdown_content)
