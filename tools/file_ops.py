import shutil
from pathlib import Path

from langchain_core.tools import tool

from config import WORKSPACE_DIR

# Resolved so macOS symlinks (/etc → /private/etc) are caught regardless of
# which alias the caller uses. /var and /private are intentionally NOT in
# the list: macOS puts per-user temp files under /var/folders/.../T/ and
# blocking them would break any tempfile-based workflow.
_DENIED_PREFIXES = [
    Path(p).resolve()
    for p in ("/System", "/Library", "/usr", "/etc", "/bin", "/sbin")
]


def _resolve_safe_path(path: str) -> Path:
    """Resolve a path; reject anything landing inside a system-critical directory.

    Relative paths are interpreted under the workspace directory (backwards
    compat with the old sandbox). Absolute paths and ``~``-prefixed paths are
    expanded and resolved as-is, so the LLM can reach things like
    ``~/Downloads`` or ``/tmp/foo``.
    """
    p = Path(path).expanduser()
    resolved = p.resolve() if p.is_absolute() else (WORKSPACE_DIR / path).resolve()

    for denied in _DENIED_PREFIXES:
        if resolved == denied or resolved.is_relative_to(denied):
            raise ValueError(
                f"Access denied: '{path}' resolves into a system-critical directory ({denied})."
            )

    return resolved


@tool
def read_file(path: str) -> str:
    """Read a file. Accepts a workspace-relative path, an absolute path, or a ~/... path (e.g. ~/Downloads/report.pdf).

    Args:
        path: Relative (under ~/task-automator-workspace), absolute, or ~/... path.
    """
    file_path = _resolve_safe_path(path)
    if not file_path.exists():
        return f"Error: File '{path}' not found."
    if not file_path.is_file():
        return f"Error: '{path}' is not a file."
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories if needed. Accepts a workspace-relative path, an absolute path, or a ~/... path.

    Args:
        path: Relative (under ~/task-automator-workspace), absolute, or ~/... path.
        content: The text content to write.
    """
    file_path = _resolve_safe_path(path)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote to '{path}'."
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """List files and directories. Defaults to the workspace root. Accepts a workspace-relative path, an absolute path, or a ~/... path (e.g. ~/Downloads).

    Args:
        path: Relative (under ~/task-automator-workspace), absolute, or ~/... path. Defaults to workspace root.
    """
    dir_path = _resolve_safe_path(path)
    if not dir_path.exists():
        return f"Error: Directory '{path}' not found."
    if not dir_path.is_dir():
        return f"Error: '{path}' is not a directory."

    entries = sorted(dir_path.iterdir())
    if not entries:
        return f"Directory '{path}' is empty."

    lines = []
    for entry in entries[:50]:  # Limit to 50 entries
        prefix = "[DIR] " if entry.is_dir() else "[FILE]"
        lines.append(f"{prefix} {entry.name}")
    return "\n".join(lines)


_CATEGORY_EXTENSIONS: dict[str, set[str]] = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic", ".tiff", ".ico"},
    "Documents": {
        ".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".pages",
        ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".numbers", ".key", ".epub", ".mobi",
    },
    "Archives": {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".dmg", ".iso", ".xz", ".tgz"},
    "Code": {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".scss", ".java",
        ".c", ".cpp", ".h", ".hpp", ".rs", ".go", ".rb", ".php", ".swift", ".kt",
        ".sh", ".json", ".yaml", ".yml", ".toml", ".xml", ".sql",
    },
    "Videos": {".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv", ".m4v", ".mpeg", ".mpg"},
}

_CATEGORY_ORDER = ["Images", "Documents", "Archives", "Code", "Videos", "Other"]


def _category_for(suffix: str) -> str:
    suffix = suffix.lower()
    for category, exts in _CATEGORY_EXTENSIONS.items():
        if suffix in exts:
            return category
    return "Other"


@tool
def organize_files(directory: str, dry_run: bool = False) -> str:
    """Organize a directory into Images/Documents/Archives/Code/Videos/Other subfolders by file extension.

    Only touches files directly in the target directory (not recursive). Hidden
    files, existing category subfolders, and files whose destination already
    exists are skipped. Accepts workspace-relative, absolute, or ~/... paths.

    Args:
        directory: Directory to organize (e.g. ~/Downloads).
        dry_run: If True, return the move plan without touching any files.
    """
    dir_path = _resolve_safe_path(directory)
    if not dir_path.exists():
        return f"Error: Directory '{directory}' not found."
    if not dir_path.is_dir():
        return f"Error: '{directory}' is not a directory."

    moves: list[tuple[Path, Path, str]] = []
    skipped: list[tuple[str, str, str]] = []

    for entry in dir_path.iterdir():
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            continue

        category = _category_for(entry.suffix)
        dest = dir_path / category / entry.name

        if dest.exists():
            skipped.append((entry.name, category, "destination already exists"))
            continue

        moves.append((entry, dest, category))

    if not moves and not skipped:
        return f"Nothing to organize in '{directory}'."

    by_category: dict[str, list[str]] = {}
    for _src, _dest, cat in moves:
        by_category.setdefault(cat, []).append(_src.name)

    header = (
        f"[DRY RUN] Would organize {len(moves)} file(s) in '{directory}':"
        if dry_run
        else f"Organized {len(moves)} file(s) in '{directory}':"
    )
    lines = [header]
    for cat in _CATEGORY_ORDER:
        if cat in by_category:
            names = by_category[cat]
            preview = ", ".join(names[:5])
            more = f" (+{len(names) - 5} more)" if len(names) > 5 else ""
            lines.append(f"  {cat}/ ({len(names)}): {preview}{more}")

    if skipped:
        lines.append(f"Skipped {len(skipped)} file(s):")
        for name, cat, reason in skipped[:5]:
            lines.append(f"  {name} -> {cat}/: {reason}")
        if len(skipped) > 5:
            lines.append(f"  ... and {len(skipped) - 5} more")

    if dry_run:
        return "\n".join(lines)

    errors: list[str] = []
    for src, dest, cat in moves:
        try:
            dest.parent.mkdir(exist_ok=True)
            shutil.move(str(src), str(dest))
        except Exception as e:
            errors.append(f"  {src.name} -> {cat}/: {e}")

    if errors:
        lines.append(f"{len(errors)} error(s) during move:")
        lines.extend(errors[:5])

    return "\n".join(lines)
