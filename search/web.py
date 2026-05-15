import re
import httpx
from config import config


def build_company_query(company_name: str, job_title: str) -> str:
    return f"{company_name} 公司 最新动态 融资 技术 {job_title}"


def _parse_ddg_lite(html: str) -> list[dict]:
    """Parse DuckDuckGo Lite HTML results."""
    results = []
    # DDG Lite: <a rel="nofollow" href="URL">Title</a> ... snippet in next row
    # Pattern: extract link + title, then look for snippet text
    links = re.findall(
        r'<a\s+rel="nofollow"\s+href="(https?://[^"]+)"[^>]*>([^<]+)</a>',
        html
    )
    # Extract snippets - text between </a> and next <a or </td>
    snippets = re.findall(
        r'<td class="result-snippet">(.*?)</td>',
        html,
        re.DOTALL
    )

    for i, (url, title) in enumerate(links):
        # Skip DuckDuckGo internal links
        if 'duckduckgo.com' in url:
            continue
        snippet = ''
        if i < len(snippets):
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
        results.append({
            'title': title.strip(),
            'content': snippet,
            'url': url,
        })

    return results[:10]


async def search_company(company_name: str, job_title: str) -> str:
    query = build_company_query(company_name, job_title)

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": query},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        resp.raise_for_status()

    results = _parse_ddg_lite(resp.text)

    if not results:
        return f"未找到关于 {company_name} 的搜索结果"

    formatted = []
    for r in results:
        content = r.get('content', '')
        if not content:
            content = '(无摘要)'
        formatted.append(f"## {r.get('title', '')}\n{content}\n{r.get('url', '')}")

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
