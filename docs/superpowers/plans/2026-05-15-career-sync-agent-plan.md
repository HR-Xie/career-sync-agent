# Career-Sync Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 FastAPI + Web 前端的求职助手，支持上传简历(PDF/Word)和JD截图，自动生成定制化PDF简历、面试自我介绍和公司情报。

**Architecture:** 分层 FastAPI 架构，4 模块流水线(M0→M1→M2→M3)，LLM 层统一接口支持 DeepSeek(主力) + Kimi(备选)，WebSocket 实时推送进度。

**Tech Stack:** Python 3.10+, FastAPI, Jinja2, PyMuPDF, python-docx, Pillow, Playwright, OpenAI SDK (兼容 DeepSeek/Kimi), Tavily API, Tailwind CSS CDN

---

### Task 1: 项目脚手架

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: 创建虚拟环境和依赖文件**

```bash
cd "G:/求职助手Agent"
python -m venv venv
```

- [ ] **Step 2: 编写 requirements.txt**

```txt
python-dotenv
httpx
PyMuPDF
python-docx
Pillow
playwright
tavily-python
jinja2
fastapi
uvicorn[standard]
websockets
pydantic
python-multipart
aiofiles
pytest
pytest-asyncio
openai
```

- [ ] **Step 3: 安装依赖**

```bash
source venv/Scripts/activate && pip install -r requirements.txt
```

- [ ] **Step 4: 安装 Playwright 浏览器内核**

```bash
source venv/Scripts/activate && playwright install chromium
```

- [ ] **Step 5: 创建 .env.example**

```env
# DeepSeek API (主力模型)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Kimi API (备选 fallback)
KIMI_API_KEY=your_kimi_api_key_here
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k

# Tavily Search
TAVILY_API_KEY=your_tavily_api_key_here

# App
UPLOAD_DIR=uploads
OUTPUT_DIR=output
MAX_FILE_SIZE_MB=20
```

- [ ] **Step 6: 创建 .gitignore**

```gitignore
venv/
__pycache__/
*.pyc
.env
uploads/
output/
*.pdf
*.docx
```

- [ ] **Step 7: 复制 .env.example 为 .env（用户自行填写 API Key）**

```bash
cp .env.example .env
```

- [ ] **Step 8: 初始化 git 并提交**

```bash
git add requirements.txt .env.example .gitignore
git commit -m "chore: project scaffolding with dependencies and config templates"
```

---

### Task 2: 配置模块

**Files:**
- Create: `config.py`

- [ ] **Step 1: 编写 config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # LLM - DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # LLM - Kimi (fallback)
    KIMI_API_KEY: str = os.getenv("KIMI_API_KEY", "")
    KIMI_BASE_URL: str = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    KIMI_MODEL: str = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

    # Tavily
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # App
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))


config = Config()
```

- [ ] **Step 2: 验证导入**

```bash
source venv/Scripts/activate && python -c "from config import config; print('DEEPSEEK_MODEL:', config.DEEPSEEK_MODEL)"
```

- [ ] **Step 3: 提交**

```bash
git add config.py
git commit -m "feat: add configuration module"
```

---

### Task 3: LLM 客户端（TDD）

**Files:**
- Create: `llm/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_llm_client.py`
- Create: `llm/client.py`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p llm tests
touch llm/__init__.py tests/__init__.py
```

- [ ] **Step 2: 编写失败测试 test_llm_client.py**

```python
import pytest
from llm.client import LLMClient


def test_client_creates_openai_instance():
    client = LLMClient(
        api_key="sk-test",
        base_url="https://test.api.com",
        model="test-model",
    )
    assert client.model == "test-model"
    assert client.client.api_key == "sk-test"


def test_chat_returns_content():
    client = LLMClient(
        api_key="sk-test",
        base_url="https://test.api.com",
        model="test-model",
    )
    with pytest.raises(Exception):
        # No real API key, should fail on connection
        import asyncio
        asyncio.run(client.chat("Hello"))
```

- [ ] **Step 3: 运行测试验证失败**

```bash
source venv/Scripts/activate && pytest tests/test_llm_client.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'llm.client'`

- [ ] **Step 4: 编写最小实现 llm/client.py**

```python
from openai import OpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    async def chat(self, system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""

    async def chat_with_image(
        self, system_prompt: str, text: str, image_base64: str, content_type: str = "image/jpeg"
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{content_type};base64,{image_base64}"},
                        },
                    ],
                },
            ],
        )
        return response.choices[0].message.content or ""
```

- [ ] **Step 5: 运行测试验证通过**

```bash
source venv/Scripts/activate && pytest tests/test_llm_client.py -v
```
Expected: PASS (test_client_creates_openai_instance passes; test_chat_returns_content passes since it expects exception)

- [ ] **Step 6: 提交**

```bash
git add llm/ tests/ && git commit -m "feat: add LLM client with OpenAI-compatible interface"
```

---

### Task 4: LLM Prompt 模板与 Fallback 机制

**Files:**
- Create: `llm/prompts.py`
- Create: `llm/fallback.py`
- Create: `tests/test_llm_fallback.py`

- [ ] **Step 1: 编写测试 test_llm_fallback.py**

