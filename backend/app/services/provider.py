import uuid
from typing import List, Optional
from app.schemas.domain import TrackResponse
from app.services.real_music import real_music_service


class MusicProviderService:
    """
    Music Provider that searches real music catalogues (YouTube / Spotify metadata)
    and extracts high-fidelity audio streams for synchronized in-app playback.
    """

    # Featured trending tracks shown before user searches
    FEATURED_TRENDING = [
        {
            "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
            "provider": "youtube",
            "provider_track_id": "60ItHLz5WEA",
            "title": "Faded",
            "artist": "Alan Walker",
            "album": "Different World",
            "duration_ms": 212000,
            "artwork_url": "https://i.ytimg.com/vi/60ItHLz5WEA/maxresdefault.jpg",
            "audio_url": None,
            "source_attribution": "Official Stream",
            "availability_status": "available",
        },
        {
            "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
            "provider": "youtube",
            "provider_track_id": "34Na4j8AVgA",
            "title": "Starboy",
            "artist": "The Weeknd ft. Daft Punk",
            "album": "Starboy",
            "duration_ms": 230000,
            "artwork_url": "https://i.ytimg.com/vi/34Na4j8AVgA/maxresdefault.jpg",
            "audio_url": None,
            "source_attribution": "Official Stream",
            "availability_status": "available",
        },
        {
            "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
            "provider": "youtube",
            "provider_track_id": "kJQP7kiw5Fk",
            "title": "Despacito",
            "artist": "Luis Fonsi ft. Daddy Yankee",
            "album": "VIDA",
            "duration_ms": 228000,
            "artwork_url": "https://i.ytimg.com/vi/kJQP7kiw5Fk/maxresdefault.jpg",
            "audio_url": None,
            "source_attribution": "Official Stream",
            "availability_status": "available",
        },
        {
            "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
            "provider": "youtube",
            "provider_track_id": "4NRXx6U8ABQ",
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "album": "After Hours",
            "duration_ms": 200000,
            "artwork_url": "https://i.ytimg.com/vi/4NRXx6U8ABQ/maxresdefault.jpg",
            "audio_url": None,
            "source_attribution": "Official Stream",
            "availability_status": "available",
        }
    ]

    async def search(self, query: str) -> List[TrackResponse]:
        if not query or not query.strip():
            return [TrackResponse(**t) for t in self.FEATURED_TRENDING]

        # Search real music tracks via real_music_service
        raw_results = await real_music_service.search(query, limit=6)
        if not raw_results:
            return [TrackResponse(**t) for t in self.FEATURED_TRENDING]

        tracks = []
        for r in raw_results:
            tracks.append(
                TrackResponse(
                    id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{r['provider']}:{r['provider_track_id']}"),
                    provider=r["provider"],
                    provider_track_id=r["provider_track_id"],
                    title=r["title"],
                    artist=r["artist"],
                    album=r.get("album"),
                    duration_ms=r.get("duration_ms", 180000),
                    artwork_url=r.get("artwork_url"),
                    audio_url=None,
                    source_attribution=r.get("source_attribution", "Real Music"),
                    availability_status="available"
                )
            )
        return tracks

    async def get_track(self, provider: str, provider_track_id: str) -> Optional[TrackResponse]:
        # Check featured trending first
        for t in self.FEATURED_TRENDING:
            if t["provider_track_id"] == provider_track_id:
                info = await real_music_service.get_audio_url(provider_track_id)
                audio_url = (info.get("audio_url") if info else None) or real_music_service.get_fallback_audio_url(provider_track_id)
                return TrackResponse(
                    id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{provider}:{provider_track_id}"),
                    provider=provider,
                    provider_track_id=provider_track_id,
                    title=t["title"],
                    artist=t["artist"],
                    album=t.get("album"),
                    duration_ms=t.get("duration_ms", 180000),
                    artwork_url=t.get("artwork_url"),
                    audio_url=audio_url,
                    source_attribution="BeatWave Authorized Stream",
                    availability_status="available"
                )

        # Extract direct or authorized fallback stream
        info = await real_music_service.get_audio_url(provider_track_id)
        if not info:
            info = {
                "audio_url": real_music_service.get_fallback_audio_url(provider_track_id),
                "title": f"Track {provider_track_id}",
                "artist": "BeatWave Artist",
                "duration_ms": 180000,
                "artwork_url": f"https://i.ytimg.com/vi/{provider_track_id}/hqdefault.jpg"
            }

        return TrackResponse(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{provider}:{provider_track_id}"),
            provider=provider,
            provider_track_id=provider_track_id,
            title=info.get("title", f"Track {provider_track_id}"),
            artist=info.get("artist", "BeatWave Artist"),
            album=info.get("album"),
            duration_ms=info.get("duration_ms", 180000),
            artwork_url=info.get("artwork_url") or f"https://i.ytimg.com/vi/{provider_track_id}/hqdefault.jpg",
            audio_url=info.get("audio_url") or real_music_service.get_fallback_audio_url(provider_track_id),
            source_attribution=info.get("source_attribution", "BeatWave Audio Stream"),
            availability_status="available"
        )


provider_service = MusicProviderService()
