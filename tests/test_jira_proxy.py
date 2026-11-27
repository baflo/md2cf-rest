"""Tests for the transparent JIRA proxy."""

import gzip
from io import BytesIO
from unittest.mock import patch

import pytest
import requests
from fastapi.testclient import TestClient
from urllib3 import HTTPResponse
from urllib3._collections import HTTPHeaderDict

from md2cf.jira_proxy import rewrite_location, rewrite_set_cookie
from md2cf.rest_api import app

JIRA = "https://jira.example.com/jira"
PROXY = "/jira/proxy"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JIRA_URL", JIRA + "/")
    return TestClient(app)


def fake_response(status=200, body=b"", headers=None):
    """Build a requests.Response backed by a real urllib3 response."""
    hdrs = HTTPHeaderDict()
    for k, v in headers or []:
        hdrs.add(k, v)
    raw = HTTPResponse(body=BytesIO(body), headers=hdrs, status=status, preload_content=False)
    resp = requests.Response()
    resp.status_code = status
    resp.raw = raw
    resp.headers = requests.structures.CaseInsensitiveDict(hdrs)
    return resp


@pytest.fixture
def jira():
    with patch("md2cf.jira_proxy.requests.request") as mock:
        mock.return_value = fake_response(
            200, b'{"key": "PROJ-1"}', [("Content-Type", "application/json")]
        )
        yield mock


class TestForwarding:
    def test_get_forwards_path_query_and_auth(self, client, jira):
        r = client.get(
            f"{PROXY}/rest/api/2/issue/PROJ-1?expand=changelog&fields=a,b",
            headers={"Authorization": "Bearer my-pat"},
        )
        assert r.status_code == 200
        assert r.json() == {"key": "PROJ-1"}
        assert r.headers["content-type"] == "application/json"

        method, url = jira.call_args.args
        kwargs = jira.call_args.kwargs
        assert method == "GET"
        assert url == f"{JIRA}/rest/api/2/issue/PROJ-1?expand=changelog&fields=a,b"
        assert kwargs["headers"]["authorization"] == "Bearer my-pat"
        assert kwargs["headers"]["X-Atlassian-Token"] == "no-check"
        assert "host" not in {k.lower() for k in kwargs["headers"]}
        assert kwargs["allow_redirects"] is False
        assert kwargs["stream"] is True

    def test_basic_auth_passed_through(self, client, jira):
        client.get(f"{PROXY}/rest/api/2/myself", auth=("user@example.com", "api-token"))
        auth = jira.call_args.kwargs["headers"]["authorization"]
        assert auth.startswith("Basic ")

    def test_put_body_forwarded_unchanged(self, client, jira):
        body = b'{"fields": {"summary": "x"}}'
        client.put(
            f"{PROXY}/rest/api/2/issue/PROJ-1",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert jira.call_args.args[0] == "PUT"
        assert jira.call_args.kwargs["data"] == body
        assert jira.call_args.kwargs["headers"]["content-type"] == "application/json"

    def test_non_rest_paths_allowed(self, client, jira):
        client.get(f"{PROXY}/secure/attachment/123/file.png")
        assert jira.call_args.args[1] == f"{JIRA}/secure/attachment/123/file.png"

    def test_jira_error_status_passed_through(self, client, jira):
        jira.return_value = fake_response(
            404, b'{"errorMessages": ["nope"]}', [("Content-Type", "application/json")]
        )
        r = client.get(f"{PROXY}/rest/api/2/issue/NOPE-1")
        assert r.status_code == 404
        assert r.json() == {"errorMessages": ["nope"]}

    def test_compressed_body_passed_through(self, client, jira):
        payload = gzip.compress(b'{"ok": true}')
        jira.return_value = fake_response(
            200, payload,
            [("Content-Type", "application/json"), ("Content-Encoding", "gzip")],
        )
        r = client.get(f"{PROXY}/rest/api/2/serverInfo")
        assert r.json() == {"ok": True}  # client decodes it, so it arrived intact

    def test_unreachable_jira_returns_502(self, client, jira):
        jira.side_effect = requests.ConnectionError("boom")
        r = client.get(f"{PROXY}/rest/api/2/myself")
        assert r.status_code == 502

    def test_missing_jira_url_returns_503(self, client, jira, monkeypatch):
        monkeypatch.delenv("JIRA_URL")
        r = client.get(f"{PROXY}/rest/api/2/myself")
        assert r.status_code == 503
        jira.assert_not_called()


class TestRedirectsAndCookies:
    def test_redirect_rewritten_to_proxy(self, client, jira):
        jira.return_value = fake_response(
            302, b"", [("Location", f"{JIRA}/login.jsp?os_destination=x")]
        )
        r = client.get(f"{PROXY}/secure/Dashboard.jspa", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"] == f"{PROXY}/login.jsp?os_destination=x"

    def test_multiple_cookies_rewritten(self, client, jira):
        jira.return_value = fake_response(200, b"{}", [
            ("Set-Cookie", "JSESSIONID=abc; Path=/jira; HttpOnly"),
            ("Set-Cookie", "atlassian.xsrf.token=t; Domain=jira.example.com; Path=/jira"),
        ])
        r = client.get(f"{PROXY}/rest/api/2/myself")
        cookies = r.headers.get_list("set-cookie")
        assert cookies == [
            f"JSESSIONID=abc; Path={PROXY}/; HttpOnly",
            f"atlassian.xsrf.token=t; Path={PROXY}/",
        ]

    @pytest.mark.parametrize("location,expected", [
        (f"{JIRA}/browse/P-1", f"{PROXY}/browse/P-1"),
        (JIRA, f"{PROXY}/"),
        ("/jira/login.jsp", f"{PROXY}/login.jsp"),
        ("https://other.example.com/x", "https://other.example.com/x"),
    ])
    def test_rewrite_location(self, location, expected):
        assert rewrite_location(location, JIRA, PROXY) == expected

    def test_rewrite_cookie_without_path(self):
        assert rewrite_set_cookie("a=b", JIRA, PROXY) == f"a=b; Path={PROXY}/"


class TestCors:
    def test_preflight(self, client, jira):
        r = client.options(
            f"{PROXY}/rest/api/2/issue/PROJ-1",
            headers={
                "Origin": "https://superprod.localhost",
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert r.status_code == 200
        assert r.headers["access-control-allow-origin"] == "https://superprod.localhost"
        jira.assert_not_called()
