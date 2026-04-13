import subprocess

from langchain_core.tools import tool

DENIED_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    ":(){",
    "fork bomb",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "chmod -R 777 /",
    "chown -R",
    "> /dev/sda",
    "mv / ",
    "curl | sh",
    "wget | sh",
]


@tool
def run_shell(command: str) -> str:
    """Run a shell command and return its output. Has a 30-second timeout.
    Dangerous commands are blocked for safety.

    Args:
        command: The shell command to execute.
    """
    cmd_lower = command.lower().strip()

    for denied in DENIED_COMMANDS:
        if denied in cmd_lower:
            return f"Error: Command blocked for safety. '{denied}' is not allowed."

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
