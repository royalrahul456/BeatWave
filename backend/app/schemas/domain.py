from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    redis: str
    timestamp: datetime


class TelegramSessionRequest(BaseModel):
    init_data: str


class UserResponse(BaseModel):
    id: UUID
    telegram_user_id: int
    username: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    is_premium: Optional[bool] = False

    class Config:
        from_attributes = True


class TelegramSessionResponse(BaseModel):
    token: str
    user: UserResponse


class TrackResponse(BaseModel):
    id: UUID
    provider: str
    provider_track_id: str
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    duration_ms: int
    artwork_url: Optional[str] = None
    audio_url: Optional[str] = None
    source_attribution: Optional[str] = None
    availability_status: str

    class Config:
        from_attributes = True


class QueueItemResponse(BaseModel):
    id: UUID
    room_id: UUID
    track: TrackResponse
    requested_by: UserResponse
    position: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PlaybackStateResponse(BaseModel):
    room_id: UUID
    status: str
    current_queue_item: Optional[QueueItemResponse] = None
    position_ms: int
    started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    playback_rate: float
    loop_mode: str
    version: int
    server_time: datetime

    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    id: UUID
    group_id: UUID
    group_title: Optional[str] = None
    status: str
    is_dj: bool = False
    is_admin: bool = False
    current_dj: Optional[UserResponse] = None
    members_count: int = 0
    members: List[UserResponse] = []
    playback_state: Optional[PlaybackStateResponse] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)


class SearchResponse(BaseModel):
    results: List[TrackResponse]


class AddRequestSchema(BaseModel):
    provider: str
    provider_track_id: str
    idempotency_key: Optional[str] = None
    play_now: Optional[bool] = False


class SeekRequestSchema(BaseModel):
    position_ms: int = Field(..., ge=0)


class LoopRequestSchema(BaseModel):
    mode: str = Field(..., pattern="^(off|track|queue)$")


class SetDJRequestSchema(BaseModel):
    user_id: UUID
