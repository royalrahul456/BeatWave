import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import (
    User,
    TelegramGroup,
    MusicRoom,
    RoomMember,
    QueueItem,
    PlaybackState,
    utc_now,
)
from app.schemas.domain import (
    HealthResponse,
    TelegramSessionRequest,
    TelegramSessionResponse,
    UserResponse,
    TrackResponse,
    QueueItemResponse,
    PlaybackStateResponse,
    RoomResponse,
    SearchRequest,
    SearchResponse,
    AddRequestSchema,
    SeekRequestSchema,
    LoopRequestSchema,
    SetDJRequestSchema,
)
from app.api.deps import get_current_user
from app.services.telegram_auth import telegram_auth_service
from app.services.room_service import room_service
from app.services.queue_service import queue_service
from app.services.playback_service import playback_service
from app.services.provider import provider_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.APP_ENV,
        database="connected",
        redis="connected",
        timestamp=utc_now()
    )


@router.post("/telegram/session", response_model=TelegramSessionResponse)
async def create_telegram_session(
    body: TelegramSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    is_valid, user_data = telegram_auth_service.validate_init_data(body.init_data)
    if not is_valid or not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram initData")

    telegram_user_id = user_data.get("id")
    if not telegram_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user id in initData")

    username = user_data.get("username")
    display_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or username

    user = await room_service.get_or_create_user(
        db=db,
        telegram_user_id=telegram_user_id,
        username=username,
        display_name=display_name
    )

    token = f"token_{user.telegram_user_id}"
    user_dto = UserResponse(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        display_name=user.display_name,
        photo_url=user_data.get("photo_url"),
        is_premium=user_data.get("is_premium", False)
    )
    return TelegramSessionResponse(
        token=token,
        user=user_dto
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.post("/rooms/group/{telegram_chat_id}", response_model=RoomResponse)
async def get_or_create_group_room(
    telegram_chat_id: int,
    title: Optional[str] = Query(None),
    chat_type: str = Query("supergroup"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    group = await room_service.get_or_create_group(db, telegram_chat_id, title=title, chat_type=chat_type)
    room = await room_service.get_or_create_room(db, group.id, created_by_user_id=user.id)
    await room_service.update_member_presence(db, room.id, user.id)

    # Fetch room details
    return await get_room(room.id, user=user, db=db)


@router.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    room = await db.get(MusicRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    await room_service.update_member_presence(db, room.id, user.id)

    group = await db.get(TelegramGroup, room.group_id)
    current_dj = await room_service.get_dj(db, room.id)
    is_dj = await room_service.is_dj_or_admin(db, room.id, user.id)

    # Count active members
    mem_res = await db.execute(
        select(func.count(RoomMember.id)).where(RoomMember.room_id == room.id)
    )
    members_count = mem_res.scalar() or 1

    # Playback state
    playback = await playback_service.get_state(db, room.id)
    playback_dto = None
    if playback:
        track = playback.current_queue_item.track if playback.current_queue_item else None
        duration_ms = track.duration_ms if track else 0
        current_pos = playback_service.calculate_current_position(playback, duration_ms)

        playback_dto = PlaybackStateResponse(
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

    return RoomResponse(
        id=room.id,
        group_id=room.group_id,
        group_title=group.title if group else "BeatWave Room",
        status=room.status,
        is_dj=is_dj,
        is_admin=is_dj,
        current_dj=UserResponse.model_validate(current_dj) if current_dj else None,
        members_count=members_count,
        playback_state=playback_dto
    )


@router.get("/rooms/{room_id}/state", response_model=PlaybackStateResponse)
async def get_room_state(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    playback = await playback_service.get_state(db, room_id)
    if not playback:
        raise HTTPException(status_code=404, detail="Playback state not found")

    track = playback.current_queue_item.track if playback.current_queue_item else None
    duration_ms = track.duration_ms if track else 0
    current_pos = playback_service.calculate_current_position(playback, duration_ms)

    # Server-side authoritative auto-advance:
    # If the track has naturally reached its duration, automatically advance to next song!
    if playback.status == "playing" and track and duration_ms > 0 and current_pos >= duration_ms:
        success, msg, new_pb = await playback_service.skip(db, room_id)
        if success and new_pb:
            playback = new_pb
            track = playback.current_queue_item.track if playback.current_queue_item else None
            duration_ms = track.duration_ms if track else 0
            current_pos = playback_service.calculate_current_position(playback, duration_ms)
        else:
            current_pos = 0

    return PlaybackStateResponse(
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


@router.get("/rooms/{room_id}/queue", response_model=List[QueueItemResponse])
async def get_room_queue(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    items = await queue_service.get_queue(db, room_id)
    return [QueueItemResponse.model_validate(item) for item in items]


@router.post("/rooms/{room_id}/search", response_model=SearchResponse)
async def search_catalogue(
    room_id: uuid.UUID,
    body: SearchRequest,
    user: User = Depends(get_current_user)
):
    results = await provider_service.search(body.query)
    return SearchResponse(results=results)


@router.post("/rooms/{room_id}/requests", response_model=QueueItemResponse)
async def add_track_request(
    room_id: uuid.UUID,
    body: AddRequestSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success, message, item = await queue_service.add_track_request(
        db=db,
        room_id=room_id,
        user_id=user.id,
        provider=body.provider,
        provider_track_id=body.provider_track_id,
        play_now=body.play_now if body.play_now is not None else True
    )
    if not success or not item:
        raise HTTPException(status_code=400, detail=message)

    await db.refresh(item, ["track", "requested_by"])
    return QueueItemResponse.model_validate(item)


@router.delete("/rooms/{room_id}/queue/{item_id}")
async def remove_queue_item(
    room_id: uuid.UUID,
    item_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_dj = await room_service.is_dj_or_admin(db, room_id, user.id)
    if not is_dj:
        raise HTTPException(status_code=403, detail="Only DJ can remove tracks from queue")

    success = await queue_service.remove_queue_item(db, room_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return {"message": "Queue item removed"}


# --- DJ Playback Controls ---

@router.post("/rooms/{room_id}/controls/pause", response_model=PlaybackStateResponse)
async def pause_playback(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_dj = await room_service.is_dj_or_admin(db, room_id, user.id)
    if not is_dj:
        raise HTTPException(status_code=403, detail="Only the DJ can control playback")

    success, msg, playback = await playback_service.pause(db, room_id)
    if not success or not playback:
        raise HTTPException(status_code=400, detail=msg)

    return await get_room_state(room_id, user=user, db=db)


@router.post("/rooms/{room_id}/controls/resume", response_model=PlaybackStateResponse)
async def resume_playback(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_dj = await room_service.is_dj_or_admin(db, room_id, user.id)
    if not is_dj:
        raise HTTPException(status_code=403, detail="Only the DJ can control playback")

    success, msg, playback = await playback_service.resume(db, room_id)
    if not success or not playback:
        raise HTTPException(status_code=400, detail=msg)

    return await get_room_state(room_id, user=user, db=db)


@router.post("/rooms/{room_id}/controls/seek", response_model=PlaybackStateResponse)
async def seek_playback(
    room_id: uuid.UUID,
    body: SeekRequestSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_dj = await room_service.is_dj_or_admin(db, room_id, user.id)
    if not is_dj:
        raise HTTPException(status_code=403, detail="Only the DJ can control playback")

    success, msg, playback = await playback_service.seek(db, room_id, body.position_ms)
    if not success or not playback:
        raise HTTPException(status_code=400, detail=msg)

    return await get_room_state(room_id, user=user, db=db)


@router.post("/rooms/{room_id}/controls/skip", response_model=PlaybackStateResponse)
async def skip_playback(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_dj = await room_service.is_dj_or_admin(db, room_id, user.id)
    if not is_dj:
        raise HTTPException(status_code=403, detail="Only the DJ can control playback")

    success, msg, playback = await playback_service.skip(db, room_id)
    if not success or not playback:
        raise HTTPException(status_code=400, detail=msg)

    return await get_room_state(room_id, user=user, db=db)


@router.post("/rooms/{room_id}/controls/loop", response_model=PlaybackStateResponse)
async def set_loop(
    room_id: uuid.UUID,
    body: LoopRequestSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_dj = await room_service.is_dj_or_admin(db, room_id, user.id)
    if not is_dj:
        raise HTTPException(status_code=403, detail="Only the DJ can control playback")

    success, msg, playback = await playback_service.set_loop(db, room_id, body.mode)
    if not success or not playback:
        raise HTTPException(status_code=400, detail=msg)

    return await get_room_state(room_id, user=user, db=db)


@router.post("/rooms/{room_id}/controls/stop", response_model=PlaybackStateResponse)
async def stop_playback(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_dj = await room_service.is_dj_or_admin(db, room_id, user.id)
    if not is_dj:
        raise HTTPException(status_code=403, detail="Only the DJ can control playback")

    success, msg, playback = await playback_service.stop(db, room_id)
    if not success or not playback:
        raise HTTPException(status_code=400, detail=msg)

    return await get_room_state(room_id, user=user, db=db)


@router.post("/rooms/{room_id}/dj")
async def appoint_dj(
    room_id: uuid.UUID,
    body: SetDJRequestSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Appoint DJ
    await room_service.set_dj(db, room_id, body.user_id, assigned_by_user_id=user.id)
    return {"message": "DJ appointed successfully", "dj_user_id": body.user_id}