```python
import pytest
from llm.client import LLMClient
from llm.fallback import LLMRouter


@pytest.fixture
def primary():
    return LLMClient(api_key="sk-a", base_url="https://api.deepseek.com", model="deepseek-chat")


@pytest.fixture
def fallback():
    return LLMClient(api_key="sk-b", base_url="https://api.moonshot.cn/v1", model="moonshot-v1-8k")


def test_router_has_clients(primary, fallback):
    router = LLMRouter(primary=primary, fallback=fallback)
    assert router.primary is primary
    assert router.fallback is fallback


def test_router_uses_primary_first(primary, fallback, mocker):
    router = LLMRouter(primary=primary, fallback=fallback)
    mock_chat = mocker.patch.object(primary, 'chat', return_value="deepseek response")
    async def run():
        return await router.chat("sys", "msg")
    import asyncio
    result = asyncio.run(run())
    assert result == "deepseek response"
    mock_chat.assert_called_once()


def test_router_falls_back_on_failure(primary, fallback, mocker):
    router = LLMRouter(primary=primary, fallback=fallback)
    mocker.patch.object(primary, 'chat', side_effect=Exception("API error"))
    mocker.patch.object(fallback, 'chat', return_value="kimi response")
    async def run():
        return await router.chat("sys", "msg")
    import asyncio
    result = asyncio.run(run())
    assert result == "kimi response"
```

- [ ] **Step 2: 编写 prompts.py**

```python
RESUME_STRUCTURING_PROMPT = """你是一位专业的简历解析专家。用户提供了一份从PDF/Word文件中提取的简历文本。
文本可能存在换行混乱、分页符残留等问题。请将文本解析为严格符合以下JSON Schema的结构化数据。

规则：
1. 修复被切断的句子和多余的换行
2. 如果某个字段在原简历中不存在，使用空值（空字符串、空数组等）
3. 项目经历和实习经历中的技术栈需要单独提取为数组
4. 保持客观，不要捏造任何不存在的信息

JSON Schema:
{
  "name": "姓名",
  "email": "邮箱",
  "phone": "电话",
  "education": [{"school": "学校", "degree": "学位", "major": "专业", "year": "时间"}],
  "skills": ["技能1", "技能2"],
  "experience": [{"company": "公司", "role": "岗位", "duration": "时间段", "highlights": ["亮点1"]}],
  "projects": [{"name": "项目名", "desc": "描述", "tech_stack": ["技术1"], "achievements": ["成果1"]}],
  "papers": [{"title": "论文标题", "venue": "发表渠道", "year": "年份"}]
}

请直接返回JSON，不要包含任何其他文字。"""

JD_EXTRACTION_PROMPT = """你是一位专业的岗位分析师。用户提供了一张招聘JD的截图。
请提取以下信息，以JSON格式返回：

{
  "title": "岗位名称",
  "skills": ["核心技术栈关键词"],
  "biz_focus": "业务方向概述",
  "must_have": ["必须掌握的技能"],
  "nice_to_have": ["加分技能"]
}

请直接返回JSON，不要包含任何其他文字。"""

RESUME_TAILORING_PROMPT = """你是一位资深的职业顾问和简历撰写专家。请根据目标岗位JD的需求，改写候选人的项目经历和实习经历。

要求：
1. 使用JD中的关键词替换或补充原始描述中的技术术语
2. 对每个项目经历，将其与该岗位最相关的技术栈高亮前置
3. 在每个 achievement 中量化成果（如果原文没有具体数据，保持客观，不要编造数字）
4. 保持 STAR 法则（情境-任务-行动-结果）的结构
5. 改写后的语言要专业、简洁、有说服力

输入格式：
- JD关键词: {jd_keywords}
- 原始简历: {profile_json}

请以JSON格式返回改写后的简历，保持与输入相同的JSON Schema结构。
请直接返回JSON，不要包含任何其他文字。"""

INTERVIEW_SELF_INTRO_PROMPT = """你是一位面试辅导专家。请根据候选人的简历和公司情报，生成一份3分钟的口语化自我介绍。

要求：
1. 使用 STAR 法则组织内容
2. 控制在 400-500 字（3分钟语速）
3. 口语化表达，不要像在读稿子
4. 将候选人的经历与目标公司的业务场景关联
5. 突出与JD最匹配的2-3个经历

候选人简历：{tailored_resume}
目标公司情报：{company_info}
岗位JD：{jd_keywords}

请直接返回自我介绍文本，不要包含标题或提示语。"""

COMPANY_RESEARCH_PROMPT = """你是一位行业分析师。根据搜索到的公司信息，生成一份简洁的公司研究报告。

内容包括：
1. 公司概况（核心产品/业务线）
2. 近期动态（融资、扩张、新产品发布）
3. 技术栈与团队（技术博客、开源项目、技术分享）
4. 面试谈资建议（3-5个可以在面试中提及的话题）

搜索到的信息：{search_results}
目标公司：{company_name}
目标岗位：{job_title}

请用Markdown格式输出，要求条理清晰、重点突出。"""
```

- [ ] **Step 3: 编写 fallback.py**

```python
import logging
from llm.client import LLMClient

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self, primary: LLMClient, fallback: LLMClient | None = None, max_retries: int = 3):
        self.primary = primary
        self.fallback = fallback
        self.max_retries = max_retries

    async def _try_call(self, client: LLMClient, method: str, *args, **kwargs) -> str:
        for attempt in range(self.max_retries):
            try:
                fn = getattr(client, method)
                return await fn(*args, **kwargs)
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
        raise RuntimeError("Unexpected: all retries exhausted")

    async def chat(self, system_prompt: str, user_message: str) -> str:
        try:
            return await self._try_call(self.primary, "chat", system_prompt, user_message)
        except Exception as e:
            logger.error(f"Primary LLM failed: {e}")
            if self.fallback:
                logger.info("Switching to fallback LLM")
                return await self._try_call(self.fallback, "chat", system_prompt, user_message)
            raise

    async def chat_with_image(self, system_prompt: str, text: str, image_base64: str, content_type: str = "image/jpeg") -> str:
        try:
            return await self._try_call(self.primary, "chat_with_image", system_prompt, text, image_base64, content_type)
        except Exception as e:
            logger.error(f"Primary LLM vision failed: {e}")
            if self.fallback:
                logger.info("Switching to fallback LLM for vision")
                return await self._try_call(self.fallback, "chat_with_image", system_prompt, text, image_base64, content_type)
            raise
```

