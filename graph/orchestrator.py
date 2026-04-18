import sys

from langgraph.graph import END, StateGraph

from graph.nodes import executor_node, planner_node, summarizer_node, supervisor_node
from graph.state import AgentState


def _route_supervisor(state: AgentState) -> str:
    """Route from supervisor to the next agent node."""
    agent = state.get("current_agent", "END")
    if agent in ("planner", "executor", "summarizer"):
        return agent
    return "end"


def build_graph():
    """Build and compile the multi-agent task automator graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("summarizer", summarizer_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor routes to the appropriate agent
    graph.add_conditional_edges(
        "supervisor",
        _route_supervisor,
        {
            "planner": "planner",
            "executor": "executor",
            "summarizer": "summarizer",
            "end": END,
        },
    )

    # Each agent routes back to supervisor for the next decision
    graph.add_edge("planner", "supervisor")
    graph.add_edge("executor", "supervisor")
    graph.add_edge("summarizer", "supervisor")

    return graph.compile()


# Compiled graph instance
app = build_graph()


def run(task: str, conversation_history: list[dict] | None = None,
        model_name: str | None = None):
    """Run the task automator and yield state updates for streaming.

    Args:
        task: The user's task description.
        conversation_history: Previous task+summary pairs for context.
        model_name: Override the default Ollama model.

    Yields:
        dict: State updates from each node execution.
    """
    initial_state = AgentState(
        task=task,
        plan=[],
        results=[],
        summary="",
        messages=[],
        current_agent="",
        error=None,
        conversation_history=conversation_history or [],
        model_name=model_name or "",
    )

    for event in app.stream(initial_state, {"recursion_limit": 15}):
        yield event


def run_sync(task: str, conversation_history: list[dict] | None = None,
             model_name: str | None = None) -> str:
    """Run the task automator and return the final summary.

    Args:
        task: The user's task description.
        conversation_history: Previous task+summary pairs for context.
        model_name: Override the default Ollama model.

    Returns:
        The final summary string.
    """
    summary = ""
    for event in run(task, conversation_history, model_name):
        for node_output in event.values():
            if isinstance(node_output, dict) and node_output.get("summary"):
                summary = node_output["summary"]

    return summary or "Task completed but no summary was generated."


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m graph.orchestrator 'your task here'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    print(f"Task: {task}\n")

    for event in run(task):
        for node_name, node_output in event.items():
            print(f"--- [{node_name}] ---")
            if isinstance(node_output, dict):
                for key, value in node_output.items():
                    if value:
                        print(f"  {key}: {value}")
            print()
