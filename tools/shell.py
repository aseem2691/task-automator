import shlex
import subprocess

from langchain_core.tools import tool

# Allowlist: only these base commands are permitted
ALLOWED_COMMANDS = frozenset({
    "ls", "cat", "head", "tail", "wc", "sort", "uniq", "diff", "file",
    "grep", "egrep", "fgrep", "find", "which", "whereis", "locate",
    "echo", "printf", "date", "cal", "uptime", "whoami", "pwd", "hostname",
    "du", "df", "stat", "touch", "mkdir", "cp", "mv", "ln",
    "env", "printenv", "uname", "sw_vers", "sysctl", "top",
    "ps", "pgrep", "lsof", "ifconfig", "ping", "curl", "wget",
    "tar", "zip", "unzip", "gzip", "gunzip",
    "python3", "python", "pip", "pip3", "node", "npm", "brew",
    "git", "open", "pbcopy", "pbpaste", "say", "mdfind", "mdls",
    "sed", "awk", "cut", "tr", "tee", "xargs", "basename", "dirname",
    "realpath", "readlink", "less", "more", "man",
})


def _extract_base_command(command: str) -> str | None:
    """Extract the first command from a shell command string."""
    try:
        tokens = shlex.split(command)
        if not tokens:
            return None
        # Handle env vars like KEY=val cmd, sudo, etc.
        for token in tokens:
            if "=" in token and not token.startswith("-"):
                continue
            # Get the basename (handles /usr/bin/ls → ls)
            base = token.rsplit("/", 1)[-1]
            return base
    except ValueError:
        # shlex can fail on unmatched quotes — try naive split
        parts = command.strip().split()
        if parts:
            return parts[0].rsplit("/", 1)[-1]
    return None


def _check_piped_commands(command: str) -> str | None:
    """Validate all commands in a piped chain. Returns error or None."""
    # Split on pipes and logical operators
    segments = command.replace("&&", "|").replace("||", "|").replace(";", "|").split("|")
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        base = _extract_base_command(segment)
        if base and base not in ALLOWED_COMMANDS:
            return f"Error: Command '{base}' is not in the allowlist. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"
    return None


@tool
def run_shell(command: str) -> str:
    """Run a shell command and return its output. Has a 30-second timeout.
    Only allowlisted commands are permitted for safety.

    Args:
        command: The shell command to execute.
    """
    command = command.strip()
    if not command:
        return "Error: Empty command."

    # Validate all commands in the pipeline
    error = _check_piped_commands(command)
    if error:
        return error

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code]: {result.returncode}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {e}"
