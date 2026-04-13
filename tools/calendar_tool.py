import subprocess

from langchain_core.tools import tool


def _run_osascript(script: str, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            ["osascript"],
            input=script.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="ignore").strip()
            return f"Error: {err or 'osascript failed'}"
        return result.stdout.decode("utf-8", errors="ignore").strip()
    except subprocess.TimeoutExpired:
        return "Error: Calendar AppleScript timed out. Iterating multiple calendars can be slow; try reducing days_ahead."
    except FileNotFoundError:
        return "Error: osascript not available (macOS only)."
    except Exception as e:
        return f"Error: {e}"


@tool
def get_calendar_events(days_ahead: int = 7) -> str:
    """Read upcoming events from macOS Calendar.app across all calendars. Requires Automation permission.

    Iterating all calendars can be slow on macOS — this tool uses a 30s timeout.

    Args:
        days_ahead: Number of days ahead to search (default 7).
    """
    if days_ahead < 1:
        days_ahead = 1
    script = f'''
set startDate to current date
set endDate to startDate + ({days_ahead} * days)
tell application "Calendar"
    set output to ""
    repeat with cal in calendars
        set evts to (every event of cal whose start date is greater than or equal to startDate and start date is less than or equal to endDate)
        repeat with e in evts
            set output to output & (summary of e) & " @ " & ((start date of e) as string) & " [" & (title of cal) & "]" & linefeed
        end repeat
    end repeat
    return output
end tell
'''
    result = _run_osascript(script)
    if result.startswith("Error:"):
        return result
    return result if result else f"No events in the next {days_ahead} day(s)."
