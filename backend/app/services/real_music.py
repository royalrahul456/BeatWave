import asyncio
import yt_dlp
from typing import List, Dict, Any, Optional


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

    def search_sync(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        search_query = f"ytsearch{limit}:{query}"
        results = []
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_search) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        if not entry:
                            continue
                        duration = entry.get('duration') or 180
                        thumbnails = entry.get('thumbnails') or []
                        thumb_url = thumbnails[-1].get('url') if thumbnails else f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg"
                        
                        results.append({
                            "provider": "youtube",
                            "provider_track_id": entry.get('id'),
                            "title": entry.get('title'),
                            "artist": entry.get('uploader') or entry.get('channel') or "Artist",
                            "duration_ms": int(duration * 1000),
                            "artwork_url": thumb_url,
                            "source_attribution": f"YouTube ({entry.get('uploader') or 'Music'})",
                            "availability_status": "available"
                        })
        except Exception as e:
            print(f"[RealMusicService] Search error: {e}")
        return results

    def get_audio_url_sync(self, video_id: str) -> Optional[Dict[str, Any]]:
        url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_extract) as ydl:
                info = ydl.extract_info(url, download=False)
                # Find best audio url
                audio_url = None
                formats = info.get('formats', [])
                # Filter for audio formats
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                if audio_formats:
                    # Pick highest bitrate
                    best = max(audio_formats, key=lambda f: f.get('abr') or 0)
                    audio_url = best.get('url')
                if not audio_url:
                    audio_url = info.get('url')

                thumbnails = info.get('thumbnails') or []
                thumb_url = thumbnails[-1].get('url') if thumbnails else f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

                return {
                    "audio_url": audio_url,
                    "title": info.get('title'),
                    "artist": info.get('uploader') or "Artist",
                    "duration_ms": int((info.get('duration') or 180) * 1000),
                    "artwork_url": thumb_url
                }
        except Exception as e:
            print(f"[RealMusicService] Extract error: {e}")
            return None

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.search_sync, query, limit)

    async def get_audio_url(self, video_id: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_audio_url_sync, video_id)


real_music_service = RealMusicService()
