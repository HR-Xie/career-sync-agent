1. # Career-Sync Agent (Job-Hunt Copilot) 开发需求说明书 (Python 版)

   ## 1. 项目概览

   - **项目名称**：Career-Sync Agent
   - **核心功能**：输入“JD 截图”+“Word/PDF 原始简历”，全自动生成：
     1. **定制化 PDF 简历**（适配目标岗位关键词）。
     2. **面试自我介绍**（基于 STAR 法则）。
     3. **公司深度情报**（面试谈资）。
   - **核心大脑**：DeepSeek-V4Pro
   - **开发语言**：Python 3.10+
   - **开发工具**：Claude Code

   ## 2. 核心技术栈选型 (Python 生态)

   为了让 Claude Code 高效实现功能，项目将采用以下 Python 库：

   - **环境与请求**：`python-dotenv` (环境变量), `requests` 或 `httpx` (API 调用)
   - **文档解析 (Ingestion)**：
     - PDF 解析：`PyMuPDF` (即 `fitz`，提取速度快且精准)
     - Word 解析：`python-docx`
   - **图像预处理 (Vision)**：`Pillow` (用于压缩 JD 截图，控制传给视觉大模型的图片体积)
   - **简历渲染 (PDF Generation)**：`playwright` (Python 版) + HTML/Tailwind CSS。利用 Headless 浏览器将前端模板精准打印为 PDF。
   - **搜索增强 (RAG/Search)**：`tavily-python` (用于抓取公司动态)

   ## 3. 详细业务流程与模块 (Workflow)

   ### M0: 简历摄取与结构化 (Resume Ingestion)

   - **动作**：读取用户的 `.docx` 或 `.pdf` 原始简历。
   - **逻辑**：使用 `PyMuPDF` 或 `python-docx` 提取纯文本。
   - **AI 介入**：调用 DeepSeek 将排版混乱的文本转化为标准的 JSON Schema（包含教育、论文、科研项目、工程落地经验）。

   ### M1: 多模态 JD 解析 (Visual Parser)

   - **动作**：读取用户提供的 BOSS 直聘等平台的 JD 截图。
   - **逻辑**：使用 `Pillow` 将图片等比例压缩（宽度控制在 1080px 内），转为 Base64。
   - **AI 介入**：调用具备视觉能力的大模型 API（或专业 OCR API），提取出“岗位名称”、“核心技术栈”与“业务场景”。

   ### M2: 经历对齐与生成 (Alignment & Generation)

   - **动作**：基于 JD 需求重写简历，并导出文件。
   - **AI 介入**：DeepSeek 接收结构化简历 JSON 和 JD 关键词，针对性地高亮和改写项目经历（如优化水下目标检测的表述以迎合算法岗需求）。
   - **逻辑**：将改写后的内容注入预先写好的 HTML 模板中，调用 `playwright` 的 `page.pdf()` 方法导出为高精度的 PDF 文件。

   ### M3: 面试情报局 (Intelligence & Prep)

   - **动作**：生成面试辅助材料。
   - **逻辑**：调用 Tavily API 搜索目标公司的近期融资、核心产品线及技术分享。
   - **AI 介入**：结合公司情报与改写后的简历，生成一份 3 分钟的口语化自我介绍。

   ------

   ## 4. Claude Code 初始执行指令 (Initial Prompt)

   你可以将以下内容直接复制给 Claude Code，让它自动帮你搭建起 Python 项目框架：

   > "Claude，你是我的高级 Python 架构师。我们要开发一个名为 Career-Sync Agent 的求职助手程序。请按照以下步骤执行：
   >
   > 1. **环境初始化**：
   >    - 创建一个 Python 虚拟环境 (venv)。
   >    - 生成 `requirements.txt`，包含以下依赖：`python-dotenv`, `httpx`, `PyMuPDF`, `python-docx`, `Pillow`, `playwright`, `tavily-python`, `jinja2` (用于 HTML 模板渲染)。
   >    - 提示我运行 `playwright install chromium` 来安装浏览器内核。
   >    - 创建 `.env` 文件模板，预留 `DEEPSEEK_API_KEY` 和 `TAVILY_API_KEY`。
   > 2. **核心解析工具 (utils/parser.py)**：
   >    - 编写 PDF 和 Word 的文本提取函数。
   >    - 编写图片压缩并转 Base64 的函数。
   > 3. **AI 交互层 (llm/agent.py)**：
   >    - 编写与 DeepSeek API 交互的逻辑。
   >    - 编写 prompt，将提取出的简历文本清洗为结构化的 JSON 数据。
   > 4. **PDF 渲染器 (core/renderer.py)**：
   >    - 使用 Jinja2 将生成的 JSON 数据注入到一个基于 Tailwind CSS 的 HTML 模板中。
   >    - 使用 Playwright 编写一个异步函数，将渲染好的 HTML 保存为 PDF 文件。
   >
   > 请先从第 1 步的环境初始化和生成 `requirements.txt` 开始。"

   ------

   ## 5. 架构师的私房建议 (Python 版避坑指南)

   1. **模板引擎的选择**：在 Python 里拼接 HTML 字符串很容易出错，我为你加入了 `Jinja2`。你可以把带有 Tailwind 类名的 HTML 写在一个单独的 `.html` 文件里，用双大括号 `{{ project.name }}` 留出占位符，这样逻辑和视图完全分离，代码极其优雅。
   2. **Playwright 的异步特性**：Python 版的 Playwright 有同步和异步两种 API。建议让 Claude Code 默认使用 `asyncio` 和异步版 Playwright，这样在你后续如果想把它封装成一个 FastAPI 后端服务（加个简单的网页前端）时，性能会好很多。
   3. **视觉 API 替代方案**：如果你发现传图片给大模型比较贵或速度慢，可以直接在 Python 里 pip 安装 `paddleocr`，本地跑一个轻量级的 OCR 模型，这对你这个做 CV 的人来说应该是秒级部署的事。