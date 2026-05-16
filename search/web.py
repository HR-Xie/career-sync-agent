import re
import httpx

BING_HOMEPAGE = "https://www.bing.com/"
BING_SEARCH = "https://www.bing.com/search"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def build_company_query(company_name: str, job_title: str) -> str:
    return f"{company_name} 公司 最新动态 融资 技术 {job_title}"


def _parse_bing_html(html: str) -> list[dict]:
    """Parse Bing HTML search results, handling nested li tags."""
    results = []

    # Find all b_algo start positions
    block_starts = [m.start() for m in re.finditer(r'<li\s[^>]*class="[^"]*b_algo[^"]*"[^>]*>', html)]

    for start in block_starts:
        # Find matching </li> by counting li tag nesting
        pos = start
        depth = 1
        for m in re.finditer(r'</?li[\s>]', html[pos + 1:], re.IGNORECASE):
            depth += -1 if m.group().startswith('</') else 1
            if depth == 0:
                pos = pos + 1 + m.end()
                break

        block = html[start:pos]

        # Title + URL from h2
        title_match = re.search(
            r'<h2[^>]*>.*?<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>.*?</h2>',
            block, re.DOTALL
        )
        if not title_match:
            continue

        url = title_match.group(1)
        title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()

        # Snippet from b_lineclamp paragraphs
        snippets = re.findall(
            r'<p[^>]*class="[^"]*b_lineclamp[^"]*"[^>]*>(.*?)</p>',
            block, re.DOTALL
        )
        snippet = ""
        if snippets:
            snippet = re.sub(r'<[^>]+>', '', snippets[0]).strip()

        results.append({
            "title": title,
            "content": snippet,
            "url": url,
        })

    return results[:10]


def _parse_ddg_lite(html: str) -> list[dict]:
    """Parse DuckDuckGo Lite HTML results (fallback)."""
    results = []
    links = re.findall(
        r'<a\s+rel="nofollow"\s+href="(https?://[^"]+)"[^>]*>([^<]+)</a>',
        html
    )
    snippets = re.findall(
        r'<td class="result-snippet">(.*?)</td>',
        html,
        re.DOTALL
    )

    for i, (url, title) in enumerate(links):
        if "duckduckgo.com" in url:
            continue
        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r'<[^>]+>', "", snippets[i]).strip()
        results.append({
            "title": title.strip(),
            "content": snippet,
            "url": url,
        })

    return results[:10]


async def _bing_search(company_name: str, job_title: str) -> str | None:
    query = build_company_query(company_name, job_title)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
        await client.get(BING_HOMEPAGE, params={"mkt": "zh-CN"})
        resp = await client.get(BING_SEARCH, params={
            "q": query,
            "mkt": "zh-CN",
            "setlang": "zh-Hans",
        })
        resp.raise_for_status()

    results = _parse_bing_html(resp.text)
    if not results:
        return None

    formatted = []
    for r in results:
        content = r.get("content", "") or "(无摘要)"
        formatted.append(f"## {r.get('title', '')}\n{content}\n{r.get('url', '')}")

    return "\n\n".join(formatted)


async def _ddg_search(company_name: str, job_title: str) -> str | None:
    query = build_company_query(company_name, job_title)
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": query},
            headers=headers,
        )
        resp.raise_for_status()

    results = _parse_ddg_lite(resp.text)
    if not results:
        return None

    formatted = []
    for r in results:
        content = r.get("content", "") or "(无摘要)"
        formatted.append(f"## {r.get('title', '')}\n{content}\n{r.get('url', '')}")

    return "\n\n".join(formatted)


async def search_company(company_name: str, job_title: str) -> str:
    """Search company info. Tries Bing first, falls back to DuckDuckGo."""
    for attempt in [_bing_search, _ddg_search]:
        try:
            result = await attempt(company_name, job_title)
            if result:
                return result
        except Exception:
            continue

    return f"未找到关于 {company_name} 的搜索结果"


async def search_and_summarize_company(company_name: str, job_title: str, llm_router) -> tuple[str, str]:
    """Returns (content, source_label) where source_label describes where data came from."""
    from llm.prompts import COMPANY_RESEARCH_PROMPT, COMPANY_RESEARCH_FALLBACK_PROMPT

    search_results = await search_company(company_name, job_title)

    if "未找到" in search_results:
        prompt = COMPANY_RESEARCH_FALLBACK_PROMPT.format(
            company_name=company_name,
            job_title=job_title,
        )
        source = "基于 AI 预训练知识生成（网络搜索不可用）"
    else:
        prompt = COMPANY_RESEARCH_PROMPT.format(
            search_results=search_results,
            company_name=company_name,
            job_title=job_title,
        )
        source = "基于 Bing 实时网络搜索结果生成"

    content = await llm_router.chat(
        system_prompt="你是一位行业分析师。",
        user_message=prompt,
    )
    return content, source
