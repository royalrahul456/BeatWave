import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine, Base, async_session_maker
from app.api.endpoints import router as api_router
from app.services.ws_manager import ws_manager
from app.services.playback_service import playback_service
from app.schemas.domain import PlaybackStateResponse, QueueItemResponse
from app.models.entities import utc_now


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
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


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