- [ ] **Step 4: 运行测试**

```bash
source venv/Scripts/activate && pytest tests/test_llm_fallback.py -v
```
Expected: 3 PASS

- [ ] **Step 5: 提交**

```bash
git add llm/prompts.py llm/fallback.py tests/test_llm_fallback.py
git commit -m "feat: add prompt templates and LLM fallback router"
```

---

### Task 5: 简历解析服务（TDD）

**Files:**
- Create: `services/__init__.py`
- Create: `tests/test_parser.py`
- Create: `services/parser.py`

- [ ] **Step 1: 创建目录**

```bash
mkdir -p services
touch services/__init__.py
```

- [ ] **Step 2: 准备测试用的 fixture 文件**

创建 `tests/fixtures/` 目录（预留，后续放入真实简历文件）。单元测试用 mock，不依赖真实文件。

- [ ] **Step 3: 编写测试 test_parser.py**

```python
import pytest
from services.parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    clean_extracted_text,
    compress_image_to_base64,
    detect_file_format,
)


class TestDetectFileFormat:
    def test_detects_pdf_by_extension(self):
        assert detect_file_format("/path/to/resume.pdf") == "pdf"

    def test_detects_docx_by_extension(self):
        assert detect_file_format("/path/to/resume.docx") == "docx"

    def test_detects_pdf_by_magic_bytes(self, tmp_path):
        p = tmp_path / "test.bin"
        p.write_bytes(b"%PDF-1.4 skldjflskjdf")
        assert detect_file_format(str(p)) == "pdf"

    def test_detects_docx_by_magic_bytes(self, tmp_path):
        p = tmp_path / "test.bin"
        p.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
        assert detect_file_format(str(p)) == "docx"

    def test_rejects_unknown_format(self, tmp_path):
        p = tmp_path / "test.xyz"
        p.write_bytes(b"random content here")
        with pytest.raises(ValueError, match="Unsupported file format"):
            detect_file_format(str(p))


class TestCleanText:
    def test_removes_excessive_newlines(self):
        text = "张三\n\n\n\n本科\n\n\n\n清华大学"
        cleaned = clean_extracted_text(text)
        assert "\n\n\n\n" not in cleaned

    def test_preserves_single_newlines(self):
        text = "项目经历\n水下目标检测\n负责算法开发"
        cleaned = clean_extracted_text(text)
        assert "\n" in cleaned

    def test_removes_form_feed(self):
        text = "第一页内容\f第二页内容"
        cleaned = clean_extracted_text(text)
        assert "\f" not in cleaned


class TestCompressImage:
    def test_compresses_and_returns_base64(self, tmp_path):
        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (1920, 1080), color="red")
        img.save(str(img_path))

        result = compress_image_to_base64(str(img_path), max_width=800)
        assert "base64" in result
        assert len(result) > 0
```

- [ ] **Step 4: 运行测试验证失败**

```bash
source venv/Scripts/activate && pytest tests/test_parser.py -v
```
Expected: FAIL

- [ ] **Step 5: 编写实现 services/parser.py**

```python
import base64
import io
import re
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document
from PIL import Image


def detect_file_format(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext in (".pdf", ".docx"):
        return ext.lstrip(".")

    # Magic bytes detection
    with open(file_path, "rb") as f:
        header = f.read(8)

    if header.startswith(b"%PDF"):
        return "pdf"
    if header.startswith(b"PK\x03\x04"):
        return "docx"

    raise ValueError(f"Unsupported file format: {ext or 'unknown'}")


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def clean_extracted_text(text: str) -> str:
    # Remove form feed characters
    text = text.replace("\f", "\n")
    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove lines that are only whitespace
    text = re.sub(r"\n\s+\n", "\n", text)
    return text.strip()


def compress_image_to_base64(image_path: str, max_width: int = 1080) -> str:
    img = Image.open(image_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    buffer = io.BytesIO()
    fmt = img.format or "JPEG"
    if fmt.upper() == "PNG":
        img.save(buffer, format="PNG", optimize=True)
        content_type = "image/png"
    else:
        img = img.convert("RGB")
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        content_type = "image/jpeg"

    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return b64, content_type
```

- [ ] **Step 6: 运行测试验证通过**

```bash
source venv/Scripts/activate && pytest tests/test_parser.py -v
```
Expected: all PASS

- [ ] **Step 7: 提交**

```bash
git add services/parser.py tests/test_parser.py services/__init__.py
git commit -m "feat: add resume parsing service (PDF/Word/image)"
```

---

### Task 6: 内容生成服务（TDD）

**Files:**
- Create: `tests/test_generator.py`
- Create: `services/generator.py`

- [ ] **Step 1: 编写测试 test_generator.py**

```python
import pytest
from services.generator import build_resume_html, generate_tailored_resume_content


SAMPLE_PROFILE = {
    "name": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800000000",
    "education": [{"school": "清华大学", "degree": "硕士", "major": "计算机科学", "year": "2023-2026"}],
    "skills": ["Python", "PyTorch", "OpenCV", "Docker"],
    "experience": [
        {
            "company": "某科技公司",
            "role": "算法实习生",
            "duration": "2025.06-2025.12",
            "highlights": ["优化模型推理速度30%", "参与目标检测项目"],
        }
    ],
    "projects": [
        {
            "name": "SEAD-YOLO",
            "desc": "水下目标检测算法研究",
            "tech_stack": ["Python", "PyTorch", "YOLO"],
            "achievements": ["mAP提升5个百分点"],
        }
    ],
    "papers": [],
}

SAMPLE_JD = {
    "title": "算法工程师",
    "skills": ["Python", "PyTorch", "目标检测", "模型部署"],
    "biz_focus": "自动驾驶感知",
    "must_have": ["Python", "深度学习"],
    "nice_to_have": ["TensorRT", "模型量化"],
}


def test_build_resume_html_contains_name():
    html = build_resume_html(SAMPLE_PROFILE, SAMPLE_JD)
    assert "张三" in html
    assert "算法工程师" in html


def test_build_resume_html_is_valid_html():
    html = build_resume_html(SAMPLE_PROFILE, SAMPLE_JD)
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html


def test_build_resume_html_includes_skills():
    html = build_resume_html(SAMPLE_PROFILE, SAMPLE_JD)
    assert "Python" in html
    assert "PyTorch" in html
    assert "SEAD-YOLO" in html
```

