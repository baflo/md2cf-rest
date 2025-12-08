"""
JIRA API Client with PAT Authentication.

This module provides a client for interacting with JIRA REST API
using Personal Access Token (PAT) authentication.
"""

import logging
import traceback
from typing import Any, Dict, Optional, List
from urllib.parse import urljoin

from atlassian import Jira


logger = logging.getLogger(__name__)


class JiraClient:
    """
    Client for JIRA REST API with PAT authentication.

    This class wraps the atlassian-python-api library and provides
    functionality for issue management.
    """

    def __init__(
        self,
        url: str,
        token: str,
        cloud: bool = False,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize JIRA client.

        Args:
            url: JIRA base URL (e.g., https://yoursite.atlassian.net)
            token: Personal Access Token for authentication
            cloud: Whether using JIRA Cloud (True) or Server/Data Center (False)
            verify_ssl: Whether to verify SSL certificates

        Example:
            >>> client = JiraClient(
            ...     url="https://yoursite.atlassian.net",
            ...     token="your-pat-token",
            ...     cloud=True
            ... )
        """
        self.url = url.rstrip("/")
        self.token = token
        self.cloud = cloud
        self.verify_ssl = verify_ssl

        # Initialize atlassian-python-api Jira client
        self.jira = Jira(
            url=self.url,
            token=self.token,
            cloud=self.cloud,
            verify_ssl=self.verify_ssl,
        )

        logger.info(f"Initialized JIRA client for {self.url}")

    def create_issue(
        self,
        project: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new issue in JIRA.

        Args:
            project: Project key (e.g., "PROJ")
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (e.g., "Bug", "Task", "Story")
            priority: Priority name (e.g., "High", "Medium", "Low")
            assignee: Assignee username/email
            labels: List of labels to add
            custom_fields: Dictionary of custom field IDs to values
                          (e.g., {"customfield_10001": "value"})

        Returns:
            Created issue data dictionary with 'id', 'key', and 'self' URL

        Example:
            >>> issue = client.create_issue(
            ...     project="DEMO",
            ...     summary="Test Issue",
            ...     description="This is a test issue",
            ...     issue_type="Task",
            ...     priority="Medium",
            ...     labels=["test", "automation"]
            ... )
            >>> print(f"Created issue: {issue['key']}")
        """
        try:
            fields = {
                "project": {"key": project},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }

            # Add optional fields
            if priority:
                fields["priority"] = {"name": priority}

            if assignee:
                fields["assignee"] = {"name": assignee} if not self.cloud else {"accountId": assignee}

            if labels:
                fields["labels"] = labels

            # Add custom fields
            if custom_fields:
                fields.update(custom_fields)

            result = self.jira.create_issue(fields=fields)

            logger.info(f"Created issue '{result['key']}' in project '{project}'")
            return result

        except Exception as e:
            logger.error(f"Error creating issue in project '{project}': {e}")
            raise

    def get_issue(
        self,
        issue_key: str,
        fields: Optional[str] = None,
        expand: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get an issue by key or ID.

        Args:
            issue_key: Issue key (e.g., "PROJ-123") or ID
            fields: Comma-separated list of fields to include (default: all)
            expand: Comma-separated list of properties to expand

        Returns:
            Issue data dictionary or None if not found

        Example:
            >>> issue = client.get_issue("PROJ-123")
            >>> if issue:
            ...     print(f"Issue: {issue['fields']['summary']}")
            ...     print(f"Status: {issue['fields']['status']['name']}")
        """
        try:
            result = self.jira.issue(
                key=issue_key,
                fields=fields or "*all",
                expand=expand,
            )

            if result:
                logger.info(f"Found issue '{issue_key}': '{result['fields']['summary']}'")
                return result

            logger.warning(f"Issue '{issue_key}' not found")
            return None

        except Exception as e:
            logger.error(f"Error getting issue '{issue_key}': {e}")
            raise

    def search_issues(
        self,
        jql: str,
        start: int = 0,
        limit: int = 50,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for issues using JQL (JIRA Query Language).

        Args:
            jql: JQL query string (e.g., "project = DEMO AND status = Open")
            start: Starting index for pagination (default: 0)
            limit: Maximum number of results to return (default: 50)
            fields: Comma-separated list of fields to include (default: key fields)

        Returns:
            Dictionary with 'issues', 'total', 'startAt', 'maxResults'

        Example:
            >>> result = client.search_issues(
            ...     jql="project = DEMO AND assignee = currentUser()",
            ...     limit=10
            ... )
            >>> print(f"Found {result['total']} issues")
            >>> for issue in result['issues']:
            ...     print(f"{issue['key']}: {issue['fields']['summary']}")
        """
        try:
            logger.info(f"Searching issues with JQL: {jql}")

            # Use the jql method from atlassian-python-api
            result = self.jira.jql(
                jql=jql,
                fields=fields or "summary,status,issuetype,assignee,priority,created,updated",
                start=start,
                limit=limit,
            )

            if result is None:
                logger.warning("JQL search returned None")
                return {"issues": [], "total": 0, "startAt": 0, "maxResults": 0}

            issues = result.get("issues", [])
            total = result.get("total", 0)

            logger.info(f"Found {len(issues)} issues (total: {total})")

            return result

        except Exception as e:
            # Better error logging
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"Error searching issues: {error_msg}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            raise

    def get_projects(
        self,
        include_archived: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get list of projects accessible to the user.

        Args:
            include_archived: Whether to include archived projects

        Returns:
            List of project data dictionaries

        Example:
            >>> projects = client.get_projects()
            >>> for project in projects:
            ...     print(f"{project['key']}: {project['name']}")
        """
        try:
            # Use the projects method from atlassian-python-api
            result = self.jira.projects(included_archived=include_archived)

            if result is None:
                logger.warning("Projects call returned None")
                return []

            logger.info(f"Found {len(result)} projects")
            return result

        except Exception as e:
            # Better error logging
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"Error getting projects: {error_msg}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            raise

    def get_project(self, project_key: str) -> Optional[Dict[str, Any]]:
        """
        Get project information by key.

        Args:
            project_key: Project key (e.g., "DEMO")

        Returns:
            Project data dictionary or None if not found

        Example:
            >>> project = client.get_project("DEMO")
            >>> if project:
            ...     print(f"Project: {project['name']}")
        """
        try:
            result = self.jira.project(key=project_key)

            if result:
                logger.info(f"Found project '{project_key}': '{result['name']}'")
                return result

            logger.warning(f"Project '{project_key}' not found")
            return None

        except Exception as e:
            logger.error(f"Error getting project '{project_key}': {e}")
            raise

    def get_issue_types(
        self,
        project_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get available issue types.

        Args:
            project_key: Optional project key to get project-specific issue types

        Returns:
            List of issue type data dictionaries

        Example:
            >>> issue_types = client.get_issue_types("DEMO")
            >>> for it in issue_types:
            ...     print(f"{it['name']}: {it['description']}")
        """
        try:
            if project_key:
                # Get issue types for specific project
                project = self.get_project(project_key)
                if project and "issueTypes" in project:
                    result = project["issueTypes"]
                else:
                    result = []
            else:
                # Get all issue types
                result = self.jira.get_all_issue_types()

            logger.info(f"Found {len(result)} issue types")
            return result

        except Exception as e:
            logger.error(f"Error getting issue types: {e}")
            raise

    def get_priorities(self) -> List[Dict[str, Any]]:
        """
        Get available priorities.

        Returns:
            List of priority data dictionaries

        Example:
            >>> priorities = client.get_priorities()
            >>> for priority in priorities:
            ...     print(f"{priority['name']}: {priority['id']}")
        """
        try:
            result = self.jira.priorities()

            logger.info(f"Found {len(result)} priorities")
            return result

        except Exception as e:
            logger.error(f"Error getting priorities: {e}")
            raise

    def get_issue_url(self, issue_key: str) -> str:
        """
        Get the full URL for an issue.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")

        Returns:
            Full issue URL

        Example:
            >>> url = client.get_issue_url("PROJ-123")
            >>> print(f"View at: {url}")
        """
        return urljoin(self.url + "/", f"browse/{issue_key}")

    def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any],
    ) -> None:
        """
        Update an existing issue.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            fields: Dictionary of fields to update

        Example:
            >>> client.update_issue(
            ...     issue_key="PROJ-123",
            ...     fields={
            ...         "summary": "Updated summary",
            ...         "description": "Updated description"
            ...     }
            ... )
        """
        try:
            self.jira.update_issue_field(
                key=issue_key,
                fields=fields,
            )

            logger.info(f"Updated issue '{issue_key}'")

        except Exception as e:
            logger.error(f"Error updating issue '{issue_key}': {e}")
            raise

    def add_comment(
        self,
        issue_key: str,
        comment: str,
    ) -> Dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            comment: Comment text

        Returns:
            Created comment data dictionary

        Example:
            >>> comment = client.add_comment(
            ...     issue_key="PROJ-123",
            ...     comment="This is a comment"
            ... )
            >>> print(f"Added comment: {comment['id']}")
        """
        try:
            result = self.jira.issue_add_comment(
                issue_key=issue_key,
                comment=comment,
            )

            logger.info(f"Added comment to issue '{issue_key}'")
            return result

        except Exception as e:
            logger.error(f"Error adding comment to issue '{issue_key}': {e}")
            raise
