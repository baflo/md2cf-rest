"""
REST API for md2cf - Markdown to Confluence converter.

This module provides a FastAPI-based REST API for converting Markdown
to Confluence Storage Format and publishing to Confluence.
"""

import logging
import json
import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, Depends, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tempfile
from pathlib import Path as PathLib

from md2cf.converter import MarkdownToConfluence
from md2cf.api.confluence import ConfluenceClient
from md2cf.api.jira import JiraClient


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


# JIRA Models

class JiraCreateIssueRequest(BaseModel):
    """Request model for creating a JIRA issue."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    project: str = Field(..., description="Project key (e.g., DEMO)")
    summary: str = Field(..., description="Issue summary/title")
    issue_type: str = Field(..., description="Issue type JSON object, e.g., '{\"id\": \"90\"}'")
    parent_key: Optional[str] = Field(None, description="Key of the parent issue for sub-tasks")
    fields: Optional[str] = Field(None, description="A JSON string containing all other fields for the issue.")
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")
    convert_markdown: bool = Field(True, description="Whether to convert description from Markdown to Jira Wiki Markup")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "project": "DEMO",
                "summary": "Dynamic Issue",
                "issue_type": "{\"id\": \"10001\"}",
                "parent_key": "PROJ-123",
                "fields": "{\"description\": \"This is a description.\", \"priority\": {\"id\": \"2\"}, \"labels\": [\"dynamic\", \"api\"]}",
                "cloud": False
            }
        }


class JiraUpdateIssueRequest(BaseModel):
    """Request model for updating a JIRA issue with transparent JIRA data format."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    fields: Dict[str, Any] = Field(..., description="Issue fields to update in JIRA format (transparently passed to JIRA API)")
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "fields": {
                    "summary": "Updated Summary",
                    "description": "Updated description text",
                    "priority": {"name": "High"},
                    "assignee": {"accountId": "5d5f0..."},
                    "labels": ["label1", "label2"]
                },
                "cloud": True
            }
        }


class JiraIssueResponse(BaseModel):
    """Response model for JIRA issue operations."""

    key: str = Field(..., description="Issue key (e.g., PROJ-123)")
    id: str = Field(..., description="Issue ID")
    url: str = Field(..., description="Issue URL")
    summary: Optional[str] = Field(None, description="Issue summary")
    status: Optional[str] = Field(None, description="Issue status")
    issue_type: Optional[str] = Field(None, description="Issue type")
    priority: Optional[str] = Field(None, description="Issue priority")
    assignee: Optional[str] = Field(None, description="Assignee name")
    created: Optional[str] = Field(None, description="Creation timestamp")
    updated: Optional[str] = Field(None, description="Last update timestamp")
    attachments_uploaded: int = Field(0, description="Number of attachments uploaded")
    attachments_failed: int = Field(0, description="Number of attachments that failed to upload")

    class Config:
        json_schema_extra = {
            "example": {
                "key": "PROJ-123",
                "id": "10001",
                "url": "https://yoursite.atlassian.net/browse/PROJ-123",
                "summary": "Test Issue",
                "status": "Open",
                "issue_type": "Task",
                "priority": "Medium",
                "assignee": "John Doe",
                "created": "2025-01-23T12:00:00.000+0000",
                "updated": "2025-01-23T14:30:00.000+0000",
                "attachments_uploaded": 2,
                "attachments_failed": 0
            }
        }