- [ ] **Step 2: 运行测试验证失败**

```bash
source venv/Scripts/activate && pytest tests/test_generator.py -v
```
Expected: FAIL

- [ ] **Step 3: 编写实现 services/generator.py**

```python
import json
import re
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = "templates/resumes"


def build_resume_html(profile: dict, jd_keywords: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("modern.html")
    return template.render(profile=profile, jd=jd_keywords)


def parse_llm_json_response(text: str) -> dict:
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if len(lines) > 1 else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def generate_tailored_prompt(profile: dict, jd_keywords: dict) -> str:
    from llm.prompts import RESUME_TAILORING_PROMPT

    return RESUME_TAILORING_PROMPT.format(
        jd_keywords=json.dumps(jd_keywords, ensure_ascii=False, indent=2),
        profile_json=json.dumps(profile, ensure_ascii=False, indent=2),
    )


def generate_self_intro_prompt(tailored_resume: dict, company_info: str, jd_keywords: dict) -> str:
    from llm.prompts import INTERVIEW_SELF_INTRO_PROMPT

    return INTERVIEW_SELF_INTRO_PROMPT.format(
        tailored_resume=json.dumps(tailored_resume, ensure_ascii=False, indent=2),
        company_info=company_info,
        jd_keywords=json.dumps(jd_keywords, ensure_ascii=False, indent=2),
    )


def generate_company_research_prompt(search_results: str, company_name: str, job_title: str) -> str:
    from llm.prompts import COMPANY_RESEARCH_PROMPT

    return COMPANY_RESEARCH_PROMPT.format(
        search_results=search_results,
        company_name=company_name,
        job_title=job_title,
    )
```

- [ ] **Step 4: 创建简历 HTML 模板（先创建最小版以通过测试）**

Create: `templates/resumes/modern.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{{ profile.name }} - 简历</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white p-8 max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold">{{ profile.name }}</h1>
    <p class="text-gray-600">{{ profile.email }} | {{ profile.phone }}</p>
    <p class="text-sm text-blue-600">目标岗位：{{ jd.title }}</p>

    <section class="mt-6">
        <h2 class="text-lg font-semibold border-b pb-1">技能</h2>
        <div class="flex flex-wrap gap-2 mt-2">
            {% for skill in profile.skills %}
            <span class="px-2 py-1 bg-gray-100 rounded text-sm">{{ skill }}</span>
            {% endfor %}
        </div>
    </section>

    <section class="mt-4">
        <h2 class="text-lg font-semibold border-b pb-1">项目经历</h2>
        {% for project in profile.projects %}
        <div class="mt-3">
            <h3 class="font-medium">{{ project.name }}</h3>
            <p class="text-sm text-gray-700">{{ project.desc }}</p>
            <div class="flex flex-wrap gap-1 mt-1">
                {% for tech in project.tech_stack %}
                <span class="text-xs px-1 py-0.5 bg-blue-50 text-blue-700 rounded">{{ tech }}</span>
                {% endfor %}
            </div>
            <ul class="list-disc list-inside text-sm mt-1">
                {% for achievement in project.achievements %}
                <li>{{ achievement }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endfor %}
    </section>

    <section class="mt-4">
        <h2 class="text-lg font-semibold border-b pb-1">工作/实习经历</h2>
        {% for exp in profile.experience %}
        <div class="mt-3">
            <div class="flex justify-between">
                <span class="font-medium">{{ exp.company }} - {{ exp.role }}</span>
                <span class="text-sm text-gray-500">{{ exp.duration }}</span>
            </div>
            <ul class="list-disc list-inside text-sm mt-1">
                {% for hl in exp.highlights %}
                <li>{{ hl }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endfor %}
    </section>

    <section class="mt-4">
        <h2 class="text-lg font-semibold border-b pb-1">教育背景</h2>
        {% for edu in profile.education %}
        <div class="mt-2 flex justify-between">
            <span>{{ edu.school }} - {{ edu.major }} {{ edu.degree }}</span>
            <span class="text-sm text-gray-500">{{ edu.year }}</span>
        </div>
        {% endfor %}
    </section>
</body>
</html>
```

- [ ] **Step 5: 创建模板目录并运行测试**

```bash
mkdir -p templates/resumes
# After writing the template file:
source venv/Scripts/activate && pytest tests/test_generator.py -v
```
Expected: 3 PASS

- [ ] **Step 6: 提交**

```bash
git add services/generator.py tests/test_generator.py templates/
git commit -m "feat: add content generator with Jinja2 resume template"
```

---

### Task 7: PDF 渲染服务（TDD）

**Files:**
- Create: `tests/test_renderer.py`
- Create: `services/renderer.py`

- [ ] **Step 1: 编写测试 test_renderer.py**

```python
import pytest
from pathlib import Path
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
    assert output_path.stat().st_size > 100  # PDF header + content > 100 bytes


@pytest.mark.asyncio
async def test_html_to_pdf_overwrites_existing(tmp_path):
    output_path = tmp_path / "test_output.pdf"
    output_path.write_text("dummy")
    await html_to_pdf(SAMPLE_HTML, str(output_path))
    assert output_path.stat().st_size > 100
```

- [ ] **Step 2: 运行测试验证失败**

