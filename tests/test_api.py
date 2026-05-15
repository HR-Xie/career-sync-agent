import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_index_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "Career-Sync" in resp.text


@pytest.mark.asyncio
async def test_upload_rejects_invalid_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {
            "resume": ("test.txt", b"not a resume", "text/plain"),
            "jd_image": ("jd.png", b"fake png", "image/png"),
        }
        resp = await client.post("/api/upload", files=files, data={"company_name": "test"})
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_status_404_for_unknown_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/status/nonexistent")
        assert resp.status_code == 404
