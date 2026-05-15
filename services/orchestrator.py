import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

from config import config

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStep(Enum):
    PARSE_RESUME = "M0_parse_resume"
    PARSE_JD = "M1_parse_jd"
    GENERATE_RESUME = "M2_generate"
    GENERATE_INTEL = "M3_intelligence"
    RENDER_PDF = "render_pdf"


STEP_LABELS = {
    PipelineStep.PARSE_RESUME: "正在解析简历...",
    PipelineStep.PARSE_JD: "正在识别JD截图...",
    PipelineStep.GENERATE_RESUME: "正在生成适配简历...",
    PipelineStep.GENERATE_INTEL: "正在搜索公司情报...",
    PipelineStep.RENDER_PDF: "正在导出PDF...",
}


@dataclass
class Task:
    id: str
    status: TaskStatus = TaskStatus.PENDING
    current_step: PipelineStep | None = None
    progress: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "current_step": self.current_step.value if self.current_step else None,
            "current_step_label": STEP_LABELS.get(self.current_step, ""),
            "progress": self.progress,
            "error": self.error,
        }


class Orchestrator:
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._progress_callbacks: list[Callable] = []

    def create_task(self, resume_path: str, jd_image_path: str, company_name: str) -> Task:
        task = Task(id=str(uuid.uuid4())[:8])
        task.progress = {
            "resume_path": resume_path,
            "jd_image_path": jd_image_path,
            "company_name": company_name,
        }
        self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    async def on_progress(self, task: Task):
        for cb in self._progress_callbacks:
            await cb(task)

    def register_progress_callback(self, cb: Callable):
        self._progress_callbacks.append(cb)

    async def run_pipeline(self, task: Task, parser, llm_router, generator, renderer, company_search):
        from services.parser import detect_file_format, extract_text_from_pdf, extract_text_from_docx, clean_extracted_text, compress_image_to_base64
        from llm.prompts import RESUME_STRUCTURING_PROMPT, JD_EXTRACTION_PROMPT

        try:
            # M0: Parse resume
            task.status = TaskStatus.RUNNING
            task.current_step = PipelineStep.PARSE_RESUME
            await self.on_progress(task)

            file_format = detect_file_format(task.progress["resume_path"])
            if file_format == "pdf":
                raw_text = extract_text_from_pdf(task.progress["resume_path"])
            else:
                raw_text = extract_text_from_docx(task.progress["resume_path"])
            cleaned = clean_extracted_text(raw_text)

            profile_json_str = await llm_router.chat(
                system_prompt=RESUME_STRUCTURING_PROMPT,
                user_message=cleaned,
            )
            # Parse JSON, stripping markdown fences if present
            cleaned_json = profile_json_str.strip()
            if cleaned_json.startswith("```"):
                cleaned_json = cleaned_json.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            profile = json.loads(cleaned_json)
            task.progress["profile"] = profile

            # M1: Parse JD image
            task.current_step = PipelineStep.PARSE_JD
            await self.on_progress(task)

            b64, content_type = compress_image_to_base64(task.progress["jd_image_path"])
            jd_json_str = await llm_router.chat_with_image(
                system_prompt=JD_EXTRACTION_PROMPT,
                text="请提取该JD截图中的岗位信息。",
                image_base64=b64,
                content_type=content_type,
            )
            cleaned_jd = jd_json_str.strip()
            if cleaned_jd.startswith("```"):
                cleaned_jd = cleaned_jd.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            jd_keywords = json.loads(cleaned_jd)
            task.progress["jd_keywords"] = jd_keywords

            # M2: Generate tailored resume
            task.current_step = PipelineStep.GENERATE_RESUME
            await self.on_progress(task)

            from services.generator import generate_tailored_prompt, build_resume_html, parse_llm_json_response

            tailoring_prompt = generate_tailored_prompt(profile, jd_keywords)
            tailored_str = await llm_router.chat(
                system_prompt="你是一位资深简历撰写专家。",
                user_message=tailoring_prompt,
            )
            tailored_profile = parse_llm_json_response(tailored_str)
            resume_html = build_resume_html(tailored_profile, jd_keywords)
            task.progress["tailored_profile"] = tailored_profile
            task.progress["resume_html"] = resume_html

            # M3: Company intelligence (non-fatal: skip on search error)
            task.current_step = PipelineStep.GENERATE_INTEL
            await self.on_progress(task)

            company_info = "暂无公司情报（搜索失败，请检查网络连接）"
            try:
                company_info = await company_search(
                    task.progress["company_name"],
                    jd_keywords.get("title", ""),
                    llm_router,
                )
            except Exception as e:
                logger.warning(f"Company intelligence skipped: {e}")
            task.progress["company_info"] = company_info

            from services.generator import generate_self_intro_prompt
            self_intro_prompt = generate_self_intro_prompt(tailored_profile, company_info, jd_keywords)
            self_intro = await llm_router.chat(
                system_prompt="你是一位面试辅导专家。",
                user_message=self_intro_prompt,
            )
            task.progress["self_intro"] = self_intro

            # Render PDF
            task.current_step = PipelineStep.RENDER_PDF
            await self.on_progress(task)

            from services.renderer import render_resume_pdf
            pdf_filename = f"Resume_{task.progress['company_name']}_{task.id}.pdf"
            pdf_path = await render_resume_pdf(resume_html, pdf_filename, config.OUTPUT_DIR)
            task.progress["pdf_path"] = pdf_path

            # Done
            task.status = TaskStatus.COMPLETED
            task.current_step = None
            task.result = {
                "pdf_url": f"/api/download/{task.id}",
                "self_intro": self_intro,
                "company_info": company_info,
            }
            await self.on_progress(task)

        except Exception as e:
            logger.exception(f"Pipeline failed for task {task.id}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await self.on_progress(task)


# Singleton
orchestrator = Orchestrator()