```bash
source venv/Scripts/activate && pytest tests/test_renderer.py -v
```
Expected: FAIL

- [ ] **Step 3: 编写实现 services/renderer.py**

```python
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
```

- [ ] **Step 4: 运行测试**

```bash
source venv/Scripts/activate && pytest tests/test_renderer.py -v
```
Expected: 2 PASS

- [ ] **Step 5: 提交**

```bash
git add services/renderer.py tests/test_renderer.py
git commit -m "feat: add PDF renderer using Playwright headless Chromium"
```

---

### Task 8: Tavily 公司搜索

**Files:**
- Create: `search/__init__.py`
- Create: `search/tavily.py`
- Create: `tests/test_tavily.py`

- [ ] **Step 1: 编写测试 test_tavily.py**

```python
import pytest
from search.tavily import search_company, build_company_query


def test_build_company_query_returns_string():
    result = build_company_query("字节跳动", "算法工程师")
    assert "字节跳动" in result
    assert isinstance(result, str)
    assert len(result) > 0


def test_search_company_mock(mocker):
    mock_client = mocker.patch("search.tavily.TavilyClient")
    mock_instance = mock_client.return_value
    mock_instance.search.return_value = {
        "results": [
            {"title": "字节跳动发布新产品", "content": "...", "url": "https://example.com"}
        ]
    }

    async def run():
        return await search_company("字节跳动", "算法工程师")

    import asyncio
    result = asyncio.run(run())
    assert len(result) > 0
    assert isinstance(result, str)
```

- [ ] **Step 2: 编写实现 search/tavily.py**

```python
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
```

- [ ] **Step 3: 运行测试**

```bash
source venv/Scripts/activate && pytest tests/test_tavily.py -v
```
Expected: 2 PASS

- [ ] **Step 4: 提交**

```bash
git add search/ tests/test_tavily.py
git commit -m "feat: add Tavily company search service"
```

---

### Task 9: 工作流编排器

**Files:**
- Create: `services/orchestrator.py`
- Create: `worker.py`

- [ ] **Step 1: 编写 orchestrator.py**

```python
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

    async def run_pipeline(self, task: Task, parser, llm_router, generator, renderer, tavily_search):
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
            profile = json.loads(profile_json_str.strip().removeprefix("```json").removesuffix("```"))
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
            jd_keywords = json.loads(jd_json_str.strip().removeprefix("```json").removesuffix("```"))
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

            # M3: Company intelligence
            task.current_step = PipelineStep.GENERATE_INTEL
            await self.on_progress(task)

            company_info = await tavily_search(
                task.progress["company_name"],
                jd_keywords.get("title", ""),
                llm_router,
            )
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
```

- [ ] **Step 2: 编写 worker.py**

```python
import asyncio
import logging

from services.parser import compress_image_to_base64
from services.generator import build_resume_html, generate_tailored_prompt, parse_llm_json_response
from services.renderer import render_resume_pdf
from services.orchestrator import orchestrator, Task, TaskStatus
from search.tavily import search_and_summarize_company
from llm.fallback import LLMRouter
from config import config

logger = logging.getLogger(__name__)


async def execute_task(task: Task, llm_router: LLMRouter):
    await orchestrator.run_pipeline(
        task=task,
        parser=None,  # uses direct function imports inside orchestrator
        llm_router=llm_router,
        generator=None,
        renderer=None,
        tavily_search=search_and_summarize_company,
    )
```

- [ ] **Step 3: 验证导入**

```bash
source venv/Scripts/activate && python -c "from services.orchestrator import orchestrator; print('Orchestrator ready')"
```

- [ ] **Step 4: 提交**

```bash
git add services/orchestrator.py worker.py
git commit -m "feat: add pipeline orchestrator and async worker"
```

---

### Task 10: API Schemas & 路由

**Files:**
- Create: `api/__init__.py`
- Create: `api/schemas.py`
- Create: `api/routes/__init__.py`
- Create: `api/routes/upload.py`
- Create: `api/routes/generate.py`
- Create: `api/routes/ws.py`

- [ ] **Step 1: 创建目录和 schemas**

```bash
mkdir -p api/routes
touch api/__init__.py api/routes/__init__.py
```

**api/schemas.py**:

```python
from pydantic import BaseModel


class TaskCreateResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    current_step: str | None
    current_step_label: str
    error: str | None


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    pdf_url: str | None
    self_intro: str | None
    company_info: str | None
    error: str | None


class GenerateRequest(BaseModel):
    company_name: str = ""
```

- [ ] **Step 2: 编写 upload 路由**

**api/routes/upload.py**:

```python
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from config import config

router = APIRouter()


@router.post("/api/upload")
async def upload_files(
    resume: UploadFile = File(...),
    jd_image: UploadFile = File(...),
    company_name: str = Form(""),
):
    # Validate file types
    allowed_resume = {".pdf", ".docx"}
    allowed_image = {".png", ".jpg", ".jpeg", ".webp"}

    resume_ext = Path(resume.filename).suffix.lower()
    jd_ext = Path(jd_image.filename).suffix.lower()

    if resume_ext not in allowed_resume:
        raise HTTPException(400, f"不支持的简历格式: {resume_ext}，仅支持 PDF/DOCX")
    if jd_ext not in allowed_image:
        raise HTTPException(400, f"不支持的图片格式: {jd_ext}，仅支持 PNG/JPG/WEBP")

    # Check file size
    resume_content = await resume.read()
    jd_content = await jd_image.read()
    max_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024

    if len(resume_content) > max_bytes:
        raise HTTPException(400, f"简历文件超过 {config.MAX_FILE_SIZE_MB}MB 限制")
    if len(jd_content) > max_bytes:
        raise HTTPException(400, f"JD截图超过 {config.MAX_FILE_SIZE_MB}MB 限制")

    # Save to uploads
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    upload_id = str(uuid.uuid4())[:8]
    resume_path = os.path.join(config.UPLOAD_DIR, f"{upload_id}_resume{resume_ext}")
    jd_path = os.path.join(config.UPLOAD_DIR, f"{upload_id}_jd{jd_ext}")

    with open(resume_path, "wb") as f:
        f.write(resume_content)
    with open(jd_path, "wb") as f:
        f.write(jd_content)

    return {"upload_id": upload_id, "resume_path": resume_path, "jd_path": jd_path, "company_name": company_name}
```

