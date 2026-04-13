import re

from langchain_core.tools import tool

_VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|embed/|shorts/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})",
    re.IGNORECASE,
)
_BARE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _extract_video_id(url_or_id: str) -> str | None:
    s = url_or_id.strip()
    if _BARE_ID_RE.match(s):
        return s
    m = _VIDEO_ID_RE.search(s)
    return m.group(1) if m else None


@tool
def get_video_transcript(url_or_id: str, max_chars: int = 4000) -> str:
    """Extract the transcript from a YouTube video using its public captions.

    Accepts a full YouTube URL (watch, youtu.be, embed, shorts) or a bare
    11-character video ID. English captions are preferred; if unavailable, any
    other available track is used. Returns the transcript truncated to
    max_chars, cut at a sentence boundary where possible.

    Fails gracefully for videos without captions or private videos.

    Args:
        url_or_id: YouTube URL or 11-char video ID.
        max_chars: Truncate output to this many characters (default 4000).
    """
    try:
        from youtube_transcript_api import (
            NoTranscriptFound,
            TranscriptsDisabled,
            VideoUnavailable,
            YouTubeTranscriptApi,
        )
    except ImportError:
        return "Error: youtube-transcript-api not installed. Run: pip install 'youtube-transcript-api>=1.0'"

    video_id = _extract_video_id(url_or_id)
    if not video_id:
        return f"Error: could not extract video ID from '{url_or_id}'."

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        try:
            transcript = transcript_list.find_transcript(["en", "en-US", "en-GB"])
        except NoTranscriptFound:
            transcript = next(iter(transcript_list), None)
            if transcript is None:
                return f"No transcript available for video '{video_id}'."
        fetched = transcript.fetch()
    except TranscriptsDisabled:
        return f"Transcripts are disabled for video '{video_id}'."
    except VideoUnavailable:
        return f"Error: video '{video_id}' is unavailable or private."
    except Exception as e:
        return f"Error fetching transcript for '{video_id}': {e}"

    text = " ".join(s.text for s in fetched).strip()
    if not text:
        return f"Transcript for '{video_id}' is empty."

    if len(text) <= max_chars:
        return text

    cut = text[:max_chars]
    last_boundary = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if last_boundary > max_chars // 2:
        cut = cut[: last_boundary + 1]
    return cut + f"\n\n[Transcript truncated to {len(cut)} of {len(text)} chars]"
