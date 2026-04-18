from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    task: str                                        # Original user task
    plan: list[str]                                  # Subtasks from planner
    results: list[str]                               # Results from executor
    summary: str                                     # Final compiled answer
    messages: Annotated[list, add_messages]           # Chat history
    current_agent: str                               # Which agent is active
    error: str | None                                # Error message if any
    conversation_history: list[dict]                 # Previous task+summary pairs for context
    model_name: str                                  # Selected Ollama model override
