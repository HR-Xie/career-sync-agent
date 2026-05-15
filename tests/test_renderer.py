import pytest
from services.renderer import html_to_pdf


SAMPLE_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Test</title></head>
<body><h1>张三 - 简历</h1><p>测试内容</p></body>
</html>"""


@pytest.mark.asyncio
async def test_html_to_pdf_creates_file(tmp_path):
    output_path = tmp_path / "test_output.pdf"
    await html_to_pdf(SAMPLE_HTML, str(output_path))
    assert output_path.exists()
    assert output_path.stat().st_size > 100


@pytest.mark.asyncio
async def test_html_to_pdf_overwrites_existing(tmp_path):
    output_path = tmp_path / "test_output.pdf"
    output_path.write_text("dummy")
    await html_to_pdf(SAMPLE_HTML, str(output_path))
    assert output_path.stat().st_size > 100
