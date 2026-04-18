from pydantic import BaseModel


class TaskRequest(BaseModel):
    task: str
    model_name: str | None = None


class TaskResult(BaseModel):
    task_id: str
    task: str
    summary: str
    plan: list[str]
    status: str  # "running", "completed", "failed"


class HistoryEntry(BaseModel):
    task: str
    summary: str