- [ ] **Step 3: 编写 generate 路由**

**api/routes/generate.py**:

```python
import asyncio
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from api.schemas import GenerateRequest
from services.orchestrator import orchestrator

router = APIRouter()


@router.post("/api/generate/{upload_id}")
async def start_generation(upload_id: str, body: GenerateRequest):
    # Find uploaded files by upload_id
    from config import config

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
        "error": task.error,
    }


@router.get("/api/download/{task_id}")
async def download_pdf(task_id: str):
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务未找到")
    pdf_path = task.progress.get("pdf_path") or task.result.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF 文件未找到")
    return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
```

- [ ] **Step 4: 编写 WebSocket 路由**

**api/routes/ws.py**:

```python
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, task_id: str, ws: WebSocket):
        await ws.accept()
        if task_id not in self._connections:
            self._connections[task_id] = []
        self._connections[task_id].append(ws)

    def disconnect(self, task_id: str, ws: WebSocket):
        if task_id in self._connections:
            self._connections[task_id].remove(ws)

    async def broadcast(self, task_id: str, data: dict):
        if task_id in self._connections:
            message = json.dumps(data, ensure_ascii=False)
            for ws in self._connections[task_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(task_id, websocket)
    try:
        while True:
            # Keep connection alive, client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)
```

- [ ] **Step 5: 提交**

```bash
git add api/
git commit -m "feat: add API routes (upload, generate, status, download, websocket)"
```

---

### Task 11: 前端页面

**Files:**
- Create: `templates/pages/index.html`
- Create: `templates/pages/progress.html`
- Create: `templates/pages/result.html`

