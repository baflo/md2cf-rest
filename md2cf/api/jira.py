"""
JIRA API Client with PAT Authentication.

This module provides a client for interacting with JIRA REST API
using Personal Access Token (PAT) authentication.
"""

import logging
import json
import traceback
from typing import Any, Dict, Optional, List
from urllib.parse import urljoin

from atlassian import Jira
from requests.exceptions import HTTPError


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
        issue_type: str,
        fields: Dict[str, Any],
        parent_key: Optional[str] = None,
        convert_markdown: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a new issue in JIRA with a dynamic set of fields.

        Args:
            project: Project key (e.g., "PROJ")
            summary: Issue summary/title
            issue_type: Issue type JSON object string (e.g., '{"id": "90"}')
            fields: A dictionary containing all other fields for the issue.
            parent_key: Key of the parent issue for sub-tasks (e.g., "PROJ-123")
            convert_markdown: Whether to convert description from Markdown to Jira Wiki Markup.

        Returns:
            Created issue data dictionary with 'id', 'key', and 'self' URL
        """
        try:
            # If a description is present in the fields and conversion is enabled
            if convert_markdown and 'description' in fields and fields['description']:
                from md2cf.converter import MarkdownToJira
                converter = MarkdownToJira()
                logger.info("Converting description from Markdown to Jira Wiki Markup")
                fields['description'] = converter.convert(fields['description'])

            # Base payload with required fields
            final_fields = {
                "project": {"key": project},
                "summary": summary,
            }

            if parent_key:
                final_fields["parent"] = {"key": parent_key}

            # Add the parsed issue_type object
            try:
                final_fields["issuetype"] = json.loads(issue_type)
            except json.JSONDecodeError:
                 raise ValueError("Issue type is not a valid JSON object string.")

            # Merge the dynamic fields
            final_fields.update(fields)

            api_path = self.jira.resource_url('issue')
            payload = {"fields": final_fields}

            logger.debug(f"Creating issue with payload: {payload}")

            result = self.jira.post(api_path, json=payload)
            logger.info(f"Successfully created issue '{result['key']}' in project '{project}'")
            return result
        except HTTPError as e:
            logger.error(f"Error creating issue in project '{project}': {e}")

            # Try to extract more details from HTTPError response
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"JIRA API error details: {error_details}")

                    # Log which field is causing the problem if available
                    if 'errors' in error_details:
                        for field_name, field_error in error_details['errors'].items():
                            logger.error(f"Field '{field_name}' error: {field_error}")

                except Exception:
                    logger.error(f"Response text: {e.response.text}")

            logger.error(traceback.format_exc())
            raise
        except Exception as e:
            logger.error(f"Error creating issue in project '{project}': {e}")
            logger.error(traceback.format_exc())
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
            print(f"Start: {start}, Limit: {limit}, Fields: {fields or 'default'}")

            # Use the jql method from atlassian-python-api
            result = self.jira.jql(
                jql=jql,
                # fields=fields or "summary,status,issuetype,assignee,priority,created,updated",
                fields=fields or None,
                start=start,
                limit=limit,
            )

            print(result)

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
            # Better error logging with more details
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"Error getting projects: {error_msg}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"JIRA URL: {self.url}")
            logger.error(f"Cloud mode: {self.cloud}")

            # Try to extract more details from HTTPError
            if hasattr(e, 'response'):
                logger.error(f"HTTP Status Code: {getattr(e.response, 'status_code', 'N/A')}")
                logger.error(f"HTTP Response Text: {getattr(e.response, 'text', 'N/A')}")
            if hasattr(e, 'request'):
                logger.error(f"Request URL: {getattr(e.request, 'url', 'N/A')}")

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

    def assign_issue(self, issue_key: str, assignee: str) -> None:
        """
        Assign an issue to a user, ensuring the payload is correct for either
        Jira Server/DC or Jira Cloud.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            assignee: Assignee username (Server/DC) or account ID (Cloud)
        """
        try:
            logger.info(f"Assigning issue '{issue_key}' to '{assignee}'")
            
            # The atlassian-python-api's assign_issue() method incorrectly builds
            # the payload for some Jira Server versions. We will construct the
            # payload manually and use a direct request call to ensure correctness.
            if self.cloud:
                payload = {"accountId": assignee}
            else:
                # Jira Server/DC expects the 'name' field for username assignment.
                payload = {"name": assignee}
            
            url = self.jira.resource_url(f"issue/{issue_key}/assignee")
            
            # Using the low-level request method with `data` parameter, which the
            # library correctly serializes to JSON for PUT requests.
            self.jira.request(method='PUT', path=url, data=payload)
            
            logger.info(f"Successfully assigned issue '{issue_key}' to '{assignee}'")

        except Exception as e:
            logger.error(f"Error assigning issue '{issue_key}': {e}")
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

    def attach_file(
        self,
        issue_key: str,
        file_path: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Attach a file to an issue.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            file_path: Path to the file to attach
            comment: Optional comment for the attachment

        Returns:
            Attachment data dictionary

        Example:
            >>> result = client.attach_file(
            ...     issue_key="PROJ-123",
            ...     file_path="/path/to/file.pdf",
            ...     comment="Technical specification"
            ... )
            >>> print(f"Attached file: {result}")
        """
        try:
            # Use the add_attachment method from atlassian-python-api
            result = self.jira.add_attachment(
                issue_key=issue_key,
                filename=file_path,
            )

            logger.info(f"Attached file '{file_path}' to issue '{issue_key}'")
            return result

        except Exception as e:
            logger.error(f"Error attaching file to issue '{issue_key}': {e}")
            raise

    def get_create_issue_meta(
        self,
        project_keys: Optional[List[str]] = None,
        issue_type_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get metadata for creating issues (fields, allowed values, etc.).

        Args:
            project_keys: Optional list of project keys to filter (e.g., ["SCH", "FM"])
            issue_type_names: Optional list of issue type names to filter (e.g., ["Story", "Bug"])

        Returns:
            Metadata dictionary with projects, issue types, and field definitions

        Example:
            >>> meta = client.get_create_issue_meta(
            ...     project_keys=["DEMO"],
            ...     issue_type_names=["Story"]
            ... )
            >>> for project in meta['projects']:
            ...     print(f"Project: {project['key']}")
            ...     for issue_type in project['issuetypes']:
            ...         print(f"  Type: {issue_type['name']}")
        """
        try:
            # Use alternative approach: get projects and build metadata manually
            # This works better with newer Jira versions where issue_createmeta is deprecated

            projects_to_query = project_keys if project_keys else []

            # If no specific projects requested, get all accessible projects
            if not projects_to_query:
                all_projects = self.get_projects()
                projects_to_query = [p["key"] for p in all_projects[:10]]  # Limit to first 10
                logger.info(f"No projects specified, using first {len(projects_to_query)} accessible projects")

            result_projects = []

            for project_key in projects_to_query:
                try:
                    # Get project details including issue types
                    project = self.get_project(project_key)
                    if not project:
                        logger.warning(f"Project {project_key} not found, skipping")
                        continue

                    # Get issue types for this project
                    issue_types = project.get("issueTypes", [])

                    # Filter by issue type names if specified
                    if issue_type_names:
                        issue_types = [it for it in issue_types if it["name"] in issue_type_names]

                    # For each issue type, get field metadata using the new API
                    enriched_issue_types = []
                    for issue_type in issue_types:
                        try:
                            # Use the newer issue_createmeta_fieldtypes method
                            field_meta = self.jira.issue_createmeta_fieldtypes(
                                project=project_key,
                                issue_type_id=issue_type["id"]
                            )

                            # Convert field metadata to expected format
                            fields = {}
                            if field_meta and "values" in field_meta:
                                for field in field_meta["values"]:
                                    field_id = field.get("fieldId", field.get("key", ""))
                                    fields[field_id] = {
                                        "required": field.get("required", False),
                                        "name": field.get("name", ""),
                                        "schema": field.get("schema", {}),
                                        "operations": field.get("operations", []),
                                        "allowedValues": field.get("allowedValues", [])
                                    }

                            enriched_issue_types.append({
                                "id": issue_type["id"],
                                "name": issue_type["name"],
                                "description": issue_type.get("description", ""),
                                "iconUrl": issue_type.get("iconUrl", ""),
                                "subtask": issue_type.get("subtask", False),
                                "fields": fields
                            })
                        except Exception as e:
                            logger.warning(f"Could not get field metadata for {project_key}/{issue_type['name']}: {e}")
                            # Include issue type without detailed fields
                            enriched_issue_types.append({
                                "id": issue_type["id"],
                                "name": issue_type["name"],
                                "description": issue_type.get("description", ""),
                                "iconUrl": issue_type.get("iconUrl", ""),
                                "subtask": issue_type.get("subtask", False),
                                "fields": {}
                            })

                    result_projects.append({
                        "key": project["key"],
                        "name": project["name"],
                        "id": project.get("id", ""),
                        "issuetypes": enriched_issue_types
                    })

                except Exception as e:
                    logger.error(f"Error processing project {project_key}: {e}")
                    continue

            result = {"projects": result_projects}
            logger.info(f"Retrieved create issue metadata for {len(result_projects)} projects")
            return result

        except Exception as e:
            logger.error(f"Error getting create issue metadata: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            raise

    def search_users(
        self,
        query: str,
        project: Optional[str] = None,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for users (for assignee selection).

        Args:
            query: Search term (username, display name, or email)
            project: Optional project key to find assignable users for that project
            max_results: Maximum number of results to return (default: 50)

        Returns:
            List of user data dictionaries

        Note:
            When a project is specified, this method first attempts to use the
            project-specific assignable users API. If that fails (due to permissions
            or API limitations), it falls back to a global user search.
        """
        try:
            search_query = query.strip() if query else ""

            if project:
                # Try project-specific assignable users search first
                result = self._search_project_users(project, search_query, max_results)
            else:
                # Global user search requires a non-empty query
                result = self._search_global_users(search_query, max_results)

            if result is None:
                logger.warning(f"User search returned None for query '{search_query}'")
                return []

            # Ensure result is always a list
            if not isinstance(result, list):
                logger.error(f"Unexpected return type from user search: {type(result)}")
                return []

            logger.info(f"Found {len(result)} users for query '{search_query}' in project '{project}'")
            return result

        except Exception as e:
            logger.error(f"Error searching users with query '{query}' in project '{project}': {e}")
            logger.error(traceback.format_exc())
            raise

    def _search_project_users(
        self,
        project: str,
        search_query: str,
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """
        Search for assignable users in a specific project.

        Attempts to use project-specific API first, falls back to global search if unavailable.
        """
        try:
            # Try project-specific assignable users API
            all_assignable = self.jira.get_all_assignable_users_for_project(
                project_key=f"{project}&username=Florian Bachmann",
                start=0,
                limit=max_results
            )

            print("search_query", search_query)

            if not all_assignable:
                raise ValueError("No users returned from project-specific search")

            # Filter by query if provided
            if search_query:
                query_lower = search_query.lower()
                return [
                    user for user in all_assignable
                    if (query_lower in user.get('displayName', '').lower() or
                        query_lower in user.get('emailAddress', '').lower() or
                        query_lower in user.get('name', '').lower())
                ]
            else:
                return all_assignable

        except (HTTPError, ValueError) as e:
            # Fallback to global user search
            # This happens when the project-specific API is not available or returns no results
            logger.warning(
                f"Project-specific user search for '{project}' unavailable: {e}. "
                f"Using global search instead."
            )
            # Use '.' as wildcard if no specific query provided
            fallback_query = search_query if search_query else "."
            return self._search_global_users(fallback_query, max_results)

    def _search_global_users(
        self,
        search_query: str,
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """
        Search for users globally using the user search API.

        Args:
            search_query: Search term (required, use wildcards like '.', '%', 'a' for broad search)
            max_results: Maximum number of results

        Returns:
            List of user dictionaries
        """
        if not search_query:
            logger.warning("Global user search requires a query. Returning empty list.")
            return []

        # Try different wildcard strategies if the initial query is a wildcard
        wildcard_queries = [search_query]

        # If using wildcard characters, try alternatives
        if search_query in [".", "%", "*"]:
            wildcard_queries = [".", "%", "a", "e", "i"]
            logger.info(f"Using wildcard search, will try multiple strategies: {wildcard_queries}")

        last_exception = None
        for attempt_query in wildcard_queries:
            try:
                logger.debug(f"Attempting global user search with query: '{attempt_query}'")

                # Try using direct API call for more control
                if self.cloud:
                    # Cloud API endpoint
                    url = self.jira.resource_url("user/search")
                    params = {"query": attempt_query, "maxResults": max_results}
                else:
                    # Server/Data Center API endpoint
                    url = self.jira.resource_url("user/search")
                    params = {"username": attempt_query, "maxResults": max_results}

                logger.debug(f"Calling {url} with params: {params}")
                users = self.jira.get(url, params=params)

                logger.debug(f"API returned type: {type(users)}, value: {users}")

                if not users:
                    logger.debug(f"Query '{attempt_query}' returned no users")
                    continue

                if not isinstance(users, list):
                    logger.error(f"Unexpected return type from user search: {type(users)}")
                    logger.error(f"Returned value: {users}")
                    continue

                logger.info(f"Successfully found {len(users)} users with query '{attempt_query}'")
                return users

            except Exception as e:
                logger.debug(f"Global user search with query '{attempt_query}' failed: {e}")
                last_exception = e
                continue

        # If all attempts failed, log the last exception
        if last_exception:
            logger.error(f"All global user search attempts failed. Last error: {last_exception}")
            logger.error(traceback.format_exc())

        logger.warning(f"Could not find any users with any wildcard strategy")
        return []

    def get_edit_issue_meta(
        self,
        issue_key: str,
    ) -> Dict[str, Any]:
        """
        Get metadata for editing an issue (fields, allowed values, etc.).

        Args:
            issue_key: The issue key (e.g., "PROJ-123")

        Returns:
            Metadata dictionary with field definitions for editing

        Example:
            >>> meta = client.get_edit_issue_meta("PROJ-123")
            >>> for field_id, field_info in meta['fields'].items():
            ...     print(f"Field: {field_info['name']}")
            ...     print(f"  Required: {field_info['required']}")
        """
        try:
            # Use the editmeta endpoint to get field metadata for editing this issue
            # GET /rest/api/2/issue/{issueIdOrKey}/editmeta
            api_path = self.jira.resource_url(f'issue/{issue_key}/editmeta')

            logger.info(f"Fetching edit metadata for issue '{issue_key}'")
            result = self.jira.get(api_path)

            if not result:
                logger.warning(f"Edit metadata for issue '{issue_key}' returned empty result")
                return {"fields": {}}

            # The result contains a 'fields' dictionary with field metadata
            fields = result.get("fields", {})

            logger.info(f"Retrieved edit metadata for issue '{issue_key}' with {len(fields)} fields")
            return result

        except Exception as e:
            logger.error(f"Error getting edit issue metadata for '{issue_key}': {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            raise

    def get_fields(self) -> List[Dict[str, Any]]:
        """
        Get all available fields (including custom fields).

        Returns:
            List of field data dictionaries

        Example:
            >>> fields = client.get_fields()
            >>> for field in fields:
            ...     if field['custom']:
            ...         print(f"{field['name']}: {field['id']}")
        """
        try:
            result = self.jira.get_all_fields()

            if result is None:
                logger.warning("Get fields call returned None")
                return []

            logger.info(f"Retrieved {len(result)} fields")
            return result

        except Exception as e:
            logger.error(f"Error getting fields: {e}")
            raise
