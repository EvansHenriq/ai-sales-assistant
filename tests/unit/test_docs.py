"""The interactive API docs (/docs) must render under the app's strict CSP.

FastAPI's default Swagger UI loads its assets from a CDN plus an inline script,
which the global ``default-src 'none'`` CSP blocks (the page renders blank). We
self-host the assets and relax the CSP for the ``/docs`` route only — every API
response keeps ``default-src 'none'``.
"""

from httpx import AsyncClient


async def test_docs_served_from_self_not_cdn(client: AsyncClient) -> None:
    response = await client.get("/docs")
    assert response.status_code == 200
    body = response.text
    assert "/static/swagger-ui-bundle.js" in body
    assert "/static/swagger-ui.css" in body
    assert "cdn.jsdelivr.net" not in body


async def test_docs_csp_allows_self_assets(client: AsyncClient) -> None:
    response = await client.get("/docs")
    csp = response.headers["Content-Security-Policy"]
    # The bundle is loaded from 'self' and Swagger fetches /openapi.json.
    assert "script-src 'self'" in csp
    assert "connect-src 'self'" in csp


async def test_static_swagger_bundle_is_served(client: AsyncClient) -> None:
    response = await client.get("/static/swagger-ui-bundle.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


async def test_api_routes_keep_strict_csp(client: AsyncClient) -> None:
    """The CSP relaxation is scoped to /docs; API responses stay locked down."""
    response = await client.get("/health")
    csp = response.headers["Content-Security-Policy"]
    assert csp.startswith("default-src 'none'")
    assert "script-src 'self'" not in csp
