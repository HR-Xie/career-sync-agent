from pydantic import BaseModel


class TaskCreateResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    current_step: str | None
    current_step_label: str
    error: str | None


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    pdf_url: str | None
    self_intro: str | None
    company_info: str | None
    error: str | None


class GenerateRequest(BaseModel):
    company_name: str = ""
