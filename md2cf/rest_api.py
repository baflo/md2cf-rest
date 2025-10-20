"""
REST API for md2cf - Markdown to Confluence converter.

This module provides a FastAPI-based REST API for converting Markdown
to Confluence Storage Format and publishing to Confluence.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

    class Config:
        json_schema_extra = {
            "example": {
                "markdown": "# My Documentation\n\nThis is my content.",
                "confluence_url": "https://your-domain.atlassian.net/wiki",
                "token": "YOUR_TOKEN_HERE",
                "space": "DEMO",
                "title": "My Page",
                "cloud": True
            }
        }


class PublishResponse(BaseModel):
    """Response model for publishing to Confluence."""

    page_id: str = Field(..., description="Created/updated page ID")
    page_url: str = Field(..., description="URL to the page")
    title: str = Field(..., description="Page title")
    space: str = Field(..., description="Space key")
    version: int = Field(..., description="Page version number")

    class Config:
        json_schema_extra = {
            "example": {
                "page_id": "123456",
                "page_url": "https://your-domain.atlassian.net/wiki/spaces/DEMO/pages/123456",
                "title": "My Page",
                "space": "DEMO",
                "version": 1
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


@app.post("/publish", response_model=PublishResponse, status_code=status.HTTP_201_CREATED)
async def publish_to_confluence(request: PublishRequest) -> PublishResponse:
    """
    Convert Markdown and publish to Confluence.

    Args:
        request: PublishRequest containing the Markdown and Confluence details

    Returns:
        PublishResponse with the created/updated page information

    Raises:
        HTTPException: If conversion or publishing fails
    """
    try:
        # Convert Markdown
        converter = MarkdownToConfluence()
        content = converter.convert(request.markdown)

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

        # Create or update page
        page = client.create_or_update_page(
            space=request.space,
            title=request.title,
            body=content,
            parent_id=request.parent_id
        )

        return PublishResponse(
            page_id=page["id"],
            page_url=client.get_page_url(page),
            title=page["title"],
            space=page["space"]["key"],
            version=page["version"]["number"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Publishing failed: {str(e)}"
        )


def create_app() -> FastAPI:
    """Factory function to create the FastAPI app."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
