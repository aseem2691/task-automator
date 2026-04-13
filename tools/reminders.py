import subprocess

from langchain_core.tools import tool


def _run_osascript(script: str, timeout: int = 10) -> str:
    """Run an AppleScript via stdin so multi-line scripts don't need shell escaping."""
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
        return "Error: AppleScript timed out. First run may need Automation permission in System Settings → Privacy & Security."
    except FileNotFoundError:
        return "Error: osascript not available (macOS only)."
    except Exception as e:
        return f"Error: {e}"


@tool
def get_reminders(list_name: str = "") -> str:
    """Read incomplete tasks from macOS Reminders.app. Requires Automation permission on first run.

    Args:
        list_name: Optional Reminders list name (e.g. "Groceries"). Empty reads across all lists.
    """
    safe_list = list_name.replace('"', '\\"')
    if list_name:
        script = f'''
tell application "Reminders"
    try
        set lst to list "{safe_list}"
    on error
        return "Error: list " & quoted form of "{safe_list}" & " not found."
    end try
    set output to ""
    repeat with r in (reminders of lst whose completed is false)
        set output to output & "- " & (name of r) & linefeed
    end repeat
    return output
end tell
'''
    else:
        script = '''
tell application "Reminders"
    set output to ""
    repeat with r in (reminders whose completed is false)
        set output to output & "- " & (name of r) & linefeed
    end repeat
    return output
end tell
'''
    result = _run_osascript(script)
    if result.startswith("Error:"):
        return result
    return result if result else "No incomplete reminders found."
