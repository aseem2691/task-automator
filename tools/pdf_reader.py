from langchain_core.tools import tool

from tools.file_ops import _resolve_safe_path


@tool
def read_pdf(path: str, max_pages: int = 20) -> str:
    """Extract text from a local PDF. Accepts workspace-relative, absolute, or ~/... paths.

    Args:
        path: Path to the PDF file.
        max_pages: Maximum number of pages to read (default 20).
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return "Error: pypdf not installed. Run: pip install pypdf"

    file_path = _resolve_safe_path(path)
    if not file_path.exists():
        return f"Error: File '{path}' not found."
    if not file_path.is_file():
        return f"Error: '{path}' is not a file."

    try:
        reader = PdfReader(str(file_path))
        total = len(reader.pages)
        pages_to_read = min(max_pages, total)
        chunks = []
        for i in range(pages_to_read):
            text = reader.pages[i].extract_text() or ""
            if text.strip():
                chunks.append(f"--- Page {i + 1} ---\n{text.strip()}")
        if not chunks:
            return f"PDF '{path}' has {total} page(s) but no extractable text (may be scanned/image-only)."
        body = "\n\n".join(chunks)
        footer = f"\n\n[Read {pages_to_read} of {total} page(s)]"
        return body + footer
    except Exception as e:
        return f"Error reading PDF: {e}"
