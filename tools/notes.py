import json
from datetime import datetime

from langchain_core.tools import tool

from config import NOTES_FILE, ensure_dirs


def _load_notes() -> list[dict]:
    ensure_dirs()
    try:
        return json.loads(NOTES_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_notes(notes: list[dict]):
    ensure_dirs()
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


@tool
def save_note(title: str, content: str) -> str:
    """Save a note with a title and content to local storage.

    Args:
        title: The title of the note.
        content: The body/content of the note.
    """
    notes = _load_notes()
    note = {
        "title": title,
        "content": content,
        "created_at": datetime.now().isoformat(),
    }
    notes.append(note)
    _save_notes(notes)
    return f"Note '{title}' saved successfully."


@tool
def get_notes() -> str:
    """Retrieve all saved notes from local storage."""
    notes = _load_notes()
    if not notes:
        return "No notes saved yet."

    output = []
    for i, note in enumerate(notes, 1):
        output.append(f"{i}. [{note['created_at'][:10]}] {note['title']}\n   {note['content']}")
    return "\n\n".join(output)
