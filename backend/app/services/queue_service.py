import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, and_, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    MusicRoom,
    Track,
    QueueItem,
    PlaybackState,
    GroupSettings,
    utc_now,
)
from app.services.provider import provider_service


class QueueService:
    @staticmethod
    async def get_or_create_track(
        db: AsyncSession,
        provider: str,
        provider_track_id: str
    ) -> Optional[Track]:
        result = await db.execute(
            select(Track).where(
                and_(Track.provider == provider, Track.provider_track_id == provider_track_id)
            )
        )
        track = result.scalar_one_or_none()
        if track:
            if not track.audio_url:
                provider_meta = await provider_service.get_track(provider, provider_track_id)
                if provider_meta and provider_meta.audio_url:
                    track.audio_url = provider_meta.audio_url
                    await db.flush()
            return track

        # Fetch from provider
        provider_meta = await provider_service.get_track(provider, provider_track_id)
        if not provider_meta:
            return None

        track = Track(
            provider=provider,
            provider_track_id=provider_track_id,
            title=provider_meta.title,
            artist=provider_meta.artist,
            album=provider_meta.album,
            duration_ms=provider_meta.duration_ms,
            artwork_url=provider_meta.artwork_url,
            audio_url=provider_meta.audio_url,
            source_attribution=provider_meta.source_attribution,
            availability_status=provider_meta.availability_status
        )
        db.add(track)
        await db.flush()
        return track

    @staticmethod
    async def add_track_request(
        db: AsyncSession,
        room_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
        provider_track_id: str,
        play_now: bool = True
    ) -> Tuple[bool, str, Optional[QueueItem]]:
        room = await db.get(MusicRoom, room_id)
        if not room or room.status == "ended":
            return False, "Room is not active", None

        # Check group settings
        settings_res = await db.execute(
            select(GroupSettings).where(GroupSettings.group_id == room.group_id)
        )
        group_settings = settings_res.scalar_one_or_none()
        if group_settings and not group_settings.requests_enabled:
            return False, "Song requests are disabled for this group", None

        # Check rate limits (e.g. max requests per window)
        window_seconds = 300
        max_requests = 30
        if group_settings:
            max_requests = max(group_settings.max_requests_per_user_window, 30)

        window_start = utc_now() - timedelta(seconds=window_seconds)
        count_res = await db.execute(
            select(func.count(QueueItem.id)).where(
                and_(
                    QueueItem.room_id == room_id,
                    QueueItem.requested_by_user_id == user_id,
                    QueueItem.created_at >= window_start
                )
            )
        )
        user_requests_count = count_res.scalar() or 0
        if user_requests_count >= max_requests:
            return False, f"Rate limit reached: maximum {max_requests} requests per 5 minutes.", None

        # Get or create track
        track = await QueueService.get_or_create_track(db, provider, provider_track_id)
        if not track:
            return False, "Track not found in authorized provider", None

        # Duplicate check in upcoming queue (skip if user wants to play now)
        duplicate_policy = group_settings.duplicate_policy if group_settings else "allow"
        if duplicate_policy == "reject" and not play_now:
            dup_res = await db.execute(
                select(QueueItem).where(
                    and_(
                        QueueItem.room_id == room_id,
                        QueueItem.track_id == track.id,
                        QueueItem.status.in_(["queued", "current"])
                    )
                )
            )
            if dup_res.scalar_one_or_none():
                return False, "Track is already in the queue or currently playing", None

        # Determine next position
        max_pos_res = await db.execute(
            select(func.coalesce(func.max(QueueItem.position), 0)).where(
                and_(QueueItem.room_id == room_id, QueueItem.status == "queued")
            )
        )
        next_pos = (max_pos_res.scalar() or 0) + 1

        queue_item = QueueItem(
            room_id=room_id,
            track_id=track.id,
            requested_by_user_id=user_id,
            position=next_pos,
            status="queued"
        )
        db.add(queue_item)
        await db.flush()

        # Check if playback state should promote this track to play immediately
        pb_res = await db.execute(
            select(PlaybackState).where(PlaybackState.room_id == room_id)
        )
        playback = pb_res.scalar_one_or_none()
        is_idle = playback is None or playback.status in ["idle", "stopped"] or not playback.current_queue_item_id
        if is_idle or play_now:
            if playback and playback.current_queue_item_id:
                prev_item = await db.get(QueueItem, playback.current_queue_item_id)
                if prev_item:
                    prev_item.status = "played"
            queue_item.status = "current"
            queue_item.position = 0
            if playback:
                playback.current_queue_item_id = queue_item.id
                playback.status = "playing"
                playback.position_ms = 0
                playback.started_at = utc_now()
                playback.paused_at = None
                playback.version += 1
            room.status = "playing"
            room.current_track_id = track.id
            await db.flush()
            msg = "Playing now!"
        else:
            msg = f"Added #{queue_item.position} in upcoming queue"

        return True, msg, queue_item

    @staticmethod
    async def get_queue(
        db: AsyncSession,
        room_id: uuid.UUID
    ) -> List[QueueItem]:
        result = await db.execute(
            select(QueueItem)
            .where(and_(QueueItem.room_id == room_id, QueueItem.status.in_(["current", "queued"])))
            .options(selectinload(QueueItem.track), selectinload(QueueItem.requested_by))
            .order_by(QueueItem.status.desc(), QueueItem.position.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def remove_queue_item(
        db: AsyncSession,
        room_id: uuid.UUID,
        item_id: uuid.UUID
    ) -> bool:
        item = await db.get(QueueItem, item_id)
        if not item or item.room_id != room_id:
            return False

        item.status = "removed"
        await db.flush()

        # Re-index remaining queued items
        remaining_res = await db.execute(
            select(QueueItem)
            .where(and_(QueueItem.room_id == room_id, QueueItem.status == "queued"))
            .order_by(QueueItem.position.asc())
        )
        remaining = remaining_res.scalars().all()
        for idx, it in enumerate(remaining, start=1):
            it.position = idx
        await db.flush()
        return True

    @staticmethod
    async def clear_queue(
        db: AsyncSession,
        room_id: uuid.UUID
    ) -> int:
        result = await db.execute(
            update(QueueItem)
            .where(and_(QueueItem.room_id == room_id, QueueItem.status == "queued"))
            .values(status="removed")
        )
        await db.flush()
        return result.rowcount


queue_service = QueueService()
