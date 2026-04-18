# Task Automator — Project Notes

A multi-agent personal productivity assistant built with LangGraph, LangChain, Ollama (local LLM), and Streamlit. Runs entirely on-device on macOS. Designed to be lightweight enough to run on a MacBook Air.

## Stack

- **Language:** Python 3.12
- **LLM:** Ollama with `llama3.2` (lightweight, runs comfortably on MacBook Air)
- **Orchestration:** LangGraph (supervisor → planner → executor → summarizer)
- **UI:** Streamlit chat interface
- **Search:** DuckDuckGo via `ddgs` package
- **RSS/HTTP:** `urllib` with `certifi` for SSL

## Project Structure

```
task-automator/
├── config.py              # Ollama settings, auto-start, health check, LLM factory, history persistence
├── requirements.txt
├── venv/                  # Python virtual environment
├── .streamlit/
│   └── config.toml        # Streamlit theme (dark mode)
├── api/
│   ├── main.py            # FastAPI backend (POST /task, SSE streaming, history)
│   └── models.py          # Pydantic request/response models
├── graph/
│   ├── state.py           # AgentState TypedDict (with conversation_history, model_name)
│   ├── nodes.py           # Supervisor, Planner, Executor, Summarizer + ALL_TOOLS registry (32 tools)
│   └── orchestrator.py    # StateGraph wiring + run() entry point
├── tools/
│   ├── file_ops.py        # read/write/list/organize with deny-list for system dirs
│   ├── shell.py           # Safe shell execution with ALLOWLIST
│   ├── web_search.py      # DuckDuckGo via ddgs
│   ├── summarize_url.py   # Fetch + strip HTML from URLs
│   ├── find_files.py      # Spotlight/mdfind file search
│   ├── stock_price.py     # Yahoo Finance stock quotes (no API key)
│   ├── unit_converter.py  # Length, weight, volume, temperature conversions
│   ├── translate.py       # LLM-based text translation (offline)
│   ├── music_control.py   # Music.app control via AppleScript
│   ├── notes.py           # Local JSON note storage
│   ├── clipboard.py       # macOS pbcopy/pbpaste
│   ├── datetime_tool.py   # Current date/time/day/timezone
│   ├── calculator.py      # Safe AST-based math eval
│   ├── weather.py         # wttr.in (no API key)
│   ├── rss.py             # RSS feed parser with presets
│   ├── macos_actions.py   # Notifications, open URL/app, screenshots
│   ├── pdf_reader.py      # Extract text from local PDFs via pypdf
│   ├── md_to_pdf.py       # Markdown → PDF via pandoc
│   ├── system_info.py     # Battery, disk, memory, CPU load
│   ├── reminders.py       # Read incomplete reminders via AppleScript
│   ├── calendar_tool.py   # Read upcoming Calendar.app events via AppleScript
│   ├── mail_draft.py      # Create (never send) Mail.app drafts via AppleScript
│   ├── sports.py          # Live scores via ESPN's public scoreboard API
│   ├── videos.py          # DuckDuckGo video search
│   └── youtube.py         # YouTube transcript extraction via youtube-transcript-api
└── ui/
    └── app.py             # Streamlit chat UI with model selector, history export, dark mode
```

## Current State — What's Working

### Architecture
- LangGraph multi-agent flow: `supervisor → planner → executor (loops subtasks) → summarizer → END`
- Supervisor is a pure routing function (no LLM call, saves resources)
- Planner capped at 3 subtasks to minimize LLM calls
- Executor passes previous subtask results as context to later subtasks (e.g., search → summarize chain)
- Tool results truncated to 1000 chars to control context size
- LLM config uses `num_ctx=2048`, `num_predict=512` — tuned for MacBook Air

### Ollama Auto-start
- [config.py](config.py) auto-starts `ollama serve` in background if not running
- Auto-pulls the model on first use
- No manual terminal commands needed

### 32 Registered Tools
1. **File & shell**: `read_file`, `write_file`, `list_directory`, `organize_files`, `read_pdf`, `markdown_to_pdf`, `run_shell`
2. **Research & knowledge**: `web_search`, `fetch_rss`, `search_videos`, `get_video_transcript`, `get_live_scores`, `save_note`, `get_notes`, `summarize_url`, `find_files`
3. **Utilities**: `get_current_datetime`, `calculate`, `get_weather`, `get_system_info`, `get_stock_price`, `convert_units`, `translate_text`
4. **macOS integration**: `read_clipboard`, `write_clipboard`, `send_notification`, `open_url_or_app`, `take_screenshot`, `get_reminders`, `get_calendar_events`, `compose_email_draft`, `control_music`

