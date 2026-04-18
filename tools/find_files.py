import subprocess

from langchain_core.tools import tool


@tool
def find_files(query: str) -> str:
    """Search for files on this Mac using Spotlight (mdfind).
    Fast indexed search across the entire filesystem.

    Args:
        query: Search query — file name, content, or type (e.g., "budget.xlsx", "kind:pdf Python").
    """
    try:
        result = subprocess.run(
            ["mdfind", query],
            capture_output=True,
            text=True,
            timeout=15,
        )
        files = result.stdout.strip().splitlines()
        if not files or files == [""]:
            return f"No files found matching '{query}'."

        # Return top 15 results
        output = files[:15]
        total = len(files)
        result_text = "\n".join(output)
        if total > 15:
            result_text += f"\n\n... and {total - 15} more results."
        return result_text
    except subprocess.TimeoutExpired:
        return "Error: Search timed out after 15 seconds."
    except FileNotFoundError:
        # Fallback to find command if mdfind not available
        try:
            result = subprocess.run(
                ["find", str(__import__("pathlib").Path.home()), "-name", f"*{query}*", "-maxdepth", "5"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            files = result.stdout.strip().splitlines()[:15]
            return "\n".join(files) if files else f"No files found matching '{query}'."
        except Exception as e:
            return f"Error searching for files: {e}"
    except Exception as e:
        return f"Error searching for files: {e}"