class JiraIssueDetailResponse(BaseModel):
    """Response model for JIRA issue details with complete raw data from JIRA API."""

    # Core issue identification
    key: str = Field(..., description="Issue key (e.g., PROJ-123)")
    id: str = Field(..., description="Issue ID")
    self: str = Field(..., description="JIRA REST API URL for this issue")
    url: str = Field(..., description="Browser URL to view the issue")

    # Complete fields object from JIRA
    fields: Dict[str, Any] = Field(..., description="All issue fields as returned by JIRA API")

    # Additional metadata if available
    expand: Optional[str] = Field(None, description="Expanded properties")
    transitions: Optional[List[Dict[str, Any]]] = Field(None, description="Available transitions if requested")
    changelog: Optional[Dict[str, Any]] = Field(None, description="Change history if requested")

    class Config:
        json_schema_extra = {
            "example": {
                "key": "PROJ-123",
                "id": "10001",
                "self": "https://yoursite.atlassian.net/rest/api/2/issue/10001",
                "url": "https://yoursite.atlassian.net/browse/PROJ-123",
                "fields": {
                    "summary": "Test Issue",
                    "status": {"name": "Open", "id": "1"},
                    "issuetype": {"name": "Task", "id": "10"},
                    "priority": {"name": "Medium", "id": "3"},
                    "assignee": {"displayName": "John Doe", "accountId": "abc123"},
                    "created": "2025-01-23T12:00:00.000+0000",
                    "updated": "2025-01-23T14:30:00.000+0000",
                    "description": "This is a test issue"
                },
                "expand": "renderedFields,names,schema"
            }
        }


class JiraGetIssueRequest(BaseModel):
    """Request model for getting a JIRA issue."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "cloud": True
            }
        }


class JiraSearchRequest(BaseModel):
    """Request model for searching JIRA issues."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    jql: str = Field(..., description='JQL query (e.g., "project = DEMO AND status = Open")')
    start: int = Field(0, ge=0, description="Starting index for pagination")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of results")
    fields: Optional[str] = Field(None, description='Comma-separated list of fields to include (e.g., "summary,status,assignee"). If not specified, returns default fields.')
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "jql": "project = DEMO AND status = Open",
                "start": 0,
                "limit": 50,
                "fields": "summary,status,assignee,priority,created,updated",
                "cloud": True
            }
        }


class JiraSearchIssue(BaseModel):
    """Model for a single issue in search results with transparent field access."""

    key: str = Field(..., description="Issue key (e.g., PROJ-123)")
    id: str = Field(..., description="Issue ID")
    self: str = Field(..., description="JIRA REST API URL for this issue")
    url: str = Field(..., description="Browser URL to view the issue")
    fields: Dict[str, Any] = Field(..., description="All issue fields as returned by JIRA API")

    class Config:
        json_schema_extra = {
            "example": {
                "key": "PROJ-123",
                "id": "10001",
                "self": "https://yoursite.atlassian.net/rest/api/2/issue/10001",
                "url": "https://yoursite.atlassian.net/browse/PROJ-123",
                "fields": {
                    "summary": "Test Issue",
                    "status": {"name": "Open", "id": "1"},
                    "issuetype": {"name": "Task", "id": "10"},
                    "priority": {"name": "Medium", "id": "3"},
                    "created": "2025-01-23T12:00:00.000+0000",
                    "updated": "2025-01-23T14:30:00.000+0000"
                }
            }
        }


class JiraSearchResponse(BaseModel):
    """Response model for JIRA issue search with transparent field access."""

    issues: List[JiraSearchIssue] = Field(..., description="List of found issues")
    total: int = Field(..., description="Total number of issues found")
    start_at: int = Field(..., description="Starting index")
    max_results: int = Field(..., description="Maximum results per page")

    class Config:
        json_schema_extra = {
            "example": {
                "issues": [
                    {
                        "key": "PROJ-123",
                        "id": "10001",
                        "self": "https://yoursite.atlassian.net/rest/api/2/issue/10001",
                        "url": "https://yoursite.atlassian.net/browse/PROJ-123",
                        "fields": {
                            "summary": "Test Issue",
                            "status": {"name": "Open"},
                            "issuetype": {"name": "Task"}
                        }
                    }
                ],
                "total": 1,
                "start_at": 0,
                "max_results": 50
            }
        }


class JiraProjectInfo(BaseModel):
    """Model for a JIRA project."""

    key: str = Field(..., description="Project key")
    name: str = Field(..., description="Project name")
    project_type: str = Field(..., description="Project type")
    description: Optional[str] = Field(None, description="Project description")

    class Config:
        json_schema_extra = {
            "example": {
                "key": "DEMO",
                "name": "Demo Project",
                "project_type": "software",
                "description": "This is a demo project"
            }
        }


