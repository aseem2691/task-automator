from langchain_core.tools import tool


@tool
def search_videos(query: str, max_results: int = 5) -> str:
    """Search for videos on the web using DuckDuckGo's video index.

    Returns video results with title, URL, duration, publisher, and a short
    description. To fetch a transcript for a specific YouTube result, pass the
    URL to get_video_transcript.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.videos(query, max_results=max_results))
    except Exception as e:
        return f"Error searching for videos: {e}"

    if not results:
        return f"No video results found for '{query}'."

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title") or "(no title)"
        url = r.get("content") or r.get("url") or r.get("href") or ""
        duration = r.get("duration") or ""
        publisher = r.get("publisher") or r.get("provider") or ""
        desc = (r.get("description") or "")[:200]

        meta_parts = [p for p in (duration, publisher) if p]
        meta = " - ".join(meta_parts)
        block = [f"{i}. {title}", f"   {url}"]
        if meta:
            block.append(f"   {meta}")
        if desc:
            block.append(f"   {desc}")
        lines.append("\n".join(block))

    return "\n\n".join(lines)
