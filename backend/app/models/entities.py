import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, BigInteger, Integer, Float, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    memberships: Mapped[List["RoomMember"]] = relationship("RoomMember", back_populates="user")
    roles: Mapped[List["RoomRole"]] = relationship("RoomRole", back_populates="user", foreign_keys="RoomRole.user_id")


class TelegramGroup(Base):
    __tablename__ = "telegram_groups"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    chat_type: Mapped[str] = mapped_column(String(50), default="supergroup")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    rooms: Mapped[List["MusicRoom"]] = relationship("MusicRoom", back_populates="group")
    settings: Mapped[Optional["GroupSettings"]] = relationship("GroupSettings", back_populates="group", uselist=False)


class MusicRoom(Base):
    __tablename__ = "music_rooms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("telegram_groups.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="idle")  # created, playing, paused, idle, ended
    current_track_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tracks.id"), nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    group: Mapped["TelegramGroup"] = relationship("TelegramGroup", back_populates="rooms")
    queue_items: Mapped[List["QueueItem"]] = relationship("QueueItem", back_populates="room", order_by="QueueItem.position")
    playback_state: Mapped[Optional["PlaybackState"]] = relationship("PlaybackState", back_populates="room", uselist=False)
    roles: Mapped[List["RoomRole"]] = relationship("RoomRole", back_populates="room")
    members: Mapped[List["RoomMember"]] = relationship("RoomMember", back_populates="room")


class RoomMember(Base):
    __tablename__ = "room_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("music_rooms.id"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    room: Mapped["MusicRoom"] = relationship("MusicRoom", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_member"),
    )


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_track_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    artist: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    album: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    artwork_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    source_attribution: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    availability_status: Mapped[str] = mapped_column(String(50), default="available")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("provider", "provider_track_id", name="uq_provider_track"),
    )


class QueueItem(Base):
    __tablename__ = "queue_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("music_rooms.id"), index=True, nullable=False)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id"), index=True, nullable=False)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued")  # queued, current, played, skipped, removed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    room: Mapped["MusicRoom"] = relationship("MusicRoom", back_populates="queue_items")
    track: Mapped["Track"] = relationship("Track")
    requested_by: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_queue_room_status_pos", "room_id", "status", "position"),
    )


class PlaybackState(Base):
    __tablename__ = "playback_states"

    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("music_rooms.id"), primary_key=True)
    current_queue_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("queue_items.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="idle")  # playing, paused, idle, stopped
    position_ms: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    playback_rate: Mapped[float] = mapped_column(Float, default=1.0)
    loop_mode: Mapped[str] = mapped_column(String(50), default="off")  # off, track, queue
    version: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    room: Mapped["MusicRoom"] = relationship("MusicRoom", back_populates="playback_state")
    current_queue_item: Mapped[Optional["QueueItem"]] = relationship("QueueItem")


class RoomRole(Base):
    __tablename__ = "room_roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("music_rooms.id"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="dj")  # dj, moderator
    assigned_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    room: Mapped["MusicRoom"] = relationship("MusicRoom", back_populates="roles")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="roles")

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", "role", name="uq_room_user_role"),
    )


class GroupSettings(Base):
    __tablename__ = "group_settings"

    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("telegram_groups.id"), primary_key=True)
    requests_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_requests_per_user_window: Mapped[int] = mapped_column(Integer, default=5)
    duplicate_policy: Mapped[str] = mapped_column(String(50), default="reject")  # reject, allow
    allow_member_queue_moderation: Mapped[bool] = mapped_column(Boolean, default=False)
    temporary_dj_policy: Mapped[str] = mapped_column(String(50), default="admin_only")
    history_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    group: Mapped["TelegramGroup"] = relationship("TelegramGroup", back_populates="settings")