class JiraProjectsRequest(BaseModel):
    """Request model for listing JIRA projects."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    include_archived: bool = Field(False, description="Include archived projects")
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "include_archived": False,
                "cloud": True
            }
        }


class JiraProjectsResponse(BaseModel):
    """Response model for listing JIRA projects."""

    projects: List[JiraProjectInfo] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")

    class Config:
        json_schema_extra = {
            "example": {
                "projects": [
                    {
                        "key": "DEMO",
                        "name": "Demo Project",
                        "project_type": "software"
                    }
                ],
                "total": 1
            }
        }


# JIRA Metadata Models

class JiraCreateMetaRequest(BaseModel):
    """Request model for getting issue creation metadata."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    project_keys: Optional[List[str]] = Field(None, description="Optional list of project keys to filter")
    issue_type_names: Optional[List[str]] = Field(None, description="Optional list of issue type names to filter")
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "project_keys": ["SCH", "FM"],
                "issue_type_names": ["Story", "Bug"],
                "cloud": True
            }
        }


class JiraCreateMetaResponse(BaseModel):
    """Response model for issue creation metadata."""

    projects: List[Dict[str, Any]] = Field(..., description="List of projects with issue types and field definitions")

    class Config:
        json_schema_extra = {
            "example": {
                "projects": [
                    {
                        "key": "SCH",
                        "name": "Schaden",
                        "issuetypes": [
                            {
                                "id": "10001",
                                "name": "Story",
                                "fields": {
                                    "summary": {"required": True, "schema": {"type": "string"}},
                                    "assignee": {"required": False, "allowedValues": []},
                                }
                            }
                        ]
                    }
                ]
            }
        }


class JiraUsersRequest(BaseModel):
    """Request model for searching JIRA users."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    query: str = Field(..., description="Search term (username, display name, or email)")
    project: Optional[str] = Field(None, description="Optional project key to find assignable users")
    max_results: int = Field(50, ge=1, le=100, description="Maximum number of results")
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "query": "max.mustermann",
                "project": "SCH",
                "max_results": 50,
                "cloud": True
            }
        }


class JiraUserInfo(BaseModel):
    """Model for a JIRA user."""

    account_id: Optional[str] = Field(None, description="User account ID (Cloud)")
    name: Optional[str] = Field(None, description="Username (Server)")
    display_name: str = Field(..., description="Display name")
    email_address: Optional[str] = Field(None, description="Email address")
    active: bool = Field(True, description="Whether the user is active")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "5d5f0...",
                "display_name": "Max Mustermann",
                "email_address": "max@company.com",
                "active": True
            }
        }


class JiraUsersResponse(BaseModel):
    """Response model for user search."""

    users: List[JiraUserInfo] = Field(..., description="List of found users")
    total: int = Field(..., description="Total number of users found")

    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "account_id": "5d5f0...",
                        "display_name": "Max Mustermann",
                        "email_address": "max@company.com",
                        "active": True
                    }
                ],
                "total": 1
            }
        }


class JiraEditMetaRequest(BaseModel):
    """Request model for getting issue edit metadata."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "cloud": True
            }
        }


class JiraEditMetaResponse(BaseModel):
    """Response model for issue edit metadata."""

    fields: Dict[str, Any] = Field(..., description="Dictionary of editable fields with their definitions")

    class Config:
        json_schema_extra = {
            "example": {
                "fields": {
                    "summary": {
                        "required": True,
                        "name": "Summary",
                        "schema": {"type": "string"},
                        "operations": ["set"]
                    },
                    "description": {
                        "required": False,
                        "name": "Description",
                        "schema": {"type": "string"},
                        "operations": ["set"]
                    },
                    "assignee": {
                        "required": False,
                        "name": "Assignee",
                        "schema": {"type": "user"},
                        "operations": ["set"],
                        "allowedValues": []
                    }
                }
            }
        }


