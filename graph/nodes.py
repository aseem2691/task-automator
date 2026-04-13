import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config import get_llm
from graph.state import AgentState
from tools.calculator import calculate
from tools.calendar_tool import get_calendar_events
from tools.clipboard import read_clipboard, write_clipboard
from tools.datetime_tool import get_current_datetime
from tools.file_ops import list_directory, organize_files, read_file, write_file
from tools.macos_actions import open_url_or_app, send_notification, take_screenshot
from tools.mail_draft import compose_email_draft
from tools.md_to_pdf import markdown_to_pdf
from tools.notes import get_notes, save_note
from tools.pdf_reader import read_pdf
from tools.reminders import get_reminders
from tools.rss import fetch_rss
from tools.shell import run_shell
from tools.sports import get_live_scores
from tools.system_info import get_system_info
from tools.videos import search_videos
from tools.weather import get_weather
from tools.web_search import web_search
from tools.youtube import get_video_transcript

ALL_TOOLS = [
    # File & shell
    read_file, write_file, list_directory, organize_files, read_pdf, markdown_to_pdf, run_shell,
    # Research & knowledge
    web_search, fetch_rss, search_videos, get_video_transcript, get_live_scores, save_note, get_notes,
    # Utilities
    get_current_datetime, calculate, get_weather, get_system_info,
    # macOS integration
    read_clipboard, write_clipboard,
    send_notification, open_url_or_app, take_screenshot,
    get_reminders, get_calendar_events, compose_email_draft,
]


_TOOL_SELECT_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "could", "may", "might", "must", "can", "of", "to", "in", "on", "at",
    "by", "for", "with", "and", "or", "not", "if", "i", "me", "my", "we",
    "our", "you", "your", "it", "its", "this", "that", "these", "those",
    "what", "which", "who", "when", "where", "why", "how", "get", "tell",
    "show", "give", "find", "please", "about", "into", "from", "as", "any",
})


def _select_tools_for_subtask(subtask: str, tools: list, max_tools: int = 8) -> list:
    """Rank tools by substring overlap with the subtask text and return the top-N.

    Small models (llama3.2:3b) can't discriminate between 20+ tools. Binding
    only the 8 most-relevant tools per subtask dramatically improves tool-call
    accuracy. Zero-match queries fall through to the first N tools in the
    registry (stable order), giving a generic-purpose default set.
    """
    words = [
        w for w in re.findall(r"[a-z]+", subtask.lower())
        if len(w) > 1 and w not in _TOOL_SELECT_STOPWORDS
    ]
    scored = []
    for i, tool in enumerate(tools):
        text = f"{tool.name} {tool.description or ''}".lower()
        score = sum(1 for w in words if w in text)
        scored.append((score, -i, tool))
    scored.sort(reverse=True)
    return [t for _, _, t in scored[:max_tools]]


def _retry_llm_call(llm, messages, max_retries=2):
    """Call LLM with retries to handle Ollama fragility."""
    last_error = None
    for _ in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            last_error = e
    if last_error:
        raise last_error
    else:
        raise RuntimeError("LLM call failed after retries with no exception captured")


def _parse_json_list(text: str) -> list[str]:
    """Extract a JSON list from LLM output, handling malformed responses."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass

    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass

    lines = []
    for line in text.strip().split('\n'):
        cleaned = re.sub(r'^\d+[\.\)]\s*', '', line.strip())
        if cleaned and not cleaned.startswith('{') and not cleaned.startswith('['):
            lines.append(cleaned)
    return lines if lines else [text.strip()]


def supervisor_node(state: AgentState) -> dict:
    """Decide which agent should run next based on the current state. No LLM call."""
    if state.get("error"):
        return {"current_agent": "END"}

    plan = state.get("plan", [])
    results = state.get("results", [])
    summary = state.get("summary", "")

    if not plan:
        return {"current_agent": "planner"}
    elif len(results) < len(plan):
        return {"current_agent": "executor"}
    elif not summary:
        return {"current_agent": "summarizer"}
    else:
        return {"current_agent": "END"}


def planner_node(state: AgentState) -> dict:
    """Break the user's task into 2-3 subtasks. Keeps plans short to minimize LLM calls."""
    llm = get_llm()
    task = state["task"]

    tool_names = ", ".join(t.name for t in ALL_TOOLS)
    messages = [
        SystemMessage(content=(
            "You are a task planner. Break the user's task into 2-3 action steps. "
            "Each step should describe what to do using the available tools.\n"
            f"Available tools: {tool_names}\n"
            "Return a JSON array of strings. Keep each step under 10 words.\n"
            'Example: ["Get current weather in Mumbai", "Summarize the results"]'
        )),
        HumanMessage(content=task),
    ]

    try:
        response = _retry_llm_call(llm, messages)
        plan = _parse_json_list(str(response.content))
        plan = plan[:3]
        if not plan:
            plan = [task]
        return {"plan": plan, "current_agent": "executor"}
    except Exception as e:
        return {"error": f"Planner failed: {e}", "current_agent": "END"}


def executor_node(state: AgentState) -> dict:
    """Execute each subtask using available tools."""
    llm = get_llm()
    plan = state.get("plan", [])
    existing_results = state.get("results", [])
    results = list(existing_results)

    for i in range(len(existing_results), len(plan)):
        subtask = plan[i]
        selected_tools = _select_tools_for_subtask(subtask, ALL_TOOLS)
        llm_with_tools = llm.bind_tools(selected_tools)

        # Keep context short — only last result, truncated
        context = ""
        if results:
            last_result = results[-1][:500]
            context = f"\n\nPrevious result:\n{last_result}"

        messages = [
            SystemMessage(content=(
                "Execute the subtask using tools if needed. "
                "If no tool is needed, answer directly using the previous result. Be brief."
            )),
            HumanMessage(content=f"{subtask}{context}"),
        ]

        try:
            response = _retry_llm_call(llm_with_tools, messages)

            if response.tool_calls:
                tool_map = {t.name: t for t in ALL_TOOLS}
                tool_results = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    if tool_name not in tool_map:
                        tool_results.append(f"[TOOL_ERROR] {tool_name}: tool not registered")
                        continue
                    try:
                        tool_result = tool_map[tool_name].invoke(tool_args)
                        # Truncate long tool results to save context
                        result_str = str(tool_result)[:1000]
                        tool_results.append(f"[{tool_name}]: {result_str}")
                    except Exception as tool_err:
                        tool_results.append(f"[TOOL_ERROR] {tool_name}: {tool_err}")
                results.append(f"Subtask: {subtask}\n" + "\n".join(tool_results))
            else:
                results.append(f"Subtask: {subtask}\nResult: {response.content}")
        except Exception as e:
            results.append(f"Subtask: {subtask}\n[SUBTASK_ERROR] LLM call failed: {e}")

    return {"results": results, "current_agent": "summarizer"}


def summarizer_node(state: AgentState) -> dict:
    """Compile results into a final summary."""
    llm = get_llm()
    task = state["task"]
    results = state.get("results", [])

    # Truncate results to keep prompt small
    results_text = "\n---\n".join(r[:600] for r in results)

    messages = [
        SystemMessage(content="Summarize the results concisely for the user. Use bullet points."),
        HumanMessage(content=f"Task: {task}\n\nResults:\n{results_text}"),
    ]

    try:
        response = _retry_llm_call(llm, messages)
        return {"summary": response.content, "current_agent": "END"}
    except Exception as e:
        return {"summary": f"Summary failed: {e}. Raw results:\n{results_text}", "current_agent": "END"}
