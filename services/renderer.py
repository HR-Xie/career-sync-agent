import os
from pathlib import Path
from playwright.async_api import async_playwright


async def html_to_pdf(html_content: str, output_path: str) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(
            path=str(output),
            format="A4",
            margin={"top": "15mm", "right": "15mm", "bottom": "15mm", "left": "15mm"},
            print_background=True,
        )
        await browser.close()
    return str(output)


async def render_resume_pdf(html_content: str, filename: str, output_dir: str = "output") -> str:
    output_path = os.path.join(output_dir, filename)
    return await html_to_pdf(html_content, output_path)
