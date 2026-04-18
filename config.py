import subprocess
import time
import urllib.request
import json
from pathlib import Path

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2:3b"

# Paths
WORKSPACE_DIR = Path.home() / "task-automator-workspace"
NOTES_DIR = Path.home() / ".task-automator"
NOTES_FILE = NOTES_DIR / "notes.json"
HISTORY_FILE = NOTES_DIR / "history.json"


def ensure_dirs():
    """Create workspace and notes directories if they don't exist."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    if not NOTES_FILE.exists():
        NOTES_FILE.write_text("[]")


def _is_ollama_running() -> bool:
    """Check if Ollama server is responding."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            resp.read()
        return True
    except Exception:
        return False


def _start_ollama() -> bool:
    """Start the Ollama server in the background. Returns True if started successfully."""
    print("Starting Ollama server...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait for it to be ready (up to 10 seconds)
        for _ in range(20):
            time.sleep(0.5)
            if _is_ollama_running():
                print("Ollama server started.")
                return True
        print("ERROR: Ollama server started but not responding.")
        return False
    except FileNotFoundError:
        print("ERROR: 'ollama' not found. Install it from https://ollama.com")
        return False


def check_ollama() -> bool:
    """Ensure Ollama is running and the model is available.
    Auto-starts Ollama and auto-pulls the model if needed.
    Returns True if ready, False otherwise.
    """
    # Start Ollama if not running
    if not _is_ollama_running():
        if not _start_ollama():
            return False

    # Get available models
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
    except Exception:
        print("ERROR: Cannot connect to Ollama.")
        return False

    # Check if model is available, pull if not
    available_models = [m["name"] for m in data.get("models", [])]
    model_found = any(MODEL_NAME in m for m in available_models)

    if not model_found:
        print(f"Model '{MODEL_NAME}' not found locally. Pulling it now (this may take a few minutes)...")
        try:
            subprocess.run(["ollama", "pull", MODEL_NAME], check=True)
            print(f"Successfully pulled {MODEL_NAME}")
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed to pull {MODEL_NAME}. Run manually: ollama pull {MODEL_NAME}")
            return False

    return True


def get_available_models() -> list[str]:
    """Get list of locally available Ollama models."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return [MODEL_NAME]


def load_history() -> list[dict]:
    """Load chat history from disk."""
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_history(history: list[dict]):
    """Save chat history to disk."""
    try:
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(json.dumps(history, indent=2))
    except OSError:
        pass


def get_llm(model_name: str | None = None):
    """Create and return a ChatOllama instance.

    Args:
        model_name: Override the default model. If None, uses MODEL_NAME.
    """
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=model_name or MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        num_ctx=2048,       # Small context window to save RAM
        num_predict=512,    # Limit response length
    )
