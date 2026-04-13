import ssl
import urllib.parse
import urllib.request

import certifi
from langchain_core.tools import tool

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


@tool
def get_weather(location: str = "") -> str:
    """Get the current weather for a location using wttr.in (no API key required).

    Args:
        location: City name like "San Francisco" or "Mumbai". Leave empty for auto-detection by IP.
    """
    try:
        query = urllib.parse.quote(location) if location else ""
        # Format: 3-line minimal current weather
        url = f"https://wttr.in/{query}?format=3"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88"})
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as resp:
            result = resp.read().decode("utf-8").strip()
        return result or "No weather data returned."
    except Exception as e:
        return f"Error fetching weather: {e}"
