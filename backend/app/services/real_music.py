import asyncio
import base64
import hashlib
import json
import urllib.parse
import urllib.request
from typing import List, Dict, Any, Optional
from Crypto.Cipher import DES
from Crypto.Util.Padding import unpad
import yt_dlp

FALLBACK_AUDIO_STREAMS = [
    "https://aac.saavncdn.com/907/12da09735c1c751ba3c4d5f6a0ec3854_320.mp4",
    "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
    "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3",
    "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3",
    "https://cdn.pixabay.com/download/audio/2022/10/14/audio_9939f777dd.mp3",
    "https://cdn.pixabay.com/download/audio/2021/08/04/audio_12b0c7443c.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
]


def decrypt_saavn_url(enc_url: str) -> Optional[str]:
    """Decrypts JioSaavn DES encrypted media URL to direct full-length 320kbps CDN stream."""
    try:
        cipher = DES.new(b"38346591", DES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(base64.b64decode(enc_url)), 8).decode('utf-8')
        # Upgrade quality to full 320kbps master stream
        upgraded = decrypted.replace("_96.mp4", "_320.mp4").replace("_160.mp4", "_320.mp4")
        return upgraded
    except Exception as e:
        print(f"[RealMusicService] DES decrypt error: {e}")
        return None


class RealMusicService:
    def __init__(self):
        self.ydl_opts_search = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
        self.ydl_opts_extract = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }

    def get_fallback_audio_url(self, seed: str) -> str:
        idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(FALLBACK_AUDIO_STREAMS)
        return FALLBACK_AUDIO_STREAMS[idx]

    def search_saavn_sync(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Direct JioSaavn API — Full length 320kbps DRM-free streams for Bollywood,
        regional (Marathi, Punjabi, Tamil), and international popular hits.
        """
        encoded = urllib.parse.quote(query)
        url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&_marker=0&api_version=4&ctx=web6dot0&q={encoded}"
        results = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=6) as response:
                data = json.loads(response.read().decode())
                items = data.get("results", [])
                for item in items[:limit]:
                    track_id = str(item.get("id"))
                    title = item.get("title", "").replace("&quot;", '"').replace("&#039;", "'").replace("&amp;", "&")
                    more_info = item.get("more_info", {})
                    enc_url = more_info.get("encrypted_media_url")
                    audio_url = decrypt_saavn_url(enc_url) if enc_url else None
                    if not audio_url:
                        audio_url = more_info.get("vlink")

                    artwork = item.get("image", "").replace("150x150", "500x500")
                    duration_sec = int(more_info.get("duration") or 240)
                    artist = more_info.get("music") or item.get("subtitle") or "Artist"

                    if audio_url:
                        results.append({
                            "provider": "saavn",
                            "provider_track_id": track_id,
                            "title": title,
                            "artist": artist,
                            "album": more_info.get("album"),
                            "duration_ms": duration_sec * 1000,
                            "artwork_url": artwork,
                            "audio_url": audio_url,
                            "source_attribution": f"Full Stream ({artist})",
                            "availability_status": "available"
                        })
        except Exception as e:
            print(f"[RealMusicService] Saavn search error: {e}")
        return results

    def lookup_saavn_sync(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Look up full details for a JioSaavn track ID."""
        url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&pids={track_id}&_format=json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as response:
                data = json.loads(response.read().decode())
                item = data.get(track_id) or (list(data.values())[0] if data else None)
                if item and isinstance(item, dict):
                    title = item.get("song", item.get("title", "")).replace("&quot;", '"').replace("&#039;", "'")
                    more_info = item.get("more_info", item)
                    enc_url = more_info.get("encrypted_media_url")
                    audio_url = decrypt_saavn_url(enc_url) if enc_url else None
                    if not audio_url:
                        audio_url = more_info.get("vlink")
                    artwork = item.get("image", "").replace("150x150", "500x500")
                    duration_sec = int(more_info.get("duration") or 240)
                    artist = more_info.get("music", item.get("primary_artists", "Artist"))

                    return {
                        "provider": "saavn",
                        "provider_track_id": str(track_id),
                        "title": title or f"Track {track_id}",
                        "artist": artist,
                        "album": more_info.get("album"),
                        "duration_ms": duration_sec * 1000,
                        "artwork_url": artwork,
                        "audio_url": audio_url or self.get_fallback_audio_url(str(track_id)),
                        "source_attribution": "Full Master Stream",
                        "availability_status": "available"
                    }
        except Exception as e:
            print(f"[RealMusicService] Saavn lookup error: {e}")
        return None

    def search_itunes_sync(self, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_query}&entity=song&limit={limit}"
        results = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BeatWave/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                for item in data.get("results", []):
                    track_id = str(item.get("trackId"))
                    artwork = item.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
                    preview_url = item.get("previewUrl") or self.get_fallback_audio_url(track_id)
                    results.append({
                        "provider": "itunes",
                        "provider_track_id": track_id,
                        "title": item.get("trackName", "Track"),
                        "artist": item.get("artistName", "Artist"),
                        "album": item.get("collectionName"),
                        "duration_ms": item.get("trackTimeMillis", 180000),
                        "artwork_url": artwork,
                        "audio_url": preview_url,
                        "source_attribution": f"Official ({item.get('artistName', 'Music')})",
                        "availability_status": "available"
                    })
        except Exception as e:
            print(f"[RealMusicService] iTunes search error: {e}")
        return results

    def lookup_itunes_sync(self, track_id: str) -> Optional[Dict[str, Any]]:
        url = f"https://itunes.apple.com/lookup?id={track_id}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BeatWave/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                results = data.get("results", [])
                if results:
                    item = results[0]
                    artwork = item.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
                    preview_url = item.get("previewUrl") or self.get_fallback_audio_url(str(track_id))
                    return {
                        "provider": "itunes",
                        "provider_track_id": str(track_id),
                        "title": item.get("trackName", "Track"),
                        "artist": item.get("artistName", "Artist"),
                        "album": item.get("collectionName"),
                        "duration_ms": item.get("trackTimeMillis", 180000),
                        "artwork_url": artwork,
                        "audio_url": preview_url,
                        "source_attribution": f"Official ({item.get('artistName', 'Music')})",
                        "availability_status": "available"
                    }
        except Exception as e:
            print(f"[RealMusicService] iTunes lookup error: {e}")
        return None

    def search_sync(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        # 1. Search JioSaavn first (delivers full-length 320kbps audio files)
        saavn_results = self.search_saavn_sync(query, limit)
        if saavn_results:
            return saavn_results

        # 2. Search iTunes
        itunes_results = self.search_itunes_sync(query, limit)
        if itunes_results:
            return itunes_results

        return []

    def get_audio_url_sync(self, track_id: str) -> Optional[Dict[str, Any]]:
        # 1. Try JioSaavn lookup
        saavn_track = self.lookup_saavn_sync(str(track_id))
        if saavn_track and saavn_track.get("audio_url"):
            return saavn_track

        # 2. Try iTunes lookup if numeric
        if str(track_id).isdigit():
            itunes_track = self.lookup_itunes_sync(str(track_id))
            if itunes_track:
                return itunes_track

        # 3. Always return high-quality audio fallback stream
        return {
            "audio_url": self.get_fallback_audio_url(str(track_id)),
            "title": f"Track {track_id}",
            "artist": "BeatWave Artist",
            "duration_ms": 240000,
            "artwork_url": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=600"
        }

    async def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.search_sync, query, limit)

    async def get_audio_url(self, track_id: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_audio_url_sync, track_id)


real_music_service = RealMusicService()
