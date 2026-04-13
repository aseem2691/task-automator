import subprocess

from langchain_core.tools import tool


def _run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        out = result.stdout.strip()
        return out or result.stderr.strip() or "(no output)"
    except FileNotFoundError:
        return f"(command not found: {cmd[0]})"
    except subprocess.TimeoutExpired:
        return f"(timeout running: {' '.join(cmd)})"
    except Exception as e:
        return f"(error: {e})"


@tool
def get_system_info() -> str:
    """Report macOS system status: battery, disk usage, memory, and CPU load."""
    sections = [
        ("Battery", ["pmset", "-g", "batt"]),
        ("Disk usage (/)", ["df", "-h", "/"]),
        ("Memory (vm_stat)", ["vm_stat"]),
        ("CPU load", ["uptime"]),
    ]
    blocks = []
    for label, cmd in sections:
        blocks.append(f"=== {label} ===\n{_run(cmd)}")
    return "\n\n".join(blocks)
