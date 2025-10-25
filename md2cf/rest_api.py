"""
REST API for md2cf - Markdown to Confluence converter.

This module provides a FastAPI-based REST API for converting Markdown
to Confluence Storage Format and publishing to Confluence.
"""

import logging
import re
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, Depends, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tempfile
from pathlib import Path as PathLib

from md2cf.converter import MarkdownToConfluence
from md2cf.api.confluence import ConfluenceClient


logger = logging.getLogger(__name__)


# Pydantic models for request/response
class ConvertRequest(BaseModel):
    """Request model for Markdown conversion."""

    markdown: str = Field(..., description="Markdown content to convert")

    class Config:
        json_schema_extra = {
            "example": {
                "markdown": "# Hello World\n\nThis is **bold** text."
            }
        }


class ConvertResponse(BaseModel):
    """Response model for Markdown conversion."""

    confluence_storage_format: str = Field(..., description="Converted Confluence Storage Format")
    character_count: int = Field(..., description="Number of characters in output")

    class Config:
        json_schema_extra = {
            "example": {
                "confluence_storage_format": "<h1>Hello World</h1>\n<p>This is <strong>bold</strong> text.</p>\n",
                "character_count": 55
            }
        }


class PublishRequest(BaseModel):
    """Request model for publishing to Confluence."""

    markdown: str = Field(..., description="Markdown content to convert and publish")
    confluence_url: str = Field(..., description="Confluence base URL")
    token: str = Field(..., description="Personal Access Token or API token")
    space: str = Field(..., description="Space key")
    title: str = Field(..., description="Page title")
    parent_id: Optional[str] = Field(None, description="Parent page ID (optional)")
    cloud: bool = Field(True, description="Whether this is Confluence Cloud (vs Server)")
    jira_url: Optional[str] = Field(None, description="Base Jira URL for converting Jira ticket links to macros (e.g., 'https://jira.lvm.de/jira')")
    add_info_panel: bool = Field(True, description="Whether to add an info panel indicating the page was generated from Markdown")


class PublishResponse(BaseModel):
    """Response model for publishing to Confluence."""

    page_id: str = Field(..., description="Created/updated page ID")
    page_url: str = Field(..., description="URL to the page")
    title: str = Field(..., description="Page title")
    space: str = Field(..., description="Space key")
    version: int = Field(..., description="Page version number")
    last_modified: Optional[str] = Field(None, description="Last modification timestamp (ISO 8601 format)")
    modified_by: Optional[str] = Field(None, description="User who last modified the page")
    attachments_uploaded: int = Field(0, description="Number of attachments uploaded")
    attachments_failed: int = Field(0, description="Number of attachments that failed to upload")

    class Config:
        json_schema_extra = {
            "example": {
                "page_id": "123456",
                "page_url": "https://your-domain.atlassian.net/wiki/spaces/DEMO/pages/123456",
                "title": "My Page",
                "space": "DEMO",
                "version": 1,
                "last_modified": "2025-01-23T12:34:56.789Z",
                "modified_by": "john.doe@example.com",
                "attachments_uploaded": 2,
                "attachments_failed": 0
            }
        }


class SpaceInfo(BaseModel):
    """Model for a single space."""

    key: str = Field(..., description="Space key")
    name: str = Field(..., description="Space name")
    type: str = Field(..., description="Space type (global, personal)")
    url: Optional[str] = Field(None, description="Space URL")

    class Config:
        json_schema_extra = {
            "example": {
                "key": "DEMO",
                "name": "Demo Space",
                "type": "global",
                "url": "/wiki/spaces/DEMO"
            }
        }


class SpacesRequest(BaseModel):
    """Request model for listing spaces."""

    confluence_url: str = Field(..., description="Confluence base URL")
    token: str = Field(..., description="Personal Access Token or API token")
    cloud: bool = Field(True, description="Whether this is Confluence Cloud (vs Server)")
    search: Optional[str] = Field(None, description="Optional search filter for space name or key")
    limit: int = Field(25, ge=1, le=100, description="Maximum number of spaces to return")

    class Config:
        json_schema_extra = {
            "example": {
                "confluence_url": "https://your-domain.atlassian.net/wiki",
                "token": "YOUR_TOKEN_HERE",
                "cloud": True,
                "search": "DEMO",
                "limit": 25
            }
        }


class SpacesResponse(BaseModel):
    """Response model for listing spaces."""

    spaces: list[SpaceInfo] = Field(..., description="List of accessible spaces")
    total: int = Field(..., description="Total number of spaces returned")

    class Config:
        json_schema_extra = {
            "example": {
                "spaces": [
                    {
                        "key": "DEMO",
                        "name": "Demo Space",
                        "type": "global",
                        "url": "/wiki/spaces/DEMO"
                    }
                ],
                "total": 1
            }
        }


