import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.db.session import engine, Base
from app.models.entities import *
from app.services.provider import provider_service
from app.services.telegram_auth import telegram_auth_service
from app.services.room_service import room_service
from app.services.queue_service import queue_service
from app.services.playback_service import playback_service


async def main():
    print("Testing BeatWave backend logic...")
    # 0. Clean old tables if any
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Tables created successfully")

    # 2. Test Telegram Auth
    import time
    now_ts = int(time.time())
    valid, udata = telegram_auth_service.validate_init_data(f"auth_date={now_ts}&hash=mock&user=%7B%22id%22%3A101%2C%22first_name%22%3A%22Alex%22%7D")
    assert valid is True
    assert udata["id"] == 101
    print("[OK] Telegram Auth service validated")

    # 3. Test Room & User creation
    from app.db.session import async_session_maker
    async with async_session_maker() as session:
        user = await room_service.get_or_create_user(session, 101, username="alex", display_name="Alex DJ")
        group = await room_service.get_or_create_group(session, -100999888, title="BeatWave Lounge")
        room = await room_service.get_or_create_room(session, group.id, created_by_user_id=user.id)
        await session.commit()
        room_id = room.id
        user_id = user.id
    print(f"[OK] Room and user created: room_id={room_id}")

    # 4. Test Queue and Provider Search
    results = await provider_service.search("Cyan")
    assert len(results) > 0
    t = results[0]
    print(f"[OK] Provider search returned {len(results)} tracks (first: {t.title})")

    async with async_session_maker() as session:
        ok, msg, qitem = await queue_service.add_track_request(session, room_id, user_id, t.provider, t.provider_track_id)
        assert ok is True
        assert qitem is not None
        await session.commit()
    print("[OK] Track requested and queued")

    # 5. Test Playback State (Pause / Resume / Seek / Skip)
    async with async_session_maker() as session:
        pb = await playback_service.get_state(session, room_id)
        assert pb.status == "playing"
        print(f"[OK] Playback auto-started on initial queue: status={pb.status}, version={pb.version}")

        # Pause
        ok, msg, pb = await playback_service.pause(session, room_id)
        assert pb.status == "paused"
        print(f"[OK] Pause action succeeded: version={pb.version}")

        # Resume
        ok, msg, pb = await playback_service.resume(session, room_id)
        assert pb.status == "playing"
        print(f"[OK] Resume action succeeded: version={pb.version}")

        # Seek
        ok, msg, pb = await playback_service.seek(session, room_id, 30000)
        assert pb.position_ms == 30000
        print(f"[OK] Seek action succeeded: position={pb.position_ms}ms, version={pb.version}")

        # Skip
        ok, msg, pb = await playback_service.skip(session, room_id)
        print(f"[OK] Skip action succeeded: version={pb.version}")

        await session.commit()

    print("\n=== ALL BEATWAVE BACKEND TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    asyncio.run(main())
