# Task Automator

A multi-agent AI assistant that runs entirely on your Mac. Give it a task in plain English and it breaks it down, executes it using 26 built-in tools, and returns a summary. No cloud APIs, no API keys, no data leaving your machine.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) + [Ollama](https://ollama.com) + [Streamlit](https://streamlit.io).

## How It Works

```
User prompt
    |
    v
Supervisor  -->  Planner  -->  Executor  -->  Summarizer  -->  Result
 (router)      (2-3 steps)   (tool calls)    (bullet points)
```

1. **Supervisor** routes the task through the pipeline (no LLM call, just logic)
2. **Planner** breaks your request into 2-3 subtasks using the LLM
3. **Executor** runs each subtask, selecting the best tools from 26 available
4. **Summarizer** compiles everything into a concise answer

The executor uses **per-subtask tool subsetting** -- it picks the 8 most relevant tools for each step instead of exposing all 26 at once. This dramatically improves tool-call accuracy on small local models.

## Quick Start

### Prerequisites

- **macOS** (uses AppleScript for calendar, reminders, notifications)
- **Python 3.12+**
- **[Ollama](https://ollama.com)** installed (the app auto-starts it and pulls the model)

### Setup

```bash
git clone https://github.com/aseem2691/task-automator.git
cd task-automator

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
source venv/bin/activate
streamlit run ui/app.py
```

That's it. Ollama auto-starts in the background and pulls `llama3.2:3b` on first run. The browser opens at `http://localhost:8501`.

## What It Can Do

### 26 Built-in Tools

| Category | Tools |
|----------|-------|
| **File & Shell** | Read/write files, list/organize directories, read PDFs, Markdown to PDF, run shell commands |
| **Research** | Web search (DuckDuckGo), RSS feeds, video search, YouTube transcripts, live sports scores |
| **Utilities** | Date/time, calculator, weather, system info (battery, disk, memory, CPU) |
| **Notes** | Save and retrieve local notes |
| **macOS** | Clipboard, notifications, open URLs/apps, screenshots, reminders, calendar events, email drafts |

### Example Prompts

```
"What's the live IPL cricket score?"

"Get today's date, weather in Mumbai, and top Hacker News stories. Save as a note."

"Search the web for the latest Python 3.14 features and summarize."

"Calculate my monthly savings: earn 80000, spend 45000. Write it to budget.txt."

"Read my clipboard, convert it to bullet points, copy back."

"Fetch TechCrunch RSS headlines and save a digest note."

"Get the transcript of this YouTube video and summarize it: https://youtu.be/dQw4w9WgXcQ"
```

## Project Structure

```
task-automator/
├── config.py                # Ollama settings, auto-start, model pull
├── requirements.txt
├── graph/
│   ├── state.py             # AgentState (TypedDict for LangGraph)
│   ├── nodes.py             # Supervisor, Planner, Executor, Summarizer
│   └── orchestrator.py      # StateGraph wiring + run() entry point
├── tools/
│   ├── calculator.py        # Safe math eval (AST-based, no eval())
│   ├── calendar_tool.py     # Calendar.app events via AppleScript
│   ├── clipboard.py         # macOS pbcopy/pbpaste
│   ├── datetime_tool.py     # Current date/time/timezone
│   ├── file_ops.py          # Read/write/list/organize with deny-list
│   ├── macos_actions.py     # Notifications, open URL/app, screenshots
│   ├── mail_draft.py        # Mail.app drafts via AppleScript (never sends)
│   ├── md_to_pdf.py         # Markdown to PDF via pandoc
│   ├── notes.py             # Local JSON note storage
│   ├── pdf_reader.py        # PDF text extraction via pypdf
│   ├── reminders.py         # Reminders.app via AppleScript
│   ├── rss.py               # RSS/Atom feed parser with presets
│   ├── shell.py             # Shell execution with command deny-list
│   ├── sports.py            # Live scores via ESPN public API
│   ├── system_info.py       # Battery, disk, memory, CPU load
│   ├── videos.py            # DuckDuckGo video search
│   ├── weather.py           # Weather via wttr.in (no API key)
│   ├── web_search.py        # Web search via DuckDuckGo
│   └── youtube.py           # YouTube transcript extraction
└── ui/
    └── app.py               # Streamlit chat interface
```

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| LLM | Ollama + `llama3.2:3b` | Runs on MacBook Air without overheating |
| Orchestration | LangGraph | Multi-agent state machine with conditional routing |
| Tools | LangChain `@tool` | Simple decorator-based tool registration |
| Search | DuckDuckGo (`ddgs`) | No API key needed |
| Sports | ESPN public API | Real-time scores, no signup required |
| Weather | wttr.in | No API key needed |
| UI | Streamlit | Chat interface with real-time agent progress |

## Design Decisions

- **No API keys required.** Every external service (search, weather, sports, transcripts) uses free public endpoints.
- **Per-subtask tool subsetting.** Small models (3B params) can't pick the right tool from 26 options. The executor ranks tools by keyword overlap with each subtask and binds only the top 8, which fixes tool-call accuracy.
- **Planner is tool-aware.** The planner prompt includes the list of available tool names so it generates subtasks that align with actual capabilities.
- **Supervisor has no LLM call.** Pure routing logic saves one LLM round-trip per task.
- **Tuned for low-end hardware.** Context window is 2048 tokens, max response is 512, tool results are truncated to 1000 chars.

## Optional Dependencies

Some tools need extra software installed:

| Tool | Dependency | Install |
|------|-----------|---------|
| `markdown_to_pdf` | pandoc + PDF engine | `brew install pandoc basictex` |
| `get_calendar_events` | macOS Automation permission | Grant on first run when prompted |
| `get_reminders` | macOS Automation permission | Grant on first run when prompted |
| `compose_email_draft` | macOS Automation permission | Grant on first run when prompted |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Ollama overheating / high CPU | You're using too large a model. Stick with `llama3.2:3b` in `config.py` |
| Tool call malformed | Ollama limitation with small models. Retry logic handles most cases. Restart Streamlit if it persists |
| Search returning empty | `ddgs` occasionally rate-limits. Wait a minute and retry |
| Calendar/Reminders error | Grant Automation permission when macOS prompts you on first run |

## License

MIT
