"""Helper para extraer metadata y transcripción de YouTube."""
import asyncio
from typing import Optional


def get_youtube_metadata(url: str) -> dict:
    """Extrae metadata pública de YouTube usando yt-dlp."""
    try:
        import yt_dlp
    except ImportError:
        return {"error": "yt-dlp no instalado"}

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "view_count": info.get("view_count"),
            "upload_date": info.get("upload_date"),
            "description": (info.get("description") or "")[:1000],
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def get_youtube_transcript(video_id: str, languages: list[str] = None) -> Optional[str]:
    """Intenta obtener transcripción automática de YouTube."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    languages = languages or ["es", "en"]
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return " ".join([t["text"] for t in transcript])
    except Exception:
        return None


async def async_get_youtube_metadata(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_youtube_metadata, url)
