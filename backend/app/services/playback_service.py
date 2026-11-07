import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    MusicRoom,
    PlaybackState,
    QueueItem,
    Track,
    utc_now,
)


class PlaybackService:
    @staticmethod
    def calculate_current_position(playback: PlaybackState, duration_ms: int) -> int:
        """
        Calculates authoritative current position in milliseconds:
        current_position_ms = position_at_start_ms + (server_now - started_at) * playback_rate
        Clamped to track duration.
        """
        if playback.status != "playing" or not playback.started_at:
            return playback.position_ms

        now = utc_now()
        started_at = playback.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        elapsed_seconds = (now - started_at).total_seconds()
        calculated_ms = playback.position_ms + int(elapsed_seconds * 1000 * playback.playback_rate)

        if duration_ms > 0:
            return min(calculated_ms, duration_ms)
        return max(0, calculated_ms)

    @staticmethod
    async def get_state(
        db: AsyncSession,
        room_id: uuid.UUID
    ) -> Optional[PlaybackState]:
        result = await db.execute(
            select(PlaybackState)
            .where(PlaybackState.room_id == room_id)
            .options(
                selectinload(PlaybackState.current_queue_item).selectinload(QueueItem.track),
                selectinload(PlaybackState.current_queue_item).selectinload(QueueItem.requested_by),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_and_sync_state(
        db: AsyncSession,
        room_id: uuid.UUID
    ) -> Optional[PlaybackState]:
        """
        Retrieves authoritative playback state. If the current track's duration
        has naturally elapsed, automatically advances queue to the next song or sets idle.
        """
        playback = await PlaybackService.get_state(db, room_id)
        if not playback or playback.status != "playing" or not playback.current_queue_item:
            return playback

        track = playback.current_queue_item.track
        duration_ms = track.duration_ms if track else 0
        if duration_ms > 0:
            current_pos = PlaybackService.calculate_current_position(playback, duration_ms)
            if current_pos >= duration_ms:
                success, msg, next_pb = await PlaybackService.skip(db, room_id)
                if success and next_pb:
                    await db.commit()
                    return next_pb
        return playback

    @staticmethod
    async def pause(db: AsyncSession, room_id: uuid.UUID) -> Tuple[bool, str, Optional[PlaybackState]]:
        playback = await PlaybackService.get_state(db, room_id)
        if not playback or not playback.current_queue_item:
            return False, "No active playback to pause", None

        if playback.status == "paused":
            return True, "Already paused", playback

        track = playback.current_queue_item.track
        duration_ms = track.duration_ms if track else 0

        # Lock current position
        playback.position_ms = PlaybackService.calculate_current_position(playback, duration_ms)
        playback.status = "paused"
        playback.paused_at = utc_now()
        playback.started_at = None
        playback.version += 1

        room = await db.get(MusicRoom, room_id)
        if room:
            room.status = "paused"

        await db.flush()
        return True, "Playback paused", playback

    @staticmethod
    async def resume(db: AsyncSession, room_id: uuid.UUID) -> Tuple[bool, str, Optional[PlaybackState]]:
        playback = await PlaybackService.get_state(db, room_id)
        if not playback or not playback.current_queue_item:
            return False, "No active track to resume", None

        if playback.status == "playing":
            return True, "Already playing", playback

        playback.status = "playing"
        playback.started_at = utc_now()
        playback.paused_at = None
        playback.version += 1

        room = await db.get(MusicRoom, room_id)
        if room:
            room.status = "playing"

        await db.flush()
        return True, "Playback resumed", playback

    @staticmethod
    async def seek(db: AsyncSession, room_id: uuid.UUID, position_ms: int) -> Tuple[bool, str, Optional[PlaybackState]]:
        playback = await PlaybackService.get_state(db, room_id)
        if not playback or not playback.current_queue_item:
            return False, "No active track to seek", None

        track = playback.current_queue_item.track
        duration_ms = track.duration_ms if track else position_ms
        clamped_position = min(position_ms, duration_ms)

        playback.position_ms = clamped_position
        if playback.status == "playing":
            playback.started_at = utc_now()
        playback.version += 1

        await db.flush()
        return True, f"Seeked to {clamped_position}ms", playback

    @staticmethod
    async def skip(db: AsyncSession, room_id: uuid.UUID) -> Tuple[bool, str, Optional[PlaybackState]]:
        playback = await PlaybackService.get_state(db, room_id)
        if not playback or not playback.current_queue_item:
            return False, "No track to skip", None

        current_item = playback.current_queue_item
        room = await db.get(MusicRoom, room_id)

        # Check loop mode
        if playback.loop_mode == "track":
            # Restart same track
            playback.position_ms = 0
            playback.started_at = utc_now()
            playback.version += 1
            await db.flush()
            return True, "Track looped", playback

        current_item.status = "played"
        if playback.loop_mode == "queue":
            # Re-queue at the end
            max_pos_res = await db.execute(
                select(func.coalesce(func.max(QueueItem.position), 0)).where(
                    and_(QueueItem.room_id == room_id, QueueItem.status == "queued")
                )
            )
            next_pos = (max_pos_res.scalar() or 0) + 1
            re_item = QueueItem(
                room_id=room_id,
                track_id=current_item.track_id,
                requested_by_user_id=current_item.requested_by_user_id,
                position=next_pos,
                status="queued"
            )
            db.add(re_item)

        # Find next queued item
        next_res = await db.execute(
            select(QueueItem)
            .where(and_(QueueItem.room_id == room_id, QueueItem.status == "queued"))
            .order_by(QueueItem.position.asc())
            .limit(1)
        )
        next_item = next_res.scalar_one_or_none()

        if next_item:
            next_item.status = "current"
            next_item.position = 0
            playback.current_queue_item_id = next_item.id
            playback.status = "playing"
            playback.position_ms = 0
            playback.started_at = utc_now()
            playback.paused_at = None
            playback.version += 1
            if room:
                room.status = "playing"
                room.current_track_id = next_item.track_id
        else:
            playback.current_queue_item_id = None
            playback.status = "idle"
            playback.position_ms = 0
            playback.started_at = None
            playback.paused_at = None
            playback.version += 1
            if room:
                room.status = "idle"
                room.current_track_id = None

        await db.flush()
        # Refresh state for return
        return True, "Skipped to next track" if next_item else "Queue completed", await PlaybackService.get_state(db, room_id)

    @staticmethod
    async def set_loop(db: AsyncSession, room_id: uuid.UUID, mode: str) -> Tuple[bool, str, Optional[PlaybackState]]:
        playback = await PlaybackService.get_state(db, room_id)
        if not playback:
            return False, "Room playback state not found", None

        playback.loop_mode = mode
        playback.version += 1
        await db.flush()
        return True, f"Loop mode set to {mode}", playback

    @staticmethod
    async def stop(db: AsyncSession, room_id: uuid.UUID) -> Tuple[bool, str, Optional[PlaybackState]]:
        playback = await PlaybackService.get_state(db, room_id)
        if not playback:
            return False, "Room playback state not found", None

        playback.status = "stopped"
        playback.position_ms = 0
        playback.started_at = None
        playback.paused_at = None
        playback.version += 1

        room = await db.get(MusicRoom, room_id)
        if room:
            room.status = "idle"

        await db.flush()
        return True, "Playback stopped", playback


playback_service = PlaybackService()
