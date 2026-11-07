import re
import urllib.parse
from typing import Dict, Any, List, Optional
import httpx


def parse_lrc_lines(lrc_text: str) -> List[Dict[str, Any]]:
    """
    Parses LRC format:
    [00:12.34] Some lyrics text
    into a list of:
    {'time_ms': 12340, 'text': 'Some lyrics text'}
    """
    lines = []
    time_regex = re.compile(r'\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]')
    
    for line in lrc_text.splitlines():
        line = line.strip()
        if not line:
            continue
        matches = list(time_regex.finditer(line))
        if not matches:
            continue
        
        # Clean line text by stripping all timestamp brackets
        clean_text = time_regex.sub('', line).strip()
        for match in matches:
            mins = int(match.group(1))
            secs = int(match.group(2))
            millis_str = match.group(3) or '0'
            if len(millis_str) == 1:
                millis = int(millis_str) * 100
            elif len(millis_str) == 2:
                millis = int(millis_str) * 10
            else:
                millis = int(millis_str[:3])
            time_ms = (mins * 60 + secs) * 1000 + millis
            lines.append({"time_ms": time_ms, "text": clean_text})
            
    lines.sort(key=lambda x: x["time_ms"])
    return lines


def pick_best_lyrics_match(candidates: List[Dict[str, Any]], target_artist: str, target_duration_sec: int) -> Optional[Dict[str, Any]]:
    """
    Duration-proximity and artist scoring guard to ensure exact studio track sync.
    """
    if not candidates:
        return None

    artists = [a.strip().lower() for a in re.split(r'[,/&|]', target_artist) if a.strip()]
    scored = []

    for item in candidates:
        score = 0
        cand_artist = (item.get("artistName") or "").lower()

        # 1. Artist matching bonus
        for a in artists:
            if a in cand_artist or cand_artist in a:
                score += 50
                break

        # 2. Duration proximity guard
        cand_dur = int(item.get("duration") or 0)
        if target_duration_sec > 0 and cand_dur > 0:
            diff = abs(target_duration_sec - cand_dur)
            if diff <= 8:
                score += 50
            elif diff <= 15:
                score += 35
            elif diff <= 30:
                score += 10
            elif diff > 45:
                score -= 40
        elif cand_dur == 0:
            score += 5

        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored and scored[0][0] >= 0:
        return scored[0][1]
    return candidates[0] if candidates else None


class LyricsService:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get_lyrics(self, title: str, artist: str = "", duration_ms: int = 0) -> Dict[str, Any]:
        cache_key = f"{title.lower().strip()}_{artist.lower().strip()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        clean_title = re.sub(r'\(.*?\)|\[.*?\]', '', title).strip()
        first_artist = re.split(r'[,/&|]', artist)[0].strip() if artist else ""
        target_dur_sec = duration_ms // 1000 if duration_ms > 0 else 0

        # 1. Try LRCLIB exact match lookup
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                query_params = {
                    "track_name": clean_title,
                    "artist_name": first_artist or artist
                }
                if target_dur_sec > 0:
                    query_params["duration"] = str(target_dur_sec)
                
                resp = await client.get("https://lrclib.net/api/get", params=query_params, headers={"User-Agent": "BeatWave/1.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    synced_raw = data.get("syncedLyrics")
                    plain_raw = data.get("plainLyrics")
                    if synced_raw:
                        result = {
                            "found": True,
                            "synced": True,
                            "lines": parse_lrc_lines(synced_raw),
                            "plain": plain_raw or "",
                            "track_name": data.get("trackName", clean_title),
                            "artist_name": data.get("artistName", artist)
                        }
                        self._cache[cache_key] = result
                        return result
                    elif plain_raw:
                        result = {
                            "found": True,
                            "synced": False,
                            "lines": [{"time_ms": idx * 3000, "text": l} for idx, l in enumerate(plain_raw.splitlines()) if l.strip()],
                            "plain": plain_raw,
                            "track_name": data.get("trackName", clean_title),
                            "artist_name": data.get("artistName", artist)
                        }
                        self._cache[cache_key] = result
                        return result
        except Exception:
            pass

        # 2. Try LRCLIB fuzzy search with duration-proximity filter
        try:
            search_query = f"{clean_title} {first_artist}".strip()
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"https://lrclib.net/api/search?q={urllib.parse.quote(search_query)}",
                    headers={"User-Agent": "BeatWave/1.0"}
                )
                if resp.status_code == 200:
                    items = resp.json()
                    if isinstance(items, list) and items:
                        best = pick_best_lyrics_match(items, artist, target_dur_sec)
                        if best:
                            synced_raw = best.get("syncedLyrics")
                            plain_raw = best.get("plainLyrics")
                            if synced_raw:
                                result = {
                                    "found": True,
                                    "synced": True,
                                    "lines": parse_lrc_lines(synced_raw),
                                    "plain": plain_raw or "",
                                    "track_name": best.get("trackName", clean_title),
                                    "artist_name": best.get("artistName", artist)
                                }
                                self._cache[cache_key] = result
                                return result
                            elif plain_raw:
                                result = {
                                    "found": True,
                                    "synced": False,
                                    "lines": [{"time_ms": idx * 3000, "text": l} for idx, l in enumerate(plain_raw.splitlines()) if l.strip()],
                                    "plain": plain_raw,
                                    "track_name": best.get("trackName", clean_title),
                                    "artist_name": best.get("artistName", artist)
                                }
                                self._cache[cache_key] = result
                                return result
        except Exception:
            pass

        # 3. JioSaavn Lyrics API Fallback
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                search_url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&q={urllib.parse.quote(clean_title)}&p=1&n=5"
                s_resp = await client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
                if s_resp.status_code == 200:
                    data = s_resp.json()
                    for item in data.get("results", []):
                        if str(item.get("has_lyrics")).lower() == "true":
                            lyr_id = item.get("id")
                            lyr_url = f"https://www.jiosaavn.com/api.php?__call=lyrics.getLyrics&lyrics_id={lyr_id}&_format=json"
                            l_resp = await client.get(lyr_url, headers={"User-Agent": "Mozilla/5.0"})
                            if l_resp.status_code == 200:
                                lyr_data = l_resp.json()
                                plain_txt = lyr_data.get("lyrics", "")
                                if plain_txt:
                                    clean_txt = plain_txt.replace("<br />", "\n").replace("<br>", "\n").replace("&quot;", '"')
                                    result = {
                                        "found": True,
                                        "synced": False,
                                        "lines": [{"time_ms": idx * 3000, "text": l} for idx, l in enumerate(clean_txt.splitlines()) if l.strip()],
                                        "plain": clean_txt,
                                        "track_name": clean_title,
                                        "artist_name": artist
                                    }
                                    self._cache[cache_key] = result
                                    return result
        except Exception:
            pass

        # Graceful placeholder
        return {
            "found": False,
            "synced": False,
            "lines": [],
            "plain": f"Lyrics currently unavailable for \"{clean_title}\".\nEnjoy the high-fidelity 320kbps CD stream.",
            "track_name": clean_title,
            "artist_name": artist
        }


lyrics_service = LyricsService()
