from datetime import datetime

from langchain_core.tools import tool


@tool
def get_current_datetime() -> str:
    """Get the current date, time, day of week, and timezone."""
    now = datetime.now().astimezone()
    return (
        f"Date: {now.strftime('%Y-%m-%d')}\n"
        f"Time: {now.strftime('%H:%M:%S')}\n"
        f"Day: {now.strftime('%A')}\n"
        f"Timezone: {now.strftime('%Z')}"
    )
