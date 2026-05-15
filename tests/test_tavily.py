import asyncio
from unittest.mock import patch, MagicMock

import pytest
from search.tavily import search_company, build_company_query


def test_build_company_query_returns_string():
    result = build_company_query("字节跳动", "算法工程师")
    assert "字节跳动" in result
    assert isinstance(result, str)
    assert len(result) > 0


def test_search_company_mock():
    with patch("search.tavily.TavilyClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.search.return_value = {
            "results": [
                {"title": "字节跳动发布新产品", "content": "...", "url": "https://example.com"}
            ]
        }

        async def run():
            return await search_company("字节跳动", "算法工程师")

        result = asyncio.run(run())
        assert len(result) > 0
        assert isinstance(result, str)