class SearchPagesRequest(BaseModel):
    """Request model for searching pages."""

    confluence_url: str = Field(..., description="Confluence base URL")
    token: str = Field(..., description="Personal Access Token or API token")
    cloud: bool = Field(True, description="Whether this is Confluence Cloud (vs Server)")
    query: str = Field(..., description="Search query for page title or content")
    space: Optional[str] = Field(None, description="Optional space key to restrict search")
    limit: int = Field(25, ge=1, le=100, description="Maximum number of pages to return")

    class Config:
        json_schema_extra = {
            "example": {
                "confluence_url": "https://your-domain.atlassian.net/wiki",
                "token": "YOUR_TOKEN_HERE",
                "cloud": True,
                "query": "documentation",
                "space": "DEMO",
                "limit": 25
            }
        }


class PageInfo(BaseModel):
    """Model for a single page."""

    id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    space_key: str = Field(..., description="Space key")
    url: Optional[str] = Field(None, description="Page URL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123456",
                "title": "My Documentation Page",
                "space_key": "DEMO",
                "url": "/wiki/spaces/DEMO/pages/123456"
            }
        }


class SearchPagesResponse(BaseModel):
    """Response model for searching pages."""

    pages: list[PageInfo] = Field(..., description="List of found pages")
    total: int = Field(..., description="Total number of pages found")

    class Config:
        json_schema_extra = {
            "example": {
                "pages": [
                    {
                        "id": "123456",
                        "title": "My Documentation Page",
                        "space_key": "DEMO",
                        "url": "/wiki/spaces/DEMO/pages/123456"
                    }
                ],
                "total": 1
            }
        }


class GetSpaceRequest(BaseModel):
    """Request model for getting a space by key."""

    confluence_url: str = Field(..., description="Confluence base URL")
    token: str = Field(..., description="Personal Access Token or API token")
    cloud: bool = Field(True, description="Whether this is Confluence Cloud (vs Server)")

    class Config:
        json_schema_extra = {
            "example": {
                "confluence_url": "https://your-domain.atlassian.net/wiki",
                "token": "YOUR_TOKEN_HERE",
                "cloud": True
            }
        }


class SpaceDetailResponse(BaseModel):
    """Response model for space details."""

    key: str = Field(..., description="Space key")
    name: str = Field(..., description="Space name")
    type: str = Field(..., description="Space type (global, personal)")
    url: Optional[str] = Field(None, description="Space URL")
    description: Optional[str] = Field(None, description="Space description")

    class Config:
        json_schema_extra = {
            "example": {
                "key": "DEMO",
                "name": "Demo Space",
                "type": "global",
                "url": "/wiki/spaces/DEMO",
                "description": "This is a demo space for testing"
            }
        }


class GetPageRequest(BaseModel):
    """Request model for getting a page by ID."""

    confluence_url: str = Field(..., description="Confluence base URL")
    token: str = Field(..., description="Personal Access Token or API token")
    cloud: bool = Field(True, description="Whether this is Confluence Cloud (vs Server)")

    class Config:
        json_schema_extra = {
            "example": {
                "confluence_url": "https://your-domain.atlassian.net/wiki",
                "token": "YOUR_TOKEN_HERE",
                "cloud": True
            }
        }


class PageDetailResponse(BaseModel):
    """Response model for page details."""

    id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    space_key: str = Field(..., description="Space key")
    url: Optional[str] = Field(None, description="Page URL")
    version: int = Field(..., description="Page version number")
    parent_id: Optional[str] = Field(None, description="Parent page ID")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123456",
                "title": "My Documentation Page",
                "space_key": "DEMO",
                "url": "/wiki/spaces/DEMO/pages/123456",
                "version": 5,
                "parent_id": "123455",
                "created_at": "2024-01-01T12:00:00.000Z",
                "updated_at": "2024-01-15T14:30:00.000Z"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


