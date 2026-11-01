import os
import sys
import asyncio
import logging

# Ensure both backend and project root are in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(backend_dir)
for p in (backend_dir, repo_root):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.db.session import engine, Base, async_session_maker
from app.api.endpoints import router as api_router
from app.services.ws_manager import ws_manager
from app.services.playback_service import playback_service
from app.schemas.domain import PlaybackStateResponse, QueueItemResponse
from app.models.entities import utc_now

logger = logging.getLogger("BeatWave")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Launch Telegram bot background task if token is set
    bot_task = None
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "demo_bot_token":
        try:
            # Add project root to sys.path so bot can be imported
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from bot.main import main as run_bot
            bot_task = asyncio.create_task(run_bot())
            logger.info("🌊 Telegram Bot background task launched successfully.")
        except Exception as e:
            logger.error(f"Could not launch Telegram bot in background: {e}")

    yield

    if bot_task:
        bot_task.cancel()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="BeatWave - Telegram Group Music Synchronized Listening Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS if isinstance(settings.CORS_ALLOWED_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST routes under /api/v1
app.include_router(api_router, prefix="/api/v1")


# WebSocket endpoint
@app.websocket("/api/v1/rooms/{room_id}/ws")
async def websocket_room_endpoint(websocket: WebSocket, room_id: uuid.UUID):
    await ws_manager.connect(room_id, websocket)
    try:
        # Send initial snapshot upon connection
        async with async_session_maker() as session:
            playback = await playback_service.get_state(session, room_id)
            if playback:
                track = playback.current_queue_item.track if playback.current_queue_item else None
                duration_ms = track.duration_ms if track else 0
                current_pos = playback_service.calculate_current_position(playback, duration_ms)

                snapshot_dto = PlaybackStateResponse(
                    room_id=playback.room_id,
                    status=playback.status,
                    current_queue_item=QueueItemResponse.model_validate(playback.current_queue_item) if playback.current_queue_item else None,
                    position_ms=current_pos,
                    started_at=playback.started_at,
                    paused_at=playback.paused_at,
                    playback_rate=playback.playback_rate,
                    loop_mode=playback.loop_mode,
                    version=playback.version,
                    server_time=utc_now()
                )
                await websocket.send_json({
                    "type": "playback.snapshot",
                    "data": snapshot_dto.model_dump(mode="json")
                })

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(room_id, websocket)
    except Exception:
        ws_manager.disconnect(room_id, websocket)


# Serve pre-built Telegram Mini App frontend if available
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dir):
    assets_dir = os.path.join(frontend_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't intercept API or docs routes
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
            return None
        candidate = os.path.join(frontend_dir, full_path)
        if full_path and os.path.exists(candidate) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "status": "online",
            "docs": "/docs",
            "health": "/api/v1/health"
        }
