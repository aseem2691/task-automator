import re
import ssl
import urllib.request
from xml.etree import ElementTree as ET

import certifi
from langchain_core.tools import tool

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Preset popular feeds for convenience
PRESET_FEEDS = {
    "hackernews": "https://hnrss.org/frontpage",
    "techcrunch": "https://techcrunch.com/feed/",
    "verge": "https://www.theverge.com/rss/index.xml",
    "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
    "reuters": "https://www.reutersagency.com/feed/?best-topics=tech",
    "arstechnica": "https://feeds.arstechnica.com/arstechnica/index",
}


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


@tool
def fetch_rss(feed: str, max_items: int = 5) -> str:
    """Fetch headlines from an RSS feed. Accepts a URL or a preset name.

    Args:
        feed: RSS feed URL, or a preset name: hackernews, techcrunch, verge, bbc, reuters, arstechnica.
        max_items: Maximum number of items to return (default 5).
    """
    try:
        url = PRESET_FEEDS.get(feed.lower(), feed)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as resp:
            raw = resp.read()

        root = ET.fromstring(raw)
        # Handle both RSS (<item>) and Atom (<entry>) formats
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

        if not items:
            return f"No items found in feed: {feed}"

        def _find(parent, *tags):
            """Find first matching element. Use 'is not None' instead of or (ET elements are falsy when empty)."""
            for tag in tags:
                el = parent.find(tag)
                if el is not None:
                    return el
            return None

        atom_ns = "{http://www.w3.org/2005/Atom}"
        output = []
        for i, item in enumerate(items[:max_items], 1):
            title_el = _find(item, "title", f"{atom_ns}title")
            link_el = _find(item, "link", f"{atom_ns}link")
            desc_el = _find(item, "description", f"{atom_ns}summary", f"{atom_ns}content")

            title = _strip_html(title_el.text) if title_el is not None and title_el.text else "(no title)"
            if link_el is not None:
                link = link_el.text or link_el.attrib.get("href", "")
            else:
                link = ""
            desc = _strip_html(desc_el.text)[:200] if desc_el is not None and desc_el.text else ""

            output.append(f"{i}. {title}\n   {link}\n   {desc}")

        return "\n\n".join(output)
    except Exception as e:
        return f"Error fetching RSS feed '{feed}': {e}"
