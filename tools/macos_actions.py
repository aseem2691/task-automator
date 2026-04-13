import subprocess
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool

from config import WORKSPACE_DIR


@tool
def send_notification(title: str, message: str) -> str:
    """Send a native macOS notification.

    Args:
        title: The notification title.
        message: The notification body text.
    """
    try:
        # Escape double quotes in user input
        safe_title = title.replace('"', '\\"')
        safe_message = message.replace('"', '\\"')
        script = f'display notification "{safe_message}" with title "{safe_title}"'
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
            check=True,
        )
        return f"Notification sent: '{title}'"
    except Exception as e:
        return f"Error sending notification: {e}"


@tool
def open_url_or_app(target: str) -> str:
    """Open a URL in the default browser or an application by name.

    Args:
        target: A URL (https://...) or an app name (e.g., "Safari", "Notes", "Calendar").
    """
    try:
        if target.startswith(("http://", "https://", "file://")):
            subprocess.run(["open", target], timeout=5, check=True)
            return f"Opened URL: {target}"
        else:
            subprocess.run(["open", "-a", target], timeout=5, check=True)
            return f"Opened app: {target}"
    except Exception as e:
        return f"Error opening '{target}': {e}"


@tool
def take_screenshot(filename: str = "") -> str:
    """Take a screenshot of the entire screen and save it to the workspace.

    Args:
        filename: Optional filename (without extension). Defaults to screenshot_YYYYMMDD_HHMMSS.
    """
    try:
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = filename.replace("/", "_")
        screenshot_path = Path(WORKSPACE_DIR) / f"{filename}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            ["screencapture", "-x", str(screenshot_path)],
            timeout=10,
            check=True,
        )
        return f"Screenshot saved to: {screenshot_path}"
    except Exception as e:
        return f"Error taking screenshot: {e}"
