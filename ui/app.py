import json
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from config import (
    MODEL_NAME,
    WORKSPACE_DIR,
    check_ollama,
    ensure_dirs,
    get_available_models,
    load_history,
    save_history,
)
from graph.orchestrator import run

# Page config
st.set_page_config(
    page_title="Task Automator",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Task Automator")
st.caption("Multi-agent AI assistant powered by LangGraph + Ollama")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history()
if "running" not in st.session_state:
    st.session_state.running = False
if "selected_model" not in st.session_state:
    st.session_state.selected_model = MODEL_NAME

# Sidebar
with st.sidebar:
    st.header("Settings")

    # Model selector
    available_models = get_available_models()
    if st.session_state.selected_model not in available_models:
        available_models.append(st.session_state.selected_model)
    selected = st.selectbox(
        "Model",
        available_models,
        index=available_models.index(st.session_state.selected_model),
    )
    st.session_state.selected_model = selected

    # Theme toggle
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    st.toggle("Dark mode", key="dark_mode")

    st.divider()
    st.header("Task History")
    if st.session_state.chat_history:
        for i, entry in enumerate(reversed(st.session_state.chat_history)):
            task_num = len(st.session_state.chat_history) - i
            label = entry["task"][:40]
            with st.expander(f"Task {task_num}: {label}..."):
                st.write(entry["summary"])
    else:
        st.write("No tasks yet. Try one!")

    st.divider()
    st.write(f"**Workspace:** `{WORKSPACE_DIR}`")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear History"):
            st.session_state.chat_history = []
            save_history([])
            st.rerun()
    with col2:
        if st.session_state.chat_history:
            st.download_button(
                "Export JSON",
                data=json.dumps(st.session_state.chat_history, indent=2),
                file_name="task_history.json",
                mime="application/json",
            )

# Display chat messages
for entry in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(entry["task"])
    with st.chat_message("assistant"):
        st.write(entry["summary"])

# Chat input
if prompt := st.chat_input("Describe a task... (e.g., 'search for latest Python news and summarize it')"):
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)

    # Run the task automator
    with st.chat_message("assistant"):
        # Auto-start Ollama and pull model if needed
        ensure_dirs()
        with st.spinner("Checking Ollama (auto-starting if needed)..."):
            if not check_ollama():
                st.error("Could not start Ollama. Please install it from https://ollama.com")
                st.stop()

        summary = ""
        with st.status("Working on your task...", expanded=True) as status:
            try:
                for event in run(
                    prompt,
                    conversation_history=st.session_state.chat_history,
                    model_name=st.session_state.selected_model,
                ):
                    for node_name, node_output in event.items():
                        if node_name == "supervisor":
                            next_agent = node_output.get("current_agent", "")
                            if next_agent and next_agent != "END":
                                st.write(f"🔄 Routing to **{next_agent}**...")

                        elif node_name == "planner":
                            plan = node_output.get("plan", [])
                            if plan:
                                st.write("📋 **Plan created:**")
                                for j, step in enumerate(plan, 1):
                                    st.write(f"  {j}. {step}")

                        elif node_name == "executor":
                            results = node_output.get("results", [])
                            if results:
                                st.write(f"🔧 **Executed {len(results)} subtask(s)**")
                                for idx, result in enumerate(results, start=1):
                                    for line in result.splitlines():
                                        if line.startswith("[TOOL_ERROR]") or line.startswith("[SUBTASK_ERROR]"):
                                            st.warning(f"Subtask {idx}: {line}")

                        elif node_name == "summarizer":
                            summary = node_output.get("summary", "")

                        error = node_output.get("error") if isinstance(node_output, dict) else None
                        if error:
                            st.error(f"Error: {error}")
                            summary = f"Task failed: {error}"

                status.update(label="Task completed!", state="complete")
            except Exception as e:
                status.update(label="Task failed", state="error")
                summary = f"An error occurred: {e}"
                st.error(summary)

        # Display final summary
        if summary:
            st.markdown("---")
            st.markdown(summary)

        # Save to history (session + disk)
        st.session_state.chat_history.append({
            "task": prompt,
            "summary": summary or "No summary generated.",
        })
        save_history(st.session_state.chat_history)
