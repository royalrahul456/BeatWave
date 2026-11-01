import uuid
from typing import Optional
from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.entities import User
from app.services.telegram_auth import telegram_auth_service


async def get_current_user(
    x_telegram_user_id: Optional[int] = Header(None, alias="X-Telegram-User-Id"),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Retrieves current user either from internal bot header or session token / telegram_user_id.
    """
    # 1. Direct Telegram User ID (used for internal bot requests or development)
    if x_telegram_user_id:
        result = await db.execute(select(User).where(User.telegram_user_id == x_telegram_user_id))
        user = result.scalar_one_or_none()
        if user:
            return user
        # Auto create if not found
        user = User(telegram_user_id=x_telegram_user_id, display_name=f"User {x_telegram_user_id}")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # 2. Bearer token (contains user id in format 'token_<telegram_user_id>')
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if token.startswith("token_"):
            try:
                tg_id = int(token.replace("token_", ""))
                result = await db.execute(select(User).where(User.telegram_user_id == tg_id))
                user = result.scalar_one_or_none()
                if user:
                    return user
            except ValueError:
                pass

    # Default fallback for demo / unauthenticated preview
    demo_tg_id = 999999999
    result = await db.execute(select(User).where(User.telegram_user_id == demo_tg_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_user_id=demo_tg_id, username="demouser", display_name="Demo Listener")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
