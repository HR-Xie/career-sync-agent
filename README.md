# CareerSync Agent - 智能求职助手

> 输入简历 + JD 截图，AI 全自动生成定制化 PDF 简历、面试自我介绍和公司深度情报。

<p align="center">
  <img src="docs/screenshots/01-upload.png" alt="Upload Page" width="80%">
</p>

## 功能

| 模块 | 功能 | 说明 |
|------|------|------|
| M0 简历解析 | PDF/Word → 结构化 JSON | PyMuPDF + python-docx 提取，DeepSeek V4 Pro 结构化 |
| M1 JD 识别 | 截图 → 岗位关键词 | Kimi k2.6 多模态视觉 API 解析 BOSS/猎聘截图 |
| M2 内容生成 | 简历对齐 + PDF 导出 | DeepSeek 重写经历 (STAR 法则)，Playwright 渲染 PDF |
| M3 面试辅助 | 自我介绍 + 公司情报 | Tavily 搜索公司动态，DeepSeek 生成 3 分钟话术 |

<p align="center">
  <img src="docs/screenshots/02-result.png" alt="Result Page" width="80%">
</p>

## 技术栈

```
Python 3.10+  |  FastAPI  |  Jinja2  |  Tailwind CSS
DeepSeek V4 Pro  |  Kimi k2.6  |  Tavily Search
PyMuPDF  |  python-docx  |  Pillow  |  Playwright
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/HR-Xie/career-sync-agent.git
cd career-sync-agent
```

### 2. 安装依赖

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
playwright install chromium
```

### 3. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key:
#   DEEPSEEK_API_KEY=sk-xxx    (必填 - 简历解析/内容生成)
#   KIMI_API_KEY=sk-xxx        (必填 - JD截图识别)
#   TAVILY_API_KEY=tvly-xxx    (可选 - 公司情报搜索)
```

### 4. 启动

```bash
python main.py
# 浏览器打开 http://localhost:8000
```

### 5. 使用

1. 上传原始简历（PDF 或 Word）
2. 上传目标岗位的 JD 截图
3. 填写目标公司名称
4. 点击"开始生成"，等待 AI 处理
5. 下载定制化 PDF 简历，查看面试材料和公司情报

## 项目结构

```
career-sync-agent/
├── main.py                 # FastAPI 入口
├── config.py               # 环境变量配置
├── worker.py               # 异步任务 Worker
├── api/routes/             # REST API + WebSocket
│   ├── upload.py           # 文件上传
│   ├── generate.py         # 任务生成/状态/下载
│   └── ws.py               # 实时进度推送
├── services/               # 核心服务层
│   ├── parser.py           # 简历解析 + 图片压缩
│   ├── generator.py        # 内容生成 + Jinja2 渲染
│   ├── renderer.py         # Playwright PDF 导出
│   └── orchestrator.py     # M0→M3 流水线编排
├── llm/                    # LLM 层
│   ├── client.py           # OpenAI 兼容接口
│   ├── fallback.py         # 多模型路由/重试
│   └── prompts.py          # Prompt 模板
├── search/tavily.py        # 公司情报搜索
├── templates/
│   ├── pages/              # 前端页面 (Tailwind CSS)
│   └── resumes/            # 简历 HTML 模板
└── tests/                  # 25 个测试用例
```

## 模型分工

| 任务 | 模型 | 策略 |
|------|------|------|
| 文本生成（简历解析/重写/话术） | DeepSeek V4 Pro | 主力，Kimi 备选 |
| 视觉识别（JD 截图解析） | Kimi k2.6 | 主力，无备选 |

## License

MIT
