import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import (
    User,
    TelegramGroup,
    MusicRoom,
    RoomMember,
    RoomRole,
    GroupSettings,
    PlaybackState,
    utc_now,
)


class RoomService:
    @staticmethod
    async def get_or_create_user(
        db: AsyncSession,
        telegram_user_id: int,
        username: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> User:
        result = await db.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                display_name=display_name
            )
            db.add(user)
            await db.flush()
        else:
            if username and user.username != username:
                user.username = username
            if display_name and user.display_name != display_name:
                user.display_name = display_name
            await db.flush()
        return user

    @staticmethod
    async def get_or_create_group(
        db: AsyncSession,
        telegram_chat_id: int,
        title: Optional[str] = None,
        chat_type: str = "supergroup"
    ) -> TelegramGroup:
        result = await db.execute(select(TelegramGroup).where(TelegramGroup.telegram_chat_id == telegram_chat_id))
        group = result.scalar_one_or_none()
        if not group:
            group = TelegramGroup(
                telegram_chat_id=telegram_chat_id,
                title=title,
                chat_type=chat_type
            )
            db.add(group)
            await db.flush()

            # Create default settings
            settings = GroupSettings(group_id=group.id)
            db.add(settings)
            await db.flush()
        else:
            if title and group.title != title:
                group.title = title
            await db.flush()
        return group

    @staticmethod
    async def get_or_create_room(
        db: AsyncSession,
        group_id: uuid.UUID,
        created_by_user_id: Optional[uuid.UUID] = None
    ) -> MusicRoom:
        result = await db.execute(
            select(MusicRoom)
            .where(
                and_(
                    MusicRoom.group_id == group_id,
                    MusicRoom.status.in_(["created", "playing", "paused", "idle"])
                )
            )
        )
        room = result.scalar_one_or_none()
        if not room:
            room = MusicRoom(
                group_id=group_id,
                created_by_user_id=created_by_user_id,
                status="idle"
            )
            db.add(room)
            await db.flush()

            # Initialize playback state
            playback = PlaybackState(
                room_id=room.id,
                status="idle",
                position_ms=0,
                version=1
            )
            db.add(playback)
            await db.flush()

        return room

    @staticmethod
    async def update_member_presence(
        db: AsyncSession,
        room_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> RoomMember:
        result = await db.execute(
            select(RoomMember).where(
                and_(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
            )
        )
        member = result.scalar_one_or_none()
        now = utc_now()
        if not member:
            member = RoomMember(
                room_id=room_id,
                user_id=user_id,
                last_seen_at=now,
                joined_at=now
            )
            db.add(member)
        else:
            member.last_seen_at = now
            member.left_at = None
        await db.flush()
        return member

    @staticmethod
    async def get_dj(db: AsyncSession, room_id: uuid.UUID) -> Optional[User]:
        result = await db.execute(
            select(User)
            .join(RoomRole, RoomRole.user_id == User.id)
            .where(and_(RoomRole.room_id == room_id, RoomRole.role == "dj"))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def set_dj(
        db: AsyncSession,
        room_id: uuid.UUID,
        user_id: uuid.UUID,
        assigned_by_user_id: Optional[uuid.UUID] = None
    ) -> RoomRole:
        # Clear existing DJ
        result = await db.execute(
            select(RoomRole).where(and_(RoomRole.room_id == room_id, RoomRole.role == "dj"))
        )
        existing = result.scalars().all()
        for role in existing:
            await db.delete(role)

        new_role = RoomRole(
            room_id=room_id,
            user_id=user_id,
            role="dj",
            assigned_by_user_id=assigned_by_user_id
        )
        db.add(new_role)
        await db.flush()
        return new_role

    @staticmethod
    async def is_dj_or_admin(
        db: AsyncSession,
        room_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        # Check explicit DJ role
        dj = await RoomService.get_dj(db, room_id)
        if dj and dj.id == user_id:
            return True

        # If no DJ is assigned, any member in the room can control playback until a DJ is appointed
        if not dj:
            return True

        return False


room_service = RoomService()
