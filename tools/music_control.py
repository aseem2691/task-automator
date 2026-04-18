import subprocess

from langchain_core.tools import tool


def _run_applescript(script: str) -> str:
    """Run an AppleScript and return the output."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "AppleScript failed")
    return result.stdout.strip()


@tool
def control_music(action: str) -> str:
    """Control the Music app (Apple Music) on macOS.

    Args:
        action: One of "play", "pause", "next", "previous", "status", or "search <query>".
    """
    action = action.strip().lower()

    try:
        if action == "play":
            _run_applescript('tell application "Music" to play')
            return "Music: Playing."

        elif action == "pause" or action == "stop":
            _run_applescript('tell application "Music" to pause')
            return "Music: Paused."

        elif action in ("next", "skip"):
            _run_applescript('tell application "Music" to next track')
            return "Music: Skipped to next track."

        elif action in ("previous", "prev", "back"):
            _run_applescript('tell application "Music" to previous track')
            return "Music: Went to previous track."

        elif action == "status":
            script = '''
            tell application "Music"
                if player state is playing then
                    set trackName to name of current track
                    set trackArtist to artist of current track
                    set trackAlbum to album of current track
                    set pos to player position as integer
                    set dur to duration of current track as integer
                    return "Playing: " & trackName & " by " & trackArtist & " (" & trackAlbum & ") [" & pos & "s / " & dur & "s]"
                else
                    return "Music is not playing."
                end if
            end tell
            '''
            return _run_applescript(script)

        elif action.startswith("search "):
            query = action[7:].strip()
            script = f'''
            tell application "Music"
                set results to (every track whose name contains "{query}" or artist contains "{query}")
                set output to ""
                repeat with t in (items 1 thru (min of {{5, count of results}}) of results)
                    set output to output & name of t & " - " & artist of t & linefeed
                end repeat
                if output is "" then return "No tracks found for '{query}'."
                return output
            end tell
            '''
            return _run_applescript(script).strip() or f"No tracks found for '{query}'."

        else:
            return f"Unknown action '{action}'. Use: play, pause, next, previous, status, or search <query>."
    except Exception as e:
        return f"Error controlling Music: {e}"
