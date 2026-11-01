import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine, Base


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["environment"] == "development"


@pytest.mark.asyncio
async def test_telegram_session_and_room_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Session authentication
        sess_res = await client.post(
            "/api/v1/telegram/session",
            json={"init_data": "auth_date=1700000000&hash=mockhash&user=%7B%22id%22%3A123456%2C%22first_name%22%3A%22Alice%22%7D"}
        )
        assert sess_res.status_code == 200
        auth_data = sess_res.json()
        token = auth_data["token"]
        assert "token_" in token

        # 2. Create or get group room
        room_res = await client.post(
            "/api/v1/rooms/group/123456789?title=Test+Music+Group",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert room_res.status_code == 200
        room = room_res.json()
        room_id = room["id"]
        assert room["status"] in ["idle", "playing"]

        # 3. Search catalogue
        search_res = await client.post(
            f"/api/v1/rooms/{room_id}/search",
            json={"query": "Cyan Pulse"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert search_res.status_code == 200
        results = search_res.json()["results"]
        assert len(results) > 0
        track = results[0]

        # 4. Request track to queue
        req_res = await client.post(
            f"/api/v1/rooms/{room_id}/requests",
            json={"provider": track["provider"], "provider_track_id": track["provider_track_id"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert req_res.status_code == 200
        queue_item = req_res.json()
        assert queue_item["status"] in ["queued", "current"]

        # 5. Check queue list
        queue_res = await client.get(
            f"/api/v1/rooms/{room_id}/queue",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert queue_res.status_code == 200
        q_items = queue_res.json()
        assert len(q_items) >= 1

        # 6. DJ Pause control
        pause_res = await client.post(
            f"/api/v1/rooms/{room_id}/controls/pause",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert pause_res.status_code == 200
        pb_state = pause_res.json()
        assert pb_state["status"] == "paused"

        # 7. DJ Resume control
        resume_res = await client.post(
            f"/api/v1/rooms/{room_id}/controls/resume",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resume_res.status_code == 200
        assert resume_res.json()["status"] == "playing"
