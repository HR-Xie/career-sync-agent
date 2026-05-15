import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from search.web import search_company, build_company_query, _parse_ddg_lite


def test_build_company_query_returns_string():
    result = build_company_query("字节跳动", "算法工程师")
    assert "字节跳动" in result
    assert isinstance(result, str)
    assert len(result) > 0


def test_parse_ddg_lite_extracts_results():
    html = """
    <html><body>
    <table>
    <tr><td><a rel="nofollow" href="https://example.com/news">字节跳动新闻</a></td></tr>
    <tr><td class="result-snippet">这是一条关于字节跳动的新闻摘要</td></tr>
    <tr><td><a rel="nofollow" href="https://example.com/funding">融资消息</a></td></tr>
    <tr><td class="result-snippet">公司完成新一轮融资</td></tr>
    </table>
    </body></html>
    """
    results = _parse_ddg_lite(html)
    assert len(results) == 2
    assert results[0]["title"] == "字节跳动新闻"
    assert results[0]["url"] == "https://example.com/news"
    assert "字节跳动" in results[0]["content"]
    assert results[1]["title"] == "融资消息"


def test_parse_ddg_lite_filters_duckduckgo_links():
    html = """
    <a rel="nofollow" href="https://duckduckgo.com/settings">Settings</a>
    <a rel="nofollow" href="https://example.com/real">Real Result</a>
    """
    results = _parse_ddg_lite(html)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/real"


def test_parse_ddg_lite_empty_html():
    results = _parse_ddg_lite("")
    assert results == []


def test_search_company_mock():
    mock_html = """
    <a rel="nofollow" href="https://example.com/news">字节跳动新闻</a>
    <td class="result-snippet">测试摘要</td>
    """

    async def run():
        with patch("search.web.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_resp = AsyncMock()
            mock_resp.text = mock_html
            mock_resp.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_resp
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            result = await search_company("字节跳动", "算法工程师")
            assert "字节跳动" in result
            assert isinstance(result, str)

    asyncio.run(run())


def test_search_company_no_results():
    async def run():
        with patch("search.web.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_resp = AsyncMock()
            mock_resp.text = "<html></html>"
            mock_resp.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_resp
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            result = await search_company("不存在的公司xyz", "测试")
            assert "未找到" in result

    asyncio.run(run())
