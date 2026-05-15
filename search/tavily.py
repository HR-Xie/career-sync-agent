from tavily import TavilyClient
from config import config


def build_company_query(company_name: str, job_title: str) -> str:
    return f"{company_name} 公司 最新动态 融资 技术 {job_title}"


async def search_company(company_name: str, job_title: str) -> str:
    client = TavilyClient(api_key=config.TAVILY_API_KEY)
    query = build_company_query(company_name, job_title)
    response = client.search(query=query, search_depth="advanced", max_results=10)

    results = response.get("results", [])
    formatted = []
    for r in results:
        formatted.append(f"## {r.get('title', '')}\n{r.get('content', '')}\n{r.get('url', '')}")

    return "\n\n".join(formatted)


async def search_and_summarize_company(company_name: str, job_title: str, llm_router) -> str:
    from llm.prompts import COMPANY_RESEARCH_PROMPT

    search_results = await search_company(company_name, job_title)
    prompt = COMPANY_RESEARCH_PROMPT.format(
        search_results=search_results,
        company_name=company_name,
        job_title=job_title,
    )
    return await llm_router.chat(
        system_prompt="你是一位行业分析师。",
        user_message=prompt,
    )
