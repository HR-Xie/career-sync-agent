import asyncio
import logging

from services.orchestrator import orchestrator, Task
from search.tavily import search_and_summarize_company

logger = logging.getLogger(__name__)


async def execute_task(task: Task, llm_router):
    await orchestrator.run_pipeline(
        task=task,
        parser=None,
        llm_router=llm_router,
        generator=None,
        renderer=None,
        tavily_search=search_and_summarize_company,
    )
