import subprocess

from langchain_core.tools import tool


@tool
def read_clipboard() -> str:
    """Read the current contents of the macOS clipboard."""
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        content = result.stdout
        if not content:
            return "(clipboard is empty)"
        return content
    except Exception as e:
        return f"Error reading clipboard: {e}"


@tool
def write_clipboard(content: str) -> str:
    """Write content to the macOS clipboard.

    Args:
        content: The text to copy to the clipboard.
    """
    try:
        subprocess.run(
            ["pbcopy"],
            input=content,
            text=True,
            timeout=5,
            check=True,
        )
        return f"Copied {len(content)} characters to clipboard."
    except Exception as e:
        return f"Error writing clipboard: {e}"
