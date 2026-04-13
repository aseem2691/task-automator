import subprocess

from langchain_core.tools import tool


def _run_osascript(script: str, timeout: int = 10) -> str:
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
        return "Error: Mail AppleScript timed out. First run may need Automation permission."
    except FileNotFoundError:
        return "Error: osascript not available (macOS only)."
    except Exception as e:
        return f"Error: {e}"


def _as_literal(text: str) -> str:
    """Encode a Python string as an AppleScript string expression, preserving newlines via `& return &`."""
    lines = text.split("\n")
    pieces = [line.replace("\\", "\\\\").replace('"', '\\"') for line in lines]
    return '" & return & "'.join(pieces)


@tool
def compose_email_draft(to: str, subject: str, body: str) -> str:
    """Create a draft in macOS Mail.app (NEVER sends). Requires Automation permission on first run.

    The draft is opened visibly and saved, so the user can review and hit Send manually.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text (supports newlines).
    """
    if not to or "@" not in to:
        return "Error: 'to' must be a valid email address."

    to_literal = _as_literal(to)
    subject_literal = _as_literal(subject)
    body_literal = _as_literal(body)

    script = f'''
tell application "Mail"
    set newMessage to make new outgoing message with properties {{subject:"{subject_literal}", content:"{body_literal}", visible:true}}
    tell newMessage
        make new to recipient with properties {{address:"{to_literal}"}}
    end tell
    save newMessage
end tell
return "Draft saved"
'''
    result = _run_osascript(script)
    if result.startswith("Error:"):
        return result
    return f"Draft created in Mail.app for {to} (subject: {subject!r}). Not sent."