- [ ] **Step 1: 上传页 templates/pages/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Career-Sync Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-2xl mx-auto py-16 px-4">
        <h1 class="text-3xl font-bold text-center text-gray-900 mb-2">Career-Sync Agent</h1>
        <p class="text-center text-gray-500 mb-10">上传简历和岗位JD截图，AI自动为你生成定制化求职材料</p>

        <form id="upload-form" class="space-y-6 bg-white rounded-xl shadow-sm p-8">
            <!-- Resume Upload -->
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">原始简历 (PDF / Word)</label>
                <div id="resume-drop" class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 transition">
                    <input type="file" id="resume-input" accept=".pdf,.docx" class="hidden">
                    <p id="resume-hint" class="text-gray-400">拖拽或点击上传简历文件</p>
                    <p id="resume-name" class="text-blue-600 font-medium hidden"></p>
                </div>
            </div>

            <!-- JD Image Upload -->
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">岗位JD截图 (PNG / JPG)</label>
                <div id="jd-drop" class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 transition">
                    <input type="file" id="jd-input" accept=".png,.jpg,.jpeg,.webp" class="hidden">
                    <p id="jd-hint" class="text-gray-400">拖拽或点击上传JD截图</p>
                    <p id="jd-name" class="text-blue-600 font-medium hidden"></p>
                </div>
            </div>

            <!-- Company Name -->
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">目标公司名称</label>
                <input type="text" id="company-name" class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="如：字节跳动">
            </div>

            <!-- Submit -->
            <button type="submit" id="submit-btn" class="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 transition">
                开始生成
            </button>
        </form>
    </div>

    <script>
    function setupDrop(dropId, inputId, hintId, nameId) {
        const drop = document.getElementById(dropId);
        const input = document.getElementById(inputId);
        drop.addEventListener('click', () => input.click());
        drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('border-blue-400', 'bg-blue-50'); });
        drop.addEventListener('dragleave', () => drop.classList.remove('border-blue-400', 'bg-blue-50'));
        drop.addEventListener('drop', e => {
            e.preventDefault();
            drop.classList.remove('border-blue-400', 'bg-blue-50');
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                document.getElementById(hintId).classList.add('hidden');
                document.getElementById(nameId).classList.remove('hidden');
                document.getElementById(nameId).textContent = e.dataTransfer.files[0].name;
            }
        });
        input.addEventListener('change', () => {
            if (input.files.length) {
                document.getElementById(hintId).classList.add('hidden');
                document.getElementById(nameId).classList.remove('hidden');
                document.getElementById(nameId).textContent = input.files[0].name;
            }
        });
    }

    setupDrop('resume-drop', 'resume-input', 'resume-hint', 'resume-name');
    setupDrop('jd-drop', 'jd-input', 'jd-hint', 'jd-name');

    document.getElementById('upload-form').addEventListener('submit', async e => {
        e.preventDefault();
        const resume = document.getElementById('resume-input').files[0];
        const jd = document.getElementById('jd-input').files[0];
        if (!resume || !jd) { alert('请上传简历和JD截图'); return; }

        const btn = document.getElementById('submit-btn');
        btn.disabled = true;
        btn.textContent = '上传中...';

        const form = new FormData();
        form.append('resume', resume);
        form.append('jd_image', jd);
        form.append('company_name', document.getElementById('company-name').value);

        try {
            const res = await fetch('/api/upload', { method: 'POST', body: form });
            if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
            const data = await res.json();

            const genRes = await fetch(`/api/generate/${data.upload_id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company_name: data.company_name })
            });
            const genData = await genRes.json();
            window.location.href = `/progress/${genData.task_id}`;
        } catch (err) {
            alert('上传失败: ' + err.message);
            btn.disabled = false;
            btn.textContent = '开始生成';
        }
    });
    </script>
</body>
</html>
```

- [ ] **Step 2: 进度页 templates/pages/progress.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>处理中 - Career-Sync</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen flex items-center justify-center">
    <div class="max-w-lg w-full mx-4 bg-white rounded-xl shadow-sm p-8">
        <h2 class="text-xl font-semibold text-center mb-8">AI 正在为你生成求职材料</h2>

        <div id="steps" class="space-y-4">
            {% set steps = [
                ('M0_parse_resume', '解析简历文件'),
                ('M1_parse_jd', '识别JD岗位需求'),
                ('M2_generate', '生成适配简历'),
                ('M3_intelligence', '搜索公司情报'),
                ('render_pdf', '导出PDF文件'),
            ] %}
            {% for step_id, label in steps %}
            <div id="step-{{ step_id }}" class="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
                <div class="step-icon w-8 h-8 flex items-center justify-center rounded-full bg-gray-200 text-gray-500 text-sm font-medium">{{ loop.index }}</div>
                <span class="text-gray-600">{{ label }}</span>
                <div class="step-spinner ml-auto hidden w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <div class="step-check ml-auto hidden text-green-500 text-lg">&#10003;</div>
                <div class="step-error ml-auto hidden text-red-500 text-lg">&#10007;</div>
            </div>
            {% endfor %}
        </div>

        <p id="error-msg" class="mt-6 text-red-500 text-center hidden"></p>
        <button id="retry-btn" onclick="location.reload()" class="mt-4 w-full bg-blue-600 text-white py-2 rounded-lg hidden hover:bg-blue-700">重试</button>
    </div>

    <script>
    const taskId = window.location.pathname.split('/').pop();
    const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProtocol}//${location.host}/ws/${taskId}`);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateStep(data.current_step);
        if (data.status === 'completed') {
            window.location.href = `/result/${taskId}`;
        } else if (data.status === 'failed') {
            document.getElementById('error-msg').textContent = '生成失败: ' + (data.error || '未知错误');
            document.getElementById('error-msg').classList.remove('hidden');
            document.getElementById('retry-btn').classList.remove('hidden');
        }
    };

    function updateStep(step) {
        const steps = ['M0_parse_resume', 'M1_parse_jd', 'M2_generate', 'M3_intelligence', 'render_pdf'];
        let found = false;
        steps.forEach(s => {
            const el = document.getElementById('step-' + s);
            if (s === step) {
                found = true;
                el.querySelector('.step-icon').classList.replace('bg-gray-200', 'bg-blue-500');
                el.querySelector('.step-icon').classList.replace('text-gray-500', 'text-white');
                el.querySelector('.step-spinner').classList.remove('hidden');
                el.querySelector('.step-check').classList.add('hidden');
            } else if (found) {
                // Future steps, unchanged
            } else {
                // Completed steps
                el.querySelector('.step-icon').classList.replace('bg-gray-200', 'bg-green-500');
                el.querySelector('.step-icon').classList.replace('text-gray-500', 'text-white');
                el.querySelector('.step-spinner').classList.add('hidden');
                el.querySelector('.step-check').classList.remove('hidden');
            }
        });
    }

    ws.onclose = () => { /* Reconnect logic if needed */ };
    ws.onerror = () => document.getElementById('error-msg').classList.remove('hidden');
    </script>
</body>
</html>
```

- [ ] **Step 3: 结果页 templates/pages/result.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>生成结果 - Career-Sync</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-4xl mx-auto py-10 px-4">
        <h1 class="text-2xl font-bold text-center mb-10">你的求职材料已生成</h1>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- PDF Resume Card -->
            <div class="bg-white rounded-xl shadow-sm p-6 text-center">
                <div class="text-4xl mb-3">&#128196;</div>
                <h3 class="font-semibold mb-2">定制化简历 PDF</h3>
                <p class="text-sm text-gray-500 mb-4">已根据JD关键词优化</p>
                <a id="pdf-download" href="#" class="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">下载 PDF</a>
            </div>

            <!-- Self Intro Card -->
            <div class="bg-white rounded-xl shadow-sm p-6 text-center">
                <div class="text-4xl mb-3">&#128483;</div>
                <h3 class="font-semibold mb-2">面试自我介绍</h3>
                <p class="text-sm text-gray-500 mb-4">基于STAR法则，3分钟版本</p>
                <button onclick="showModal('intro')" class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">查看 & 复制</button>
            </div>

            <!-- Company Report Card -->
            <div class="bg-white rounded-xl shadow-sm p-6 text-center">
                <div class="text-4xl mb-3">&#128270;</div>
                <h3 class="font-semibold mb-2">公司深度情报</h3>
                <p class="text-sm text-gray-500 mb-4">面试谈资 + 技术动态</p>
                <button onclick="showModal('company')" class="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700">查看 & 复制</button>
            </div>
        </div>

        <!-- Modal -->
        <div id="modal" class="fixed inset-0 bg-black/50 hidden items-center justify-center z-50">
            <div class="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 id="modal-title" class="text-lg font-semibold"></h3>
                    <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
                </div>
                <pre id="modal-content" class="text-sm text-gray-700 whitespace-pre-wrap font-sans"></pre>
                <button onclick="copyContent()" class="mt-4 w-full bg-gray-100 py-2 rounded-lg hover:bg-gray-200">复制内容</button>
            </div>
        </div>
    </div>

    <script>
    const taskId = window.location.pathname.split('/').pop();

    fetch(`/api/result/${taskId}`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('pdf-download').href = data.pdf_url || '#';
            window._intro = data.self_intro || '';
            window._company = data.company_info || '';
        });

    function showModal(type) {
        const modal = document.getElementById('modal');
        const title = document.getElementById('modal-title');
        const content = document.getElementById('modal-content');
        if (type === 'intro') {
            title.textContent = '面试自我介绍';
            content.textContent = window._intro;
        } else {
            title.textContent = '公司深度情报';
            content.textContent = window._company;
        }
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    function closeModal() {
        const modal = document.getElementById('modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    function copyContent() {
        navigator.clipboard.writeText(document.getElementById('modal-content').textContent);
        alert('已复制到剪贴板');
    }
    </script>
</body>
</html>
```

- [ ] **Step 4: 提交**

```bash
git add templates/pages/
git commit -m "feat: add frontend pages (upload, progress, result)"
```

---

### Task 12: FastAPI 主入口 & 集成

**Files:**
- Create: `main.py`

- [ ] **Step 1: 编写 main.py**

```python
import logging
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from config import config
from services.orchestrator import orchestrator, Task
from api.routes.ws import manager as ws_manager
from api.routes import upload, generate, ws

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs("templates/pages", exist_ok=True)
    os.makedirs("templates/resumes", exist_ok=True)

    # Register WebSocket progress callback
    async def ws_callback(task: Task):
        await ws_manager.broadcast(task.id, task.to_dict())

    orchestrator.register_progress_callback(ws_callback)
    yield


app = FastAPI(title="Career-Sync Agent", lifespan=lifespan)

# Routes
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(ws.router)

# Templates
templates = Jinja2Templates(directory="templates/pages")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/progress/{task_id}")
async def progress_page(request: Request, task_id: str):
    steps = [
        ("M0_parse_resume", "解析简历文件"),
        ("M1_parse_jd", "识别JD岗位需求"),
        ("M2_generate", "生成适配简历"),
        ("M3_intelligence", "搜索公司情报"),
        ("render_pdf", "导出PDF文件"),
    ]
    return templates.TemplateResponse("progress.html", {"request": request, "task_id": task_id, "steps": steps})


@app.get("/result/{task_id}")
async def result_page(request: Request, task_id: str):
    return templates.TemplateResponse("result.html", {"request": request, "task_id": task_id})


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 2: 修复 progress.html 中的 Jinja2 变量引用**

之前的 progress.html 硬编码了 steps，现在改为从后端传入。需要编辑 `templates/pages/progress.html`，将硬编码的 steps 列表改为使用 `{{ steps }}` Jinja2 变量。修正如下：

```bash
# The progress.html already uses steps from the Jinja2 context correctly.
# Verify:
source venv/Scripts/activate && python -c "from main import app; print('FastAPI ready')"
```

- [ ] **Step 3: 启动并验证**

```bash
source venv/Scripts/activate && python main.py
# Visit http://localhost:8000 in browser
# Visit http://localhost:8000/api/health -> {"status":"ok"}
```

- [ ] **Step 4: 提交**

```bash
git add main.py
git commit -m "feat: add FastAPI main entry point with all routes"
```

---

### Task 13: 端到端集成测试

**Files:**
- Create: `tests/test_api.py`

- [ ] **Step 1: 编写集成测试 test_api.py**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_index_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "Career-Sync" in resp.text


@pytest.mark.asyncio
async def test_upload_rejects_invalid_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {
            "resume": ("test.txt", b"not a resume", "text/plain"),
            "jd_image": ("jd.png", b"fake png", "image/png"),
        }
        resp = await client.post("/api/upload", files=files, data={"company_name": "test"})
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_status_404_for_unknown_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/status/nonexistent")
        assert resp.status_code == 404
```

- [ ] **Step 2: 运行集成测试**

```bash
source venv/Scripts/activate && pip install httpx && pytest tests/test_api.py -v
```
Expected: 4 PASS

- [ ] **Step 3: 提交**

```bash
git add tests/test_api.py
git commit -m "test: add API integration tests"
```

---

### Task 14: 最终检查与文档

- [ ] **Step 1: 确认最终项目结构**

```bash
cd "G:/求职助手Agent" && find . -not -path './venv/*' -not -path './.git/*' -not -path './__pycache__/*' -not -name '*.pyc' | sort
```

Expected structure:
```
.
├── .env.example
├── .gitignore
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── generate.py
│   │   ├── upload.py
│   │   └── ws.py
│   └── schemas.py
├── config.py
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-15-career-sync-agent-design.md
├── llm/
│   ├── __init__.py
│   ├── client.py
│   ├── fallback.py
│   └── prompts.py
├── main.py
├── requirements.txt
├── search/
│   ├── __init__.py
│   └── tavily.py
├── services/
│   ├── __init__.py
│   ├── generator.py
│   ├── orchestrator.py
│   ├── parser.py
│   └── renderer.py
├── templates/
│   ├── pages/
│   │   ├── index.html
│   │   ├── progress.html
│   │   └── result.html
│   └── resumes/
│       └── modern.html
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_generator.py
│   ├── test_llm_client.py
│   ├── test_llm_fallback.py
│   ├── test_parser.py
│   ├── test_renderer.py
│   └── test_tavily.py
└── worker.py
```

- [ ] **Step 2: 运行全部测试**

```bash
source venv/Scripts/activate && python -m pytest tests/ -v
```
Expected: All tests PASS

- [ ] **Step 3: 最终提交**

```bash
git add -A && git commit -m "chore: finalize project structure and verify all tests pass"
```

---

## 实现顺序

```
Task 1 (脚手架) → Task 2 (配置) → Task 3 (LLM客户端) → Task 4 (Prompt/Fallback)
    → Task 5 (简历解析) → Task 6 (内容生成+模板) → Task 7 (PDF渲染)
    → Task 8 (Tavily搜索) → Task 9 (编排器) → Task 10 (API路由)
    → Task 11 (前端页面) → Task 12 (主入口) → Task 13 (集成测试) → Task 14 (最终检查)
```
