from typing import Optional, Dict, Any, List, Tuple
import httpx
from bot.config import bot_settings


class BackendAPIClient:
    def __init__(self, base_url: str = bot_settings.API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _headers(self, telegram_user_id: int) -> Dict[str, str]:
        return {
            "X-Telegram-User-Id": str(telegram_user_id),
            "Content-Type": "application/json"
        }

    async def get_or_create_room(self, chat_id: int, user_id: int, title: Optional[str] = None) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    f"{self.base_url}/rooms/group/{chat_id}",
                    params={"title": title or f"Group {chat_id}"},
                    headers=self._headers(user_id),
                    timeout=10.0
                )
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                print(f"[APIClient] Error getting room: {e}")
        return None

    async def get_room(self, room_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(
                    f"{self.base_url}/rooms/{room_id}",
                    headers=self._headers(user_id),
                    timeout=10.0
                )
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                print(f"[APIClient] Error getting room info: {e}")
        return None

    async def get_playback_state(self, room_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(
                    f"{self.base_url}/rooms/{room_id}/state",
                    headers=self._headers(user_id),
                    timeout=10.0
                )
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                print(f"[APIClient] Error getting playback state: {e}")
        return None

    async def search_tracks(self, room_id: str, user_id: int, query: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    f"{self.base_url}/rooms/{room_id}/search",
                    json={"query": query},
                    headers=self._headers(user_id),
                    timeout=10.0
                )
                if res.status_code == 200:
                    return res.json().get("results", [])
            except Exception as e:
                print(f"[APIClient] Error searching tracks: {e}")
        return []

    async def add_track_request(
        self,
        room_id: str,
        user_id: int,
        provider: str,
        provider_track_id: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    f"{self.base_url}/rooms/{room_id}/requests",
                    json={"provider": provider, "provider_track_id": provider_track_id},
                    headers=self._headers(user_id),
                    timeout=10.0
                )
                if res.status_code == 200:
                    return True, "Added to queue", res.json()
                data = res.json()
                return False, data.get("detail", "Failed to add track"), None
            except Exception as e:
                return False, str(e), None

    async def get_queue(self, room_id: str, user_id: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(
                    f"{self.base_url}/rooms/{room_id}/queue",
                    headers=self._headers(user_id),
                    timeout=10.0
                )
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                print(f"[APIClient] Error getting queue: {e}")
        return []

    async def control_playback(self, room_id: str, user_id: int, action: str, payload: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    f"{self.base_url}/rooms/{room_id}/controls/{action}",
                    json=payload if payload else None,
                    headers=self._headers(user_id),
                    timeout=10.0
                )
                if res.status_code == 200:
                    return True, f"Command {action} successful"
                data = res.json()
                return False, data.get("detail", f"Action {action} failed")
            except Exception as e:
                return False, str(e)


api_client = BackendAPIClient()
