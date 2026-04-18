# Task Automator

A multi-agent AI assistant that runs entirely on your Mac. Give it a task in plain English and it breaks it down, executes it using 32 built-in tools, and returns a summary. No cloud APIs, no API keys, no data leaving your machine.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) + [Ollama](https://ollama.com) + [Streamlit](https://streamlit.io) + [FastAPI](https://fastapi.tiangolo.com).

## How It Works

```
User prompt
    |
    v
Supervisor  -->  Planner  -->  Executor  -->  Summarizer  -->  Result
 (router)      (2-3 steps)   (tool calls)    (bullet points)
```

1. **Supervisor** routes the task through the pipeline (no LLM call, just logic). Simple tasks skip the planner entirely via fast-path detection.
2. **Planner** breaks your request into 2-3 subtasks using the LLM (tool-aware prompt).
3. **Executor** runs each subtask, selecting the best tools from 32 available. Uses **per-subtask tool subsetting** -- picks the 8 most relevant tools per step.
4. **Summarizer** compiles everything into a concise answer.

## Quick Start

### Prerequisites

- **macOS** (uses AppleScript for calendar, reminders, notifications, music)
- **Python 3.12+**
- **[Ollama](https://ollama.com)** installed (the app auto-starts it and pulls the model)

### Install

```bash
# Clone the repo
git clone https://github.com/aseem2691/task-automator.git
cd task-automator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Streamlit UI

```bash
source venv/bin/activate
streamlit run ui/app.py
```

That's it. Ollama auto-starts in the background and pulls `llama3.2:3b` on first run. The browser opens at `http://localhost:8501`.

### Run the FastAPI Backend

```bash
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

**API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/task` | Submit a task (blocking, returns result) |
| `POST` | `/task/stream` | Submit a task (SSE streaming progress) |
| `GET` | `/history` | Get task history |
| `DELETE` | `/history` | Clear task history |
| `GET` | `/models` | List available Ollama models |
| `GET` | `/health` | Health check (Ollama status) |

**Example API call:**

```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task": "What is the weather in Mumbai?"}'
```

## What It Can Do

### 32 Built-in Tools

| Category | Tools |
|----------|-------|
| **File & Shell** | Read/write files, list/organize directories, find files (Spotlight), read PDFs, Markdown to PDF, run shell commands (allowlisted) |
| **Research** | Web search (DuckDuckGo), fetch & read URLs, RSS feeds, video search, YouTube transcripts, live sports scores |
| **Utilities** | Date/time, calculator, weather, system info, stock prices, unit converter, text translation |
| **Notes** | Save and retrieve local notes |
| **macOS** | Clipboard, notifications, open URLs/apps, screenshots, reminders, calendar events, email drafts, music control |

### Example Prompts

```
"What's the live IPL cricket score?"

"What's the stock price of AAPL?"

"Convert 100 fahrenheit to celsius"

"Translate 'good morning' to Hindi"

"Get today's date, weather in Mumbai, and top Hacker News stories. Save as a note."

"Search the web for the latest Python 3.14 features and summarize."

"Calculate my monthly savings: earn 80000, spend 45000. Write it to budget.txt."

"Read my clipboard, convert it to bullet points, copy back."

"Fetch TechCrunch RSS headlines and save a digest note."

"Find all PDF files on my Mac"

"Play next track in Music app"
```

## Features

- **Fast-path bypass** -- Simple tasks (weather, time, scores) skip the planner and execute directly, saving an LLM round-trip.
- **Conversation memory** -- Follow-up questions work within a session. Previous task results are passed as context.
- **Persistent history** -- Task history is saved to `~/.task-automator/history.json` and survives app restarts.
- **Model selector** -- Switch between any locally installed Ollama model from the sidebar dropdown.
- **Dark mode** -- Dark theme enabled by default via Streamlit config.
- **Export history** -- Download your full task history as a JSON file from the sidebar.
- **Shell security** -- Shell commands use an allowlist (not a deny-list). Only ~50 safe commands are permitted.

## Project Structure

```
task-automator/
├── config.py                # Ollama settings, auto-start, model pull, history persistence
├── requirements.txt
├── .streamlit/
│   └── config.toml          # Streamlit theme (dark mode)
├── api/
│   ├── main.py              # FastAPI backend (REST + SSE streaming)
│   └── models.py            # Pydantic request/response models
├── graph/
│   ├── state.py             # AgentState (TypedDict for LangGraph)
│   ├── nodes.py             # Supervisor, Planner, Executor, Summarizer + 32-tool registry
│   └── orchestrator.py      # StateGraph wiring + run() entry point
├── tools/
│   ├── calculator.py        # Safe math eval (AST-based, no eval())
│   ├── calendar_tool.py     # Calendar.app events via AppleScript
│   ├── clipboard.py         # macOS pbcopy/pbpaste
│   ├── datetime_tool.py     # Current date/time/timezone
│   ├── file_ops.py          # Read/write/list/organize with path deny-list
│   ├── find_files.py        # Spotlight/mdfind file search
│   ├── macos_actions.py     # Notifications, open URL/app, screenshots
│   ├── mail_draft.py        # Mail.app drafts via AppleScript (never sends)
│   ├── md_to_pdf.py         # Markdown to PDF via pandoc
│   ├── music_control.py     # Music.app control via AppleScript
│   ├── notes.py             # Local JSON note storage
│   ├── pdf_reader.py        # PDF text extraction via pypdf
│   ├── reminders.py         # Reminders.app via AppleScript
│   ├── rss.py               # RSS/Atom feed parser with presets
│   ├── shell.py             # Shell execution with command allowlist
│   ├── sports.py            # Live scores via ESPN public API
│   ├── stock_price.py       # Stock quotes via Yahoo Finance (no API key)
│   ├── summarize_url.py     # Fetch and extract text from URLs
│   ├── system_info.py       # Battery, disk, memory, CPU load
│   ├── translate.py         # LLM-based text translation (offline)
│   ├── unit_converter.py    # Temperature, length, weight, volume conversions
│   ├── videos.py            # DuckDuckGo video search
│   ├── weather.py           # Weather via wttr.in (no API key)
│   ├── web_search.py        # Web search via DuckDuckGo
│   └── youtube.py           # YouTube transcript extraction
└── ui/
    └── app.py               # Streamlit chat interface with model selector
```

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| LLM | Ollama + `llama3.2:3b` | Runs on MacBook Air without overheating |
| Orchestration | LangGraph | Multi-agent state machine with conditional routing |
| Tools | LangChain `@tool` | Simple decorator-based tool registration |
| Backend | FastAPI | REST API + SSE streaming for future mobile clients |
| Search | DuckDuckGo (`ddgs`) | No API key needed |
| Sports | ESPN public API | Real-time scores, no signup required |
| Stocks | Yahoo Finance | Real-time quotes, no API key |
| Weather | wttr.in | No API key needed |
| UI | Streamlit | Chat interface with real-time agent progress |

## Design Decisions

- **No API keys required.** Every external service (search, weather, sports, stocks, transcripts) uses free public endpoints.
- **Per-subtask tool subsetting.** Small models (3B params) can't pick the right tool from 32 options. The executor ranks tools by keyword overlap with each subtask and binds only the top 8, which fixes tool-call accuracy.
- **Fast-path bypass.** Simple single-tool tasks (weather, time, scores) are detected by keyword matching and skip the planner entirely, saving an LLM round-trip.
- **Planner is tool-aware.** The planner prompt includes the list of available tool names so it generates subtasks that align with actual capabilities.
- **Supervisor has no LLM call.** Pure routing logic saves one LLM round-trip per task.
- **Shell allowlist, not deny-list.** Only ~50 safe commands are permitted. Everything else is blocked. Piped/chained commands are validated segment by segment.
- **Tuned for low-end hardware.** Context window is 2048 tokens, max response is 512, tool results are truncated to 1000 chars.

## Optional Dependencies

Some tools need extra software installed:

| Tool | Dependency | Install |
|------|-----------|---------|
| `markdown_to_pdf` | pandoc + PDF engine | `brew install pandoc basictex` |
| `get_calendar_events` | macOS Automation permission | Grant on first run when prompted |
| `get_reminders` | macOS Automation permission | Grant on first run when prompted |
| `compose_email_draft` | macOS Automation permission | Grant on first run when prompted |
| `control_music` | macOS Automation permission | Grant on first run when prompted |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Ollama overheating / high CPU | You're using too large a model. Stick with `llama3.2:3b` in `config.py` |
| Tool call malformed | Ollama limitation with small models. Retry logic handles most cases. Restart Streamlit if it persists |
| Search returning empty | `ddgs` occasionally rate-limits. Wait a minute and retry |
| Calendar/Reminders error | Grant Automation permission when macOS prompts you on first run |
| Stock price error | Yahoo Finance may rate-limit. Wait a minute and retry |

## License

MIT