class JiraFieldsRequest(BaseModel):
    """Request model for getting JIRA fields."""

    jira_url: str = Field(..., description="JIRA base URL")
    token: str = Field(..., description="Personal Access Token")
    cloud: bool = Field(False, description="Whether this is JIRA Cloud (vs Server/Data Center)")

    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://yoursite.atlassian.net",
                "token": "YOUR_TOKEN_HERE",
                "cloud": True
            }
        }


class JiraFieldInfo(BaseModel):
    """Model for a JIRA field."""

    id: str = Field(..., description="Field ID")
    name: str = Field(..., description="Field name")
    custom: bool = Field(..., description="Whether this is a custom field")
    schema_type: Optional[str] = Field(None, description="Field schema type")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "customfield_10001",
                "name": "Story Points",
                "custom": True,
                "schema_type": "number"
            }
        }


class JiraFieldsResponse(BaseModel):
    """Response model for fields."""

    fields: List[Dict[str, Any]] = Field(..., description="List of available fields")
    total: int = Field(..., description="Total number of fields")

    class Config:
        json_schema_extra = {
            "example": {
                "fields": [
                    {
                        "id": "customfield_10001",
                        "name": "Story Points",
                        "custom": True,
                        "schema": {"type": "number"}
                    }
                ],
                "total": 1
            }
        }


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
        

        with open("/app/examples/.testdaten/input.md", "w", encoding="utf-8") as f:
            f.write(request.markdown)
        with open("/app/examples/.testdaten/output.html", "w", encoding="utf-8") as f:
            f.write(content)

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


def jira_create_issue_form(
    jira_url: str = Form(..., description="JIRA base URL"),
    token: str = Form(..., description="Personal Access Token"),
    project: str = Form(..., description="Project key (e.g., DEMO)"),
    summary: str = Form(..., description="Issue summary/title"),
    issue_type: str = Form(..., description="Issue type JSON object, e.g., '{\"id\": \"90\"}'"),
    parent_key: Optional[str] = Form(None, description="Key of the parent issue for sub-tasks"),
    fields: Optional[str] = Form(None, description="A JSON string containing all other fields for the issue."),
    cloud: bool = Form(False, description="Whether this is JIRA Cloud (vs Server/Data Center)"),
    convert_markdown: bool = Form(True, description="Whether to convert description from Markdown to Jira Wiki Markup"),
) -> JiraCreateIssueRequest:
    """Helper function to create JiraCreateIssueRequest from form data."""
    return JiraCreateIssueRequest(
        jira_url=jira_url,
        token=token,
        project=project,
        summary=summary,
        issue_type=issue_type,
        parent_key=parent_key,
        fields=fields,
        cloud=cloud,
        convert_markdown=convert_markdown,
    )


