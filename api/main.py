"""FastAPI backend for Task Automator.

Run with:
    uvicorn api.main:app --reload --port 8000
"""

import asyncio
import json
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from api.models import HistoryEntry, TaskRequest, TaskResult
from config import check_ollama, ensure_dirs, get_available_models, load_history, save_history
from graph.orchestrator import run

app = FastAPI(
    title="Task Automator API",
    description="Multi-agent AI assistant powered by LangGraph + Ollama",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store
_tasks: dict[str, TaskResult] = {}


@app.on_event("startup")
async def startup():
    ensure_dirs()


@app.get("/health")
async def health():
    ollama_ok = check_ollama()
    return {"status": "ok" if ollama_ok else "ollama_unavailable", "ollama": ollama_ok}


@app.get("/models")
async def list_models():
    return {"models": get_available_models()}


@app.post("/task", response_model=TaskResult)
async def create_task(req: TaskRequest):
    """Submit a task and get the result (blocking)."""
    if not check_ollama():
        raise HTTPException(503, "Ollama is not available")

    task_id = str(uuid.uuid4())[:8]
    history = load_history()

    summary = ""
    plan = []
    status = "running"

    try:
        for event in run(req.task, conversation_history=history, model_name=req.model_name):
            for node_name, node_output in event.items():
                if node_name == "planner":
                    plan = node_output.get("plan", plan)
                elif node_name == "summarizer":
                    summary = node_output.get("summary", summary)
                if isinstance(node_output, dict) and node_output.get("error"):
                    summary = f"Task failed: {node_output['error']}"
                    status = "failed"

        if status != "failed":
            status = "completed"
    except Exception as e:
        summary = f"Error: {e}"
        status = "failed"

    result = TaskResult(
        task_id=task_id,
        task=req.task,
        summary=summary or "No summary generated.",
        plan=plan,
        status=status,
    )
    _tasks[task_id] = result

    # Persist to history
    history.append({"task": req.task, "summary": result.summary})
    save_history(history)

    return result


@app.post("/task/stream")
async def create_task_stream(req: TaskRequest):
    """Submit a task and stream progress events via SSE."""
    if not check_ollama():
        raise HTTPException(503, "Ollama is not available")

    history = load_history()

    async def event_generator():
        summary = ""
        try:
            for event in run(req.task, conversation_history=history, model_name=req.model_name):
                for node_name, node_output in event.items():
                    payload = {"node": node_name}
                    if node_name == "supervisor":
                        payload["agent"] = node_output.get("current_agent", "")
                    elif node_name == "planner":
                        payload["plan"] = node_output.get("plan", [])
                    elif node_name == "executor":
                        payload["results"] = node_output.get("results", [])
                    elif node_name == "summarizer":
                        summary = node_output.get("summary", "")
                        payload["summary"] = summary

                    if isinstance(node_output, dict) and node_output.get("error"):
                        payload["error"] = node_output["error"]

                    yield f"data: {json.dumps(payload)}\n\n"
                    await asyncio.sleep(0)  # Yield control

            # Persist to history
            if summary:
                hist = load_history()
                hist.append({"task": req.task, "summary": summary})
                save_history(hist)

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/history", response_model=list[HistoryEntry])
async def get_history():
    return load_history()


@app.delete("/history")
async def clear_history():
    save_history([])
    return {"status": "cleared"}