### Verified Working
- All 32 tools load via `ALL_TOOLS` and dispatch by name through the executor
- Streamlit UI launches and executes tasks end-to-end
- Auto-start of Ollama works
- SSL cert issue with weather/RSS fixed using `certifi`
- RSS parsing handles ElementTree falsy-element gotcha correctly
- AppleScript-backed tools (`get_reminders`, `get_calendar_events`, `compose_email_draft`) need macOS Automation permission on first run
- `markdown_to_pdf` needs `pandoc` + a PDF engine on PATH (e.g. `brew install pandoc basictex`)
- `get_live_scores` uses ESPN's public scoreboard API (no key); cricket covers IPL + internationals, soccer covers EPL + UEFA Champions League
- `get_video_transcript` requires `youtube-transcript-api>=1.0` (pinned in `requirements.txt`); the older 0.6.x line no longer works against YouTube's current caption endpoint

## Known Limitations

1. **Gemma 4 too heavy** — initial attempts with `gemma4` (default tag) overheated the MacBook Air. Switched to `llama3.2` which runs smoothly.

2. **Limited concurrency** — single task at a time; no background task queue.

3. **Tool-calling fragility** — Ollama models occasionally produce malformed tool calls. Mitigated with retry logic (2 attempts) but not bulletproof.

## Next Steps / TODO

### Priority 1 — Usability fixes
- [x] **Expand file_ops beyond the sandbox**: accept absolute paths (e.g., `~/Downloads`) while keeping a deny-list for system-critical dirs (`/System`, `/etc`, `/usr`, `/Library`). Resolve `~` before checking.
- [x] **Add `organize_files` tool**: takes a directory, groups files by extension into subfolders (Images/, Documents/, Archives/, Code/, Videos/, Other/). Include a `dry_run` flag that previews moves without executing.
- [x] **Better error messages in the UI** when a tool fails mid-task.

### Priority 2 — More tools
- [x] **PDF reader**: extract text from local PDFs using `pypdf`
- [x] **System info**: battery, disk usage, memory pressure (via `psutil` or `sysctl`)
- [x] **Reminders / Calendar**: read from macOS Reminders.app via AppleScript
- [x] **Email draft**: compose drafts in Mail.app via AppleScript (no send, just draft)
- [x] **Markdown → PDF**: convert notes to PDFs via `pandoc` or `markdown2`

### Priority 3 — Agent quality
- [x] **Per-subtask tool subsetting**: executor picks top 8 tools per subtask by keyword overlap, fixing tool-call accuracy on small models
- [x] **Fast-path bypass**: simple tasks (<=8 words, matching known patterns) skip planner entirely
- [x] **Conversation memory**: previous task+summary pairs passed as context to planner/executor for follow-up questions
- [x] **Shell security**: switched from deny-list to allowlist — only ~50 safe commands permitted
- [x] **Persist task history**: chat history saved to `~/.task-automator/history.json`, survives app restarts
- [ ] **Self-correction loop**: if executor output looks wrong, retry with a reworded query
- [ ] **Streaming tokens to UI**: show LLM output as it's generated, not just after each node completes

### Priority 4 — Mobile / cross-platform
- [x] **FastAPI backend**: `api/main.py` with POST /task, POST /task/stream (SSE), GET /history, GET /models, DELETE /history
- [ ] **React Native mobile client** that talks to the FastAPI backend
- [ ] **Remote Ollama support**: let the mobile client use a Mac running Ollama as the LLM server

### Priority 5 — Polish
- [x] **Model selector**: sidebar dropdown in Streamlit, queries Ollama for available models
- [x] **Dark mode**: `.streamlit/config.toml` with dark theme
- [x] **Export task history**: download button in sidebar exports JSON
- [ ] Pin exact package versions in `requirements.txt`
- [ ] Add unit tests for each tool
- [ ] Add a `--debug` flag to show full LLM prompts/responses

## How to Run

### Streamlit UI
```bash
cd ~/Programming/task-automator
source venv/bin/activate
streamlit run ui/app.py
```

Ollama auto-starts, `llama3.2` auto-pulls on first run. Browser opens at `http://localhost:8501`.

### FastAPI Backend
```bash
cd ~/Programming/task-automator
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`. Endpoints: POST /task, POST /task/stream (SSE), GET /history, GET /models, DELETE /history.

## Example Tasks to Try

- "Get today's date, weather in Mumbai, and top 3 Hacker News stories. Save as a note."
- "Read my clipboard and convert it into bullet points, then copy the result back."
- "Search the web for the latest Python 3.14 features and summarize."
- "Calculate my monthly savings: earn 80000, spend 45000. Write it to budget.txt."
- "Fetch TechCrunch RSS headlines and save a digest note."

## Troubleshooting

- **Ollama overheating / high CPU**: you're using too large a model. Stick with `llama3.2` (set in [config.py:9](config.py#L9)).
- **SSL cert errors**: already fixed using `certifi` in [weather.py](tools/weather.py) and [rss.py](tools/rss.py).
- **Tool call malformed**: Ollama limitation; the retry wrapper handles most cases. Restart Streamlit if it persists.
- **Search returning empty results**: `ddgs` package occasionally rate-limits. Wait a minute and retry.
