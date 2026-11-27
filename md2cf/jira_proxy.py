"""
Transparent JIRA proxy.

Forwards every request under ``/jira/proxy/`` unchanged to the JIRA instance
configured in the ``JIRA_URL`` environment variable. Browser-based clients
(e.g. Super Productivity) can use it as their JIRA base URL to avoid CORS
problems, without a separate reverse proxy in front of md2cf.

- The ``Authorization`` header (Basic or Bearer/PAT) is passed through as-is.
- ``X-Atlassian-Token: no-check`` is always set (JIRA's CSRF check).
- Redirects and cookies from JIRA are rewritten to point at the proxy, so the
  browser never ends up talking to JIRA directly.
- Response bodies are streamed, so large attachments are not buffered.
- TLS is verified against the system CA bundle (``REQUESTS_CA_BUNDLE``).
"""

import logging
import os
import re
from typing import Iterator, List, Tuple

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from starlette.background import BackgroundTask

logger = logging.getLogger(__name__)

PROXY_PREFIX = "/jira/proxy"

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 120

# Headers that must not be forwarded by a proxy (RFC 7230, section 6.1),
# plus those that requests/the ASGI server set themselves.
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade",
}
SKIP_REQUEST_HEADERS = HOP_BY_HOP | {"host", "content-length"}
SKIP_RESPONSE_HEADERS = HOP_BY_HOP | {"content-length", "location", "set-cookie"}

router = APIRouter()


def _jira_base_url() -> str:
    base = os.environ.get("JIRA_URL", "").strip().rstrip("/")
    if not base:
        raise HTTPException(
            status_code=503,
            detail="JIRA proxy is not configured (set the JIRA_URL environment variable)",
        )
    return base


def rewrite_location(location: str, jira_base: str, proxy_base: str) -> str:
    """Point redirects to JIRA at the proxy instead (kept relative, like nginx's
    ``absolute_redirect off``, so the scheme seen by the browser is preserved)."""
    if location == jira_base or location.startswith(jira_base + "/"):
        return proxy_base + (location[len(jira_base):] or "/")
    # Root-relative redirect on the JIRA host, e.g. "/login.jsp"
    jira_path = re.sub(r"^https?://[^/]+", "", jira_base)
    if location.startswith("/") and not location.startswith("//"):
        if jira_path and location.startswith(jira_path):
            location = location[len(jira_path):]
        return proxy_base + location
    return location


def rewrite_set_cookie(cookie: str, jira_base: str, proxy_base: str) -> str:
    """Drop the cookie's Domain (so it binds to the proxy host) and move its
    Path below the proxy prefix."""
    jira_path = re.sub(r"^https?://[^/]+", "", jira_base)
    parts = [p.strip() for p in cookie.split(";")]
    out = [parts[0]]
    has_path = False
    for attr in parts[1:]:
        name = attr.split("=", 1)[0].strip().lower()
        if name == "domain":
            continue
        if name == "path":
            has_path = True
            path = attr.split("=", 1)[1].strip() if "=" in attr else "/"
            if jira_path and path.startswith(jira_path):
                path = path[len(jira_path):] or "/"
            attr = "Path=" + (proxy_base + path if path != "/" else proxy_base + "/")
        out.append(attr)
    if not has_path:
        out.append(f"Path={proxy_base}/")
    return "; ".join(out)


def _forward_headers(request: Request) -> dict:
    headers = {
        k: v for k, v in request.headers.items() if k.lower() not in SKIP_REQUEST_HEADERS
    }
    headers["X-Atlassian-Token"] = "no-check"
    headers["X-Forwarded-Host"] = request.headers.get("host", "")
    headers["X-Forwarded-Proto"] = request.headers.get("x-forwarded-proto", request.url.scheme)
    return headers


def _response_headers(resp: requests.Response, jira_base: str, proxy_base: str) -> List[Tuple[str, str]]:
    raw_headers = resp.raw.headers  # urllib3 HTTPHeaderDict, keeps repeated headers
    result = [
        (k, v) for k, v in raw_headers.items() if k.lower() not in SKIP_RESPONSE_HEADERS
    ]
    location = raw_headers.get("Location")
    if location:
        result.append(("Location", rewrite_location(location, jira_base, proxy_base)))
    for cookie in raw_headers.getlist("Set-Cookie"):
        result.append(("Set-Cookie", rewrite_set_cookie(cookie, jira_base, proxy_base)))
    return result


@router.api_route(
    PROXY_PREFIX + "/{jira_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
    tags=["jira-proxy"],
    summary="Transparent JIRA proxy",
)
async def proxy_jira(jira_path: str, request: Request) -> StreamingResponse:
    """
    Forward the request unchanged to ``$JIRA_URL/<jira_path>``.

    Send the same headers as to JIRA itself, e.g.
    ``Authorization: Bearer <PAT>`` or ``Authorization: Basic <base64(user:token)>``.
    """
    jira_base = _jira_base_url()
    proxy_base = request.scope.get("root_path", "") + PROXY_PREFIX

    url = f"{jira_base}/{jira_path}"
    if request.url.query:
        url += "?" + request.url.query

    body = await request.body()
    try:
        # requests is blocking: run it in the threadpool. StreamingResponse
        # iterates the sync body iterator in the threadpool as well.
        resp = await run_in_threadpool(
            requests.request,
            request.method,
            url,
            headers=_forward_headers(request),
            data=body or None,
            allow_redirects=False,
            stream=True,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
    except requests.RequestException as e:
        logger.error(f"JIRA proxy: {request.method} {url} failed: {e}")
        raise HTTPException(status_code=502, detail=f"JIRA not reachable: {e}")

    def body_iter() -> Iterator[bytes]:
        # decode_content=False: pass compressed bodies through untouched,
        # Content-Encoding is forwarded as well.
        yield from resp.raw.stream(64 * 1024, decode_content=False)

    response = StreamingResponse(
        body_iter(),
        status_code=resp.status_code,
        background=BackgroundTask(resp.close),
    )
    # Replace StreamingResponse's own headers entirely with JIRA's
    # (raw_headers keeps repeated Set-Cookie headers).
    response.raw_headers = [
        (k.lower().encode("latin-1"), v.encode("latin-1"))
        for k, v in _response_headers(resp, jira_base, proxy_base)
    ]
    return response

