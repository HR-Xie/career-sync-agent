import asyncio
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from api.schemas import GenerateRequest
from services.orchestrator import orchestrator
from config import config

router = APIRouter()


@router.post("/api/generate/{upload_id}")
async def start_generation(upload_id: str, body: GenerateRequest):
    # Find uploaded files by upload_id
    resume_path = None
    jd_path = None

    for f in os.listdir(config.UPLOAD_DIR):
        if f.startswith(upload_id):
            full = os.path.join(config.UPLOAD_DIR, f)
            if "_resume" in f:
                resume_path = full
            elif "_jd" in f:
                jd_path = full

    if not resume_path or not jd_path:
        raise HTTPException(404, "上传文件未找到，请重新上传")

    task = orchestrator.create_task(resume_path, jd_path, body.company_name)

    # Launch async execution
    from worker import execute_task
    from llm.fallback import LLMRouter
    from llm.client import LLMClient

    primary = LLMClient(
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
        model=config.DEEPSEEK_MODEL,
    )
    fallback = LLMClient(
        api_key=config.KIMI_API_KEY,
        base_url=config.KIMI_BASE_URL,
        model=config.KIMI_MODEL,
    )
    llm_router = LLMRouter(primary=primary, fallback=fallback)

    asyncio.create_task(execute_task(task, llm_router))

    return {"task_id": task.id}


@router.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务未找到")
    return task.to_dict()


@router.get("/api/result/{task_id}")
async def get_task_result(task_id: str):
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务未找到")
    return {
        "task_id": task.id,
        "status": task.status.value,
        "pdf_url": task.result.get("pdf_url"),
        "self_intro": task.result.get("self_intro"),
        "company_info": task.result.get("company_info"),
        "company_info_source": task.result.get("company_info_source", ""),
        "error": task.error,
    }


@router.get("/api/download/{task_id}")
async def download_pdf(task_id: str):
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务未找到")
    pdf_path = task.progress.get("pdf_path") or task.result.get("pdf_path", "")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF 文件未找到")
    return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