# Create FastAPI app
app = FastAPI(
    title="md2cf REST API",
    description="Convert Markdown to Confluence Storage Format and publish to Confluence",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root() -> HealthResponse:
    """Root endpoint - health check."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/convert", response_model=ConvertResponse, status_code=status.HTTP_200_OK)
async def convert_markdown(request: ConvertRequest) -> ConvertResponse:
    """
    Convert Markdown to Confluence Storage Format.

    Args:
        request: ConvertRequest containing the Markdown content

    Returns:
        ConvertResponse with the converted content

    Raises:
        HTTPException: If conversion fails
    """
    try:
        converter = MarkdownToConfluence()
        result = converter.convert(request.markdown)

        return ConvertResponse(
            confluence_storage_format=result,
            character_count=len(result)
        )

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}"
        )
    
def publish_request_form(
    markdown: str = Form(..., description="Markdown content to convert and publish"),
    confluence_url: str = Form(..., description="Confluence base URL"),
    token: str = Form(..., description="Personal Access Token or API token"),
    space: str = Form(..., description="Space key"),
    title: str = Form(..., description="Page title"),
    parent_id: Optional[str] = Form(None, description="Parent page ID (optional)"),
    cloud: bool = Form(True, description="Whether this is Confluence Cloud (vs Server)"),
    jira_url: Optional[str] = Form(None, description="Base Jira URL for converting Jira ticket links to macros"),
    add_info_panel: bool = Form(True, description="Whether to add an info panel indicating the page was generated from Markdown"),
) -> PublishRequest:
    """Helper function to create PublishRequest from form data."""
    return PublishRequest(
        markdown=markdown,
        confluence_url=confluence_url,
        token=token,
        space=space,
        title=title,
        parent_id=parent_id,
        cloud=cloud,
        jira_url=jira_url,
        add_info_panel=add_info_panel
    )


@app.post("/publish", response_model=PublishResponse, status_code=status.HTTP_201_CREATED)
async def publish_to_confluence(
    request: PublishRequest = Depends(publish_request_form),
    attachments: List[UploadFile] = None,
) -> PublishResponse:
    """
    Convert Markdown and publish to Confluence with optional attachments.

    This endpoint accepts:
    - Markdown content as form data (via PublishRequest model)
    - Optional multiple file attachments
    - Confluence connection details

    Images referenced in the Markdown (e.g., ![alt](image.png)) will be automatically
    linked to uploaded attachments with matching filenames.

    Supports both:
    - Publishing without attachments (form data only)
    - Publishing with attachments (form data + files)

    Args:
        request: PublishRequest containing all form data fields
        attachments: Optional list of attachment files to upload (default: empty list)

    Returns:
        PublishResponse with the created/updated page information, version metadata,
        timestamp of last modification, user who modified the page, and attachment status

    Raises:
        HTTPException: If conversion or publishing fails
    """
    temp_dir = None
    try:
        # Create a temporary directory for attachments
        temp_dir = tempfile.mkdtemp()
        attachment_paths = {}

        # Save uploaded files to temp directory with their original filenames
        # Handle case where attachments is None (no files uploaded)
        for attachment in (attachments or []):
            # Use original filename in temp directory
            temp_path = PathLib(temp_dir) / attachment.filename

            # Write uploaded content
            content_bytes = await attachment.read()
            temp_path.write_bytes(content_bytes)

            # Store mapping of filename to temp path
            attachment_paths[attachment.filename] = str(temp_path)
            logger.info(f"Saved attachment: {attachment.filename} to {temp_path}")

        # Determine markdown attachment filename
        # We'll use the page title as the markdown filename, but sanitize it for filesystem
        # Replace characters that are problematic in filenames
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', request.title)
        # Also replace multiple spaces/underscores with single underscore
        safe_title = re.sub(r'[_\s]+', '_', safe_title)
        # Remove leading/trailing underscores
        safe_title = safe_title.strip('_')
        markdown_filename = f"{safe_title}.md"

        # Initialize Confluence client
        client = ConfluenceClient(
            url=request.confluence_url,
            token=request.token,
            cloud=request.cloud
        )

        # Verify space exists
        space_info = client.get_space(request.space)
        if not space_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space '{request.space}' not found"
            )

        # Check if page already exists by title
        existing_page = client.get_page_by_title(space=request.space, title=request.title)
        is_new_page = existing_page is None
        page_id = existing_page['id'] if existing_page else None

        if is_new_page:
            logger.info("Creating new page")
        else:
            logger.info(f"Found existing page by title: {page_id}")

        # For existing pages: convert with info panel directly
        # For new pages: convert without info panel first, then update
        if is_new_page:
            # Create page without info panel first (we don't have page_id yet)
            if attachment_paths:
                converter = MarkdownToConfluence(
                    jira_url=request.jira_url,
                    add_info_panel=False,
                    markdown_attachment_name=None
                )
                content = converter.convert(request.markdown, extract_images=True)
                image_refs = converter.get_image_references()
            else:
                converter = MarkdownToConfluence(
                    jira_url=request.jira_url,
                    add_info_panel=False,
                    markdown_attachment_name=None
                )
                content = converter.convert(request.markdown)
                image_refs = []
        else:
            # Update existing page with info panel directly
            if attachment_paths:
                converter = MarkdownToConfluence(
                    jira_url=request.jira_url,
                    add_info_panel=request.add_info_panel,
                    markdown_attachment_name=markdown_filename if request.add_info_panel else None,
                    page_id=page_id,
                    space_key=request.space,
                    page_title=request.title
                )
                content = converter.convert(request.markdown, extract_images=True)
                image_refs = converter.get_image_references()
            else:
                converter = MarkdownToConfluence(
                    jira_url=request.jira_url,
                    add_info_panel=request.add_info_panel,
                    markdown_attachment_name=markdown_filename if request.add_info_panel else None,
                    page_id=page_id,
                    space_key=request.space,
                    page_title=request.title
                )
                content = converter.convert(request.markdown)
                image_refs = []

        # Create or update page
        page = client.create_or_update_page(
            space=request.space,
            title=request.title,
            body=content,
            parent_id=request.parent_id
        )

        page_id = page["id"]
        logger.info(f"Page created/updated: {page_id}")

        # For new pages: add info panel now that we have the page_id
        if is_new_page and request.add_info_panel:
            converter_with_info = MarkdownToConfluence(
                jira_url=request.jira_url,
                add_info_panel=True,
                markdown_attachment_name=markdown_filename,
                page_id=page_id,
                space_key=request.space,
                page_title=request.title
            )

            # Re-convert with info panel
            content_with_info = converter_with_info.convert(request.markdown, extract_images=False)

            # Update the page with the info panel
            page = client.update_page(
                page_id=page_id,
                title=request.title,
                body=content_with_info,
                parent_id=request.parent_id
            )
            logger.info(f"Added info panel to new page: {page_id}")

        # Fetch the page again with full version details to ensure we have all metadata
        # The create/update response might not include all version.by details
        page = client.get_page_by_id(page_id, expand="version,space")

        # Upload the original markdown as attachment (if info panel is enabled)
        if request.add_info_panel:
            try:
                # Create temporary markdown file
                markdown_temp_path = PathLib(temp_dir) / markdown_filename
                markdown_temp_path.write_text(request.markdown, encoding='utf-8')

                client.attach_file(
                    page_id=page_id,
                    file_path=str(markdown_temp_path),
                    comment="Original Markdown source file"
                )
                logger.info(f"Uploaded markdown source file: {markdown_filename}")
            except Exception as e:
                logger.error(f"Failed to upload markdown source file: {e}")

        # Upload attachments
        uploaded_count = 0
        failed_count = 0

        # Check if all image references have matching attachments
        if image_refs:
            referenced_filenames = {ref['filename'] for ref in image_refs}
            uploaded_filenames = set(attachment_paths.keys())

            # Warn about missing attachments
            missing_attachments = referenced_filenames - uploaded_filenames
            if missing_attachments:
                logger.warning(
                    f"Markdown references images that are not in attachments: {missing_attachments}. "
                    f"These image references will be broken in Confluence."
                )

            # Info about unreferenced attachments
            unreferenced_attachments = uploaded_filenames - referenced_filenames
            if unreferenced_attachments:
                logger.info(
                    f"Uploading attachments not referenced in markdown: {unreferenced_attachments}"
                )

        # Upload all provided attachments
        for filename, temp_path in attachment_paths.items():
            try:
                client.attach_file(
                    page_id=page_id,
                    file_path=temp_path,
                    comment=f"Uploaded via REST API"
                )
                logger.info(f"Uploaded attachment: {filename}")
                uploaded_count += 1
            except Exception as e:
                logger.error(f"Failed to upload {filename}: {e}")
                failed_count += 1

        # Extract version information
        version_info = page.get("version", {})
        last_modified = version_info.get("when")  # ISO 8601 timestamp
        modified_by_data = version_info.get("by", {})
        modified_by = modified_by_data.get("email") or modified_by_data.get("displayName") or modified_by_data.get("username")

        return PublishResponse(
            page_id=page["id"],
            page_url=client.get_page_url(page),
            title=page["title"],
            space=page["space"]["key"],
            version=page["version"]["number"],
            last_modified=last_modified,
            modified_by=modified_by,
            attachments_uploaded=uploaded_count,
            attachments_failed=failed_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Publishing failed: {str(e)}"
        )
    finally:
        # Clean up temporary directory and all files
        if temp_dir:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to delete temp directory {temp_dir}: {e}")


@app.post("/spaces", response_model=SpacesResponse, status_code=status.HTTP_200_OK)
async def list_spaces(request: SpacesRequest) -> SpacesResponse:
    """
    List accessible Confluence spaces.

    Args:
        request: SpacesRequest containing Confluence credentials and optional filter

    Returns:
        SpacesResponse with list of accessible spaces

    Raises:
        HTTPException: If listing spaces fails
    """
    try:
        # Initialize Confluence client
        client = ConfluenceClient(
            url=request.confluence_url,
            token=request.token,
            cloud=request.cloud
        )

        # Get accessible spaces
        spaces = client.get_spaces(
            search_query=request.search,
            limit=request.limit
        )

        space_list = [
            SpaceInfo(
                key=space["key"],
                name=space["name"],
                type=space.get("type", "global"),
                url=space.get("_links", {}).get("webui")
            )
            for space in spaces
        ]

        return SpacesResponse(
            spaces=space_list,
            total=len(space_list)
        )

    except Exception as e:
        logger.error(f"Failed to list spaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list spaces: {str(e)}"
        )


@app.post("/space/{space_key}", response_model=SpaceDetailResponse, status_code=status.HTTP_200_OK)
async def get_space(space_key: str, request: GetSpaceRequest) -> SpaceDetailResponse:
    """
    Get detailed information about a Confluence space by its key.

    Args:
        space_key: Space key (from path parameter)
        request: GetSpaceRequest containing Confluence credentials

    Returns:
        SpaceDetailResponse with space details

    Raises:
        HTTPException: If space not found or retrieval fails
    """
    try:
        # Initialize Confluence client
        client = ConfluenceClient(
            url=request.confluence_url,
            token=request.token,
            cloud=request.cloud
        )

        # Get space information
        space = client.get_space(space_key)

        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space '{space_key}' not found"
            )

        return SpaceDetailResponse(
            key=space["key"],
            name=space["name"],
            type=space.get("type", "global"),
            url=space.get("_links", {}).get("webui"),
            description=space.get("description", {}).get("plain", {}).get("value") if isinstance(space.get("description"), dict) else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get space '{space_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get space: {str(e)}"
        )


@app.post("/page/{page_id}", response_model=PageDetailResponse, status_code=status.HTTP_200_OK)
async def get_page(page_id: str, request: GetPageRequest) -> PageDetailResponse:
    """
    Get detailed information about a Confluence page by its ID.

    Args:
        page_id: Page ID (from path parameter)
        request: GetPageRequest containing Confluence credentials

    Returns:
        PageDetailResponse with page details

    Raises:
        HTTPException: If page not found or retrieval fails
    """
    try:
        # Initialize Confluence client
        client = ConfluenceClient(
            url=request.confluence_url,
            token=request.token,
            cloud=request.cloud
        )

        # Get page information
        page = client.get_page_by_id(page_id)

        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page with ID '{page_id}' not found"
            )

        # Extract parent ID from ancestors if available
        parent_id = None
        ancestors = page.get("ancestors", [])
        if ancestors and len(ancestors) > 0:
            parent_id = ancestors[-1].get("id")

        # Extract timestamps
        created_at = page.get("history", {}).get("createdDate")
        updated_at = page.get("version", {}).get("when")

        return PageDetailResponse(
            id=page["id"],
            title=page["title"],
            space_key=page.get("space", {}).get("key"),
            url=page.get("_links", {}).get("webui"),
            version=page.get("version", {}).get("number", 1),
            parent_id=parent_id,
            created_at=created_at,
            updated_at=updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get page '{page_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get page: {str(e)}"
        )


@app.post("/search-pages", response_model=SearchPagesResponse, status_code=status.HTTP_200_OK)
async def search_pages(request: SearchPagesRequest) -> SearchPagesResponse:
    """
    Search for Confluence pages by title or content.

    Args:
        request: SearchPagesRequest containing search query and optional space filter

    Returns:
        SearchPagesResponse with list of matching pages

    Raises:
        HTTPException: If search fails
    """
    try:
        # Initialize Confluence client
        client = ConfluenceClient(
            url=request.confluence_url,
            token=request.token,
            cloud=request.cloud
        )

        # Search for pages
        pages = client.search_pages(
            query=request.query,
            space=request.space,
            limit=request.limit
        )

        page_list = [
            PageInfo(
                id=page["content"]["id"],
                title=page["content"]["title"],
                space_key=page["content"].get("_expandable", {}).get("space"),
                url=page["content"].get("_links", {}).get("webui")
            )
            for page in pages
        ]

        return SearchPagesResponse(
            pages=page_list,
            total=len(page_list)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search pages: {str(e)}"
        )


def create_app() -> FastAPI:
    """Factory function to create the FastAPI app."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
