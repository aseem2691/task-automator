import shutil
import subprocess

from langchain_core.tools import tool

from tools.file_ops import _resolve_safe_path


@tool
def markdown_to_pdf(source: str, destination: str = "") -> str:
    """Convert a local Markdown file to PDF using pandoc.

    Requires pandoc and a PDF engine on PATH. If conversion fails, pandoc's own error message
    will tell you what's missing — typical install: `brew install pandoc basictex` or
    `brew install pandoc wkhtmltopdf`.

    Args:
        source: Path to the source .md file (workspace-relative, absolute, or ~/...).
        destination: Optional output .pdf path. Defaults to the source path with .pdf extension.
    """
    if shutil.which("pandoc") is None:
        return "Error: pandoc not found on PATH. Install: brew install pandoc basictex"

    src_path = _resolve_safe_path(source)
    if not src_path.exists():
        return f"Error: Source file '{source}' not found."
    if not src_path.is_file():
        return f"Error: '{source}' is not a file."

    dest_path = _resolve_safe_path(destination) if destination else src_path.with_suffix(".pdf")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["pandoc", str(src_path), "-o", str(dest_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            err = result.stderr.strip() or "unknown pandoc error"
            return f"Error from pandoc: {err}"
        return f"Successfully converted '{source}' to '{dest_path}'."
    except subprocess.TimeoutExpired:
        return "Error: pandoc timed out after 60 seconds."
    except Exception as e:
        return f"Error: {e}"
