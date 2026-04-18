import json
import ssl
import urllib.request

import certifi
from langchain_core.tools import tool

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


@tool
def get_stock_price(symbol: str) -> str:
    """Get the current stock price for a ticker symbol using Yahoo Finance.
    No API key required.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL", "RELIANCE.NS" for Indian stocks).
    """
    symbol = symbol.strip().upper()
    try:
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            f"?interval=1d&range=1d"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as resp:
            data = json.loads(resp.read())

        result = data.get("chart", {}).get("result", [])
        if not result:
            return f"No data found for symbol '{symbol}'. Check the ticker."

        meta = result[0].get("meta", {})
        price = meta.get("regularMarketPrice", "N/A")
        prev_close = meta.get("previousClose", 0)
        currency = meta.get("currency", "USD")
        name = meta.get("shortName", symbol)

        change = ""
        if prev_close and price != "N/A":
            diff = price - prev_close
            pct = (diff / prev_close) * 100
            direction = "+" if diff >= 0 else ""
            change = f" ({direction}{diff:.2f}, {direction}{pct:.2f}%)"

        return f"{name} ({symbol}): {price} {currency}{change}"
    except Exception as e:
        return f"Error fetching stock price for '{symbol}': {e}"