@app.post("/jira/create", response_model=JiraIssueResponse, status_code=status.HTTP_201_CREATED)
async def create_jira_issue(
    request: JiraCreateIssueRequest = Depends(jira_create_issue_form),
    attachments: List[UploadFile] = File(None),
) -> JiraIssueResponse:
    """
    Create a new JIRA issue with optional attachments.

    This endpoint accepts:
    - Issue details as form data (via JiraCreateIssueRequest model)
    - Optional multiple file attachments
    - JIRA connection details

    Args:
        request: JiraCreateIssueRequest containing issue details
        attachments: Optional list of attachment files to upload (default: empty list)

    Returns:
        JiraIssueResponse with the created issue information and attachment status

    Raises:
        HTTPException: If issue creation fails
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

        # Initialize JIRA client
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        # Parse the dynamic fields from the JSON string
        fields_dict = {}
        if request.fields:
            try:
                fields_dict = json.loads(request.fields)
                if not isinstance(fields_dict, dict):
                    raise ValueError("Fields must be a JSON object.")
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format for fields"
                )

        issue = client.create_issue(
            project=request.project,
            summary=request.summary,
            issue_type=request.issue_type,
            parent_key=request.parent_key,
            fields=fields_dict,
            convert_markdown=request.convert_markdown,
        )

        issue_key = issue["key"]
        issue_url = client.get_issue_url(issue_key)
        logger.info(f"Created JIRA issue: {issue_key}")

        # Upload attachments
        uploaded_count = 0
        failed_count = 0

        for filename, temp_path in attachment_paths.items():
            try:
                client.attach_file(
                    issue_key=issue_key,
                    file_path=temp_path,
                    comment=f"Uploaded via REST API"
                )
                logger.info(f"Uploaded attachment to {issue_key}: {filename}")
                uploaded_count += 1
            except Exception as e:
                logger.error(f"Failed to upload {filename} to {issue_key}: {e}")
                failed_count += 1

        return JiraIssueResponse(
            key=issue["key"],
            id=issue["id"],
            url=issue_url,
            summary=request.summary,
            attachments_uploaded=uploaded_count,
            attachments_failed=failed_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create JIRA issue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create issue: {str(e)}"
        )
    finally:
        # Clean up temporary directory and all files
        if temp_dir:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to delete temp directory {temp_dir}: {e}")


@app.put("/jira/issue/{issue_key}", response_model=JiraIssueDetailResponse, status_code=status.HTTP_200_OK)
async def update_jira_issue(issue_key: str, request: JiraUpdateIssueRequest) -> JiraIssueDetailResponse:
    """
    Update an existing JIRA issue with transparent data format.

    This endpoint accepts the issue fields in the exact JIRA API format and passes
    them transparently to the JIRA API without transformation. The caller is responsible
    for providing the data in the correct JIRA format.

    Args:
        issue_key: The key of the issue to update (e.g., "PROJ-123")
        request: JiraUpdateIssueRequest containing the fields to update in JIRA format

    Returns:
        JiraIssueDetailResponse with the complete updated issue information from JIRA

    Raises:
        HTTPException: If the issue is not found or the update fails

    Example:
        To update summary and priority:
        {
            "jira_url": "https://yoursite.atlassian.net",
            "token": "YOUR_TOKEN",
            "fields": {
                "summary": "New Summary",
                "priority": {"name": "High"}
            },
            "cloud": true
        }
    """
    try:
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        if not request.fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update."
            )

        # Pass fields transparently to JIRA API
        client.update_issue(issue_key=issue_key, fields=request.fields)

        # After updating, fetch the issue to return its latest state
        updated_issue_detail = await get_jira_issue(
            issue_key=issue_key,
            request=JiraGetIssueRequest(
                jira_url=request.jira_url,
                token=request.token,
                cloud=request.cloud
            )
        )

        return updated_issue_detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update JIRA issue '{issue_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update issue: {str(e)}"
        )


@app.post("/jira/issue/{issue_key}", response_model=JiraIssueDetailResponse, status_code=status.HTTP_200_OK)
async def get_jira_issue(issue_key: str, request: JiraGetIssueRequest) -> JiraIssueDetailResponse:
    """
    Get a JIRA issue by key with complete raw data from JIRA API.

    This endpoint returns the complete issue data transparently as received
    from JIRA, including all fields, metadata, and expanded properties.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        request: JiraGetIssueRequest containing JIRA credentials

    Returns:
        JiraIssueDetailResponse with complete issue details from JIRA

    Raises:
        HTTPException: If issue not found or retrieval fails
    """
    try:
        # Initialize JIRA client
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        # Get issue with all fields
        issue = client.get_issue(issue_key)

        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue '{issue_key}' not found"
            )

        # Generate browser URL
        issue_url = client.get_issue_url(issue["key"])

        # Return complete raw issue data transparently
        return JiraIssueDetailResponse(
            key=issue["key"],
            id=issue["id"],
            self=issue.get("self", ""),
            url=issue_url,
            fields=issue.get("fields", {}),
            expand=issue.get("expand"),
            transitions=issue.get("transitions"),
            changelog=issue.get("changelog"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get JIRA issue '{issue_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get issue: {str(e)}"
        )


@app.post("/jira/search", response_model=JiraSearchResponse, status_code=status.HTTP_200_OK)
async def search_jira_issues(request: JiraSearchRequest) -> JiraSearchResponse:
    """
    Search JIRA issues with JQL.

    Args:
        request: JiraSearchRequest containing search query

    Returns:
        JiraSearchResponse with list of matching issues

    Raises:
        HTTPException: If search fails
    """
    try:
        # Initialize JIRA client
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        # Search issues
        result = client.search_issues(
            jql=request.jql,
            start=request.start,
            limit=request.limit,
            fields=request.fields,
        )

        issues = result.get("issues", [])
        issue_list = []

        for issue in issues:
            issue_url = client.get_issue_url(issue["key"])

            issue_list.append(
                JiraSearchIssue(
                    key=issue["key"],
                    id=issue["id"],
                    self=issue.get("self", ""),
                    url=issue_url,
                    fields=issue.get("fields", {}),
                )
            )

        return JiraSearchResponse(
            issues=issue_list,
            total=result.get("total", 0),
            start_at=result.get("startAt", 0),
            max_results=result.get("maxResults", 0),
        )

    except Exception as e:
        # Better error logging and formatting
        error_msg = str(e) if str(e) else repr(e)
        logger.error(f"Failed to search JIRA issues: {error_msg}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search issues: {error_msg} (type: {type(e).__name__})"
        )


@app.post("/jira/projects", response_model=JiraProjectsResponse, status_code=status.HTTP_200_OK)
async def list_jira_projects(request: JiraProjectsRequest) -> JiraProjectsResponse:
    """
    List accessible JIRA projects.

    Args:
        request: JiraProjectsRequest containing JIRA credentials

    Returns:
        JiraProjectsResponse with list of projects

    Raises:
        HTTPException: If listing projects fails
    """
    try:
        # Initialize JIRA client
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        print("Fetching JIRA projects...", request.token)

        # Get projects
        projects = client.get_projects(include_archived=request.include_archived)

        project_list = []
        for project in projects:
            project_list.append(
                JiraProjectInfo(
                    key=project["key"],
                    name=project["name"],
                    project_type=project.get("projectTypeKey", "unknown"),
                    description=project.get("description"),
                )
            )

        return JiraProjectsResponse(
            projects=project_list,
            total=len(project_list),
        )

    except Exception as e:
        # Better error logging
        error_msg = str(e) if str(e) else repr(e)
        logger.error(f"Failed to list JIRA projects: {error_msg}")
        logger.error(f"Exception type: {type(e).__name__}")

        # Try to extract more details from HTTPError
        detail_msg = f"Failed to list projects: {error_msg if error_msg else type(e).__name__}"
        if hasattr(e, 'response'):
            status_code = getattr(e.response, 'status_code', None)
            response_text = getattr(e.response, 'text', None)
            if status_code:
                detail_msg += f" (HTTP {status_code})"
            if response_text:
                logger.error(f"Response: {response_text[:500]}")  # Log first 500 chars
                detail_msg += f" - {response_text[:200]}"  # Include first 200 chars in error

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_msg
        )


@app.post("/jira/create-meta", response_model=JiraCreateMetaResponse, status_code=status.HTTP_200_OK)
async def get_jira_create_meta(request: JiraCreateMetaRequest) -> JiraCreateMetaResponse:
    """
    Get metadata for creating JIRA issues (fields, allowed values, etc.).

    This endpoint provides information about:
    - Available issue types for each project
    - Required and optional fields for each issue type
    - Allowed values for fields (e.g., priorities, statuses)
    - Custom field definitions

    Args:
        request: JiraCreateMetaRequest containing JIRA credentials and optional filters

    Returns:
        JiraCreateMetaResponse with project and issue type metadata

    Raises:
        HTTPException: If metadata retrieval fails
    """
    try:
        # Initialize JIRA client
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        # Get create issue metadata
        result = client.get_create_issue_meta(
            project_keys=request.project_keys,
            issue_type_names=request.issue_type_names,
        )

        return JiraCreateMetaResponse(
            projects=result.get("projects", [])
        )

    except Exception as e:
        logger.error(f"Failed to get JIRA create metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get create metadata: {str(e)}"
        )


@app.post("/jira/issue/{issue_key}/edit-meta", response_model=JiraEditMetaResponse, status_code=status.HTTP_200_OK)
async def get_jira_edit_meta(issue_key: str, request: JiraEditMetaRequest) -> JiraEditMetaResponse:
    """
    Get metadata for editing a JIRA issue (fields, allowed values, etc.).

    This endpoint provides information about:
    - Editable fields for the specific issue
    - Required and optional fields
    - Allowed values for fields (e.g., priorities, statuses)
    - Field operations (set, add, remove, etc.)

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        request: JiraEditMetaRequest containing JIRA credentials

    Returns:
        JiraEditMetaResponse with field metadata for editing

    Raises:
        HTTPException: If metadata retrieval fails
    """
    try:
        # Initialize JIRA client
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        # Get edit issue metadata
        result = client.get_edit_issue_meta(issue_key=issue_key)

        return JiraEditMetaResponse(
            fields=result.get("fields", {})
        )

    except Exception as e:
        logger.error(f"Failed to get JIRA edit metadata for issue '{issue_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get edit metadata: {str(e)}"
        )


@app.post("/jira/users", response_model=JiraUsersResponse, status_code=status.HTTP_200_OK)
async def search_jira_users(request: JiraUsersRequest) -> JiraUsersResponse:
    """
    Search for JIRA users (for assignee selection).

    This endpoint allows searching for users by username, display name, or email.
    Optionally filter by project to get only assignable users for that project.
    If the query is empty but a project is provided, it returns all assignable
    users for that project.

    Args:
        request: JiraUsersRequest containing search query and optional project filter

    Returns:
        JiraUsersResponse with list of matching users

    Raises:
        HTTPException: If user search fails
    """
    try:
        # If no project is specified, a query is required.
        query = request.query.strip() if request.query else ""
        if not request.project and not query:
            logger.warning("User search requires a project or a query.")
            return JiraUsersResponse(users=[], total=0)

        # Initialize JIRA client
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        # The client's search_users method will handle the logic of filtering
        # by query if it's provided, or returning all if it's empty.
        users = client.search_users(
            query=query,
            project=request.project,
            max_results=request.max_results,
        )

        # Convert user data to response format
        user_list = []
        for user in users:
            # Ensure user is a dictionary before processing
            if not isinstance(user, dict):
                logger.warning(f"Skipping non-dictionary user entry: {type(user)} - {user}")
                continue

            user_list.append(
                JiraUserInfo(
                    account_id=user.get("accountId"),
                    name=user.get("name"),
                    display_name=user.get("displayName", ""),
                    email_address=user.get("emailAddress"),
                    active=user.get("active", True),
                )
            )

        return JiraUsersResponse(
            users=user_list,
            total=len(user_list)
        )

    except Exception as e:
        logger.error(f"Failed to search JIRA users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )


@app.post("/jira/fields", response_model=JiraFieldsResponse, status_code=status.HTTP_200_OK)
async def get_jira_fields(request: JiraFieldsRequest) -> JiraFieldsResponse:
    """
    Get all available JIRA fields (including custom fields).

    This endpoint provides information about all fields available in JIRA,
    including system fields and custom fields with their types and properties.

    Args:
        request: JiraFieldsRequest containing JIRA credentials

    Returns:
        JiraFieldsResponse with list of all fields

    Raises:
        HTTPException: If fields retrieval fails
    """
    try:
        # Initialize JIRA client
        client = JiraClient(
            url=request.jira_url,
            token=request.token,
            cloud=request.cloud
        )

        # Get all fields
        fields = client.get_fields()

        return JiraFieldsResponse(
            fields=fields,
            total=len(fields)
        )

    except Exception as e:
        logger.error(f"Failed to get JIRA fields: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fields: {str(e)}"
        )


def create_app() -> FastAPI:
    """Factory function to create the FastAPI app."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
