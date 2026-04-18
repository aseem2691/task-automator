import re
import ssl
import urllib.request

import certifi
from langchain_core.tools import tool

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    # Remove script and style blocks
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode common entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


@tool
def summarize_url(url: str) -> str:
    """Fetch a webpage and return its text content (HTML stripped).
    Useful for reading articles, blog posts, or documentation pages.

    Args:
        url: The full URL to fetch (e.g., "https://example.com/article").
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
        )
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CONTEXT) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        text = _strip_html(html)

        if not text:
            return f"No readable content found at {url}."

        # Truncate to ~2000 chars to keep context manageable
        if len(text) > 2000:
            text = text[:2000] + "... [truncated]"

        return text
    except Exception as e:
        return f"Error fetching URL: {e}"
