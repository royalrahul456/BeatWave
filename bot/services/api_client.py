import os
from typing import Optional, Dict, Any, List, Tuple
import httpx
from bot.config import bot_settings


class BackendAPIClient:
    def __init__(self, base_url: Optional[str] = None):
        self._base_url = base_url

    @property
    def candidate_base_urls(self) -> List[str]:
        port = os.getenv("PORT", "8000")
        urls = []
        if self._base_url:
            urls.append(self._base_url.rstrip("/"))
        if os.getenv("API_BASE_URL"):
            urls.append(os.getenv("API_BASE_URL").rstrip("/"))
        urls.append(f"http://127.0.0.1:{port}/api/v1")
        urls.append(f"http://localhost:{port}/api/v1")
        if os.getenv("RENDER_EXTERNAL_URL"):
            urls.append(f"{os.getenv('RENDER_EXTERNAL_URL').rstrip('/')}/api/v1")
        if bot_settings.MINI_APP_URL and "localhost" not in bot_settings.MINI_APP_URL:
            urls.append(f"{bot_settings.MINI_APP_URL.rstrip('/')}/api/v1")

        seen = set()
        res = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                res.append(u)
        return res

    def _headers(self, telegram_user_id: int) -> Dict[str, str]:
        return {
            "X-Telegram-User-Id": str(telegram_user_id),
            "Content-Type": "application/json"
        }

    async def _request(self, method: str, path: str, **kwargs) -> Optional[httpx.Response]:
        last_error = None
        # Try active cached base URL first to avoid candidate latency
        candidates = [self._base_url] + [u for u in self.candidate_base_urls if u != self._base_url] if self._base_url else self.candidate_base_urls
        for base in candidates:
            url = f"{base}/{path.lstrip('/')}"
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.request(method, url, timeout=25.0, **kwargs)
                    if res.status_code in (200, 201):
                        self._base_url = base  # Cache successful endpoint
                        return res
                    else:
                        print(f"[APIClient] {method} {url} returned HTTP {res.status_code}: {res.text[:120]}")
                        last_error = f"HTTP {res.status_code}"
            except Exception as e:
                last_error = e
                continue
        print(f"[APIClient] All candidate connections failed for {method} /{path.lstrip('/')}: {last_error}")
        return None

    async def get_or_create_room(self, chat_id: int, user_id: int, title: Optional[str] = None) -> Optional[Dict[str, Any]]:
        res = await self._request(
            "POST",
            f"rooms/group/{chat_id}",
            params={"title": title or f"Group {chat_id}"},
            headers=self._headers(user_id)
        )
        if res and res.status_code == 200:
            return res.json()
        return None

    async def get_room(self, room_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        res = await self._request("GET", f"rooms/{room_id}", headers=self._headers(user_id))
        if res and res.status_code == 200:
            return res.json()
        return None

    async def get_playback_state(self, room_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        res = await self._request("GET", f"rooms/{room_id}/state", headers=self._headers(user_id))
        if res and res.status_code == 200:
            return res.json()
        return None

    async def search_tracks(self, room_id: str, user_id: int, query: str) -> List[Dict[str, Any]]:
        res = await self._request(
            "POST",
            f"rooms/{room_id}/search",
            json={"query": query},
            headers=self._headers(user_id)
        )
        if res and res.status_code == 200:
            return res.json().get("results", [])
        return []

    async def add_track_request(
        self,
        room_id: str,
        user_id: int,
        provider: str,
        provider_track_id: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        res = await self._request(
            "POST",
            f"rooms/{room_id}/requests",
            json={"provider": provider, "provider_track_id": provider_track_id},
            headers=self._headers(user_id)
        )
        if res and res.status_code == 200:
            return True, "Added to queue", res.json()
        if res:
            try:
                data = res.json()
                return False, data.get("detail", "Failed to add track"), None
            except Exception:
                return False, res.text, None
        return False, "Could not reach music server", None

    async def get_queue(self, room_id: str, user_id: int) -> List[Dict[str, Any]]:
        res = await self._request("GET", f"rooms/{room_id}/queue", headers=self._headers(user_id))
        if res and res.status_code == 200:
            return res.json()
        return []

    async def control_playback(self, room_id: str, user_id: int, action: str, payload: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        res = await self._request(
            "POST",
            f"rooms/{room_id}/controls/{action}",
            json=payload if payload else None,
            headers=self._headers(user_id)
        )
        if res and res.status_code == 200:
            return True, f"Command {action} successful"
        if res:
            try:
                data = res.json()
                return False, data.get("detail", f"Action {action} failed")
            except Exception:
                return False, res.text
        return False, "Could not reach music server"


api_client = BackendAPIClient()
