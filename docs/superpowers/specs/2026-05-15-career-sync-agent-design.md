# Career-Sync Agent (Job-Hunt Copilot) 架构设计文档

**日期**: 2026-05-15  
**版本**: v1.0  
**状态**: 已确认

---

## 1. 项目概览

- **项目名称**：Career-Sync Agent
- **核心功能**：输入 JD 截图 + Word/PDF 原始简历，全自动生成：
  1. 定制化 PDF 简历（适配目标岗位关键词）
  2. 面试自我介绍（基于 STAR 法则）
  3. 公司深度情报（面试谈资）
- **开发语言**：Python 3.10+
- **交互方式**：FastAPI + Web 前端
- **核心 LLM**：DeepSeek V4 Pro（主力）+ Kimi-2.6（备选 fallback）

## 2. 技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 语言 | Python 3.10+ | 用户偏好，PDF/Word/OCR 生态成熟 |
| 框架 | FastAPI + Jinja2 | 异步原生支持，WebSocket 开箱即用 |
| PDF 解析 | PyMuPDF (fitz) | 速度快，提取精准 |
| Word 解析 | python-docx | 标准方案 |
| 图片处理 | Pillow | JPEG 压缩，等比缩放 |
| OCR | DeepSeek/Kimi 视觉 API | 无需本地模型，直接图文理解 |
| PDF 渲染 | Playwright + Jinja2 + Tailwind CSS | Headless 浏览器精准转换为 PDF |
| 搜索 | Tavily API | 公司动态抓取 |
| RAG | 暂不引入 | 当前流程无向量检索需求，后续按需加入 Milvus |
| 前端 | Jinja2 SSR + WebSocket + Tailwind CSS (CDN) | 不引入 SPA 框架，保持轻量 |
| 测试 | pytest + pytest-asyncio | Python 标准测试栈 |

## 3. 架构概览

采用分层 FastAPI 架构：

```
career-sync-agent/
├── main.py                 # FastAPI 入口 + 生命周期管理
├── config.py               # 配置中心 (env, model选择)
├── api/
│   ├── routes/
│   │   ├── upload.py       # 文件上传
│   │   ├── generate.py     # 任务创建/查询/下载
│   │   └── ws.py           # WebSocket 进度推送
│   └── schemas.py          # Pydantic 请求/响应模型
├── services/
│   ├── parser.py           # PDF/Word/图片 解析服务
│   ├── orchestrator.py     # 工作流编排 (M0→M1→M2→M3)
│   ├── generator.py        # 内容生成服务
│   └── renderer.py         # Playwright PDF 渲染
├── llm/
│   ├── client.py           # DeepSeek + Kimi 统一 API 客户端
│   ├── prompts.py          # Prompt 模板管理
│   └── fallback.py         # 重试 + DeepSeek→Kimi 切换
├── search/
│   └── tavily.py           # Tavily 公司情报搜索
├── templates/
│   ├── pages/              # 网站页面模板
│   └── resumes/            # 简历 HTML 模板
├── static/                 # 前端资产
├── worker.py               # 异步任务 worker
└── uploads/ / output/      # 临时文件 / 产物
```

## 4. 数据流

```
用户上传 (JD截图 + 简历文件)
        │
        ▼
   ┌─────────────┐
   │  FastAPI     │   前端: 上传 → 进度 → 预览 → 下载
   │  Routes      │
   └──────┬──────┘
          │ 创建任务, task_id
          ▼
   ┌─────────────┐
   │  Worker      │   asyncio 异步执行
   │              │   WebSocket 实时推送每步进度
   └──────┬──────┘
          │
    ┌─────┴─────┬─────────┬─────────┐
    ▼           ▼         ▼         ▼
  M0:解析    M1:JD识别   M2:生成   M3:情报
  ────────   ─────────  ────────  ────────
  PyMuPDF    VisionAPI   DeepSeek  Tavily
  python-docx LLM         重写对齐   自我介绍
    │           │         │         │
    ▼           ▼         ▼         ▼
  profile.json JD关键词  HTML简历  company.md
    └───────────┴────┬────┴─────────┘
                     │
                     ▼
              ┌─────────────┐
              │  Playwright  │  → output/Resume_TargetCompany.pdf
              │  PDF 渲染    │
              └─────────────┘
```

## 5. 模块详细设计

### M0: 简历解析 (services/parser.py)

- 输入: `.pdf` 或 `.docx` 文件路径
- 输出: `profile.json`（结构化简历）
- 实现: PyMuPDF / python-docx 提取文本 → 正则清洗多余换行 → DeepSeek 转为 JSON Schema

```json
{
  "name": "", "email": "", "phone": "",
  "education": [{"school": "", "degree": "", "major": "", "year": ""}],
  "skills": ["Python", "PyTorch"],
  "experience": [{"company": "", "role": "", "duration": "", "highlights": []}],
  "projects": [{"name": "", "desc": "", "tech_stack": [], "achievements": []}],
  "papers": [{"title": "", "venue": "", "year": ""}]
}
```

### M1: JD 解析 (services/parser.py + llm/)

- 输入: JD 截图 (png/jpg)
- 输出: `jd_keywords.json` `{"title":"", "skills":[], "biz_focus":"", "must_have":[], "nice_to_have":[]}`
- 实现: Pillow 压缩(宽度≤1080px) → Base64 → 视觉 API → fallback 到 Kimi

### M2: 内容生成 (services/generator.py)

- 输入: profile.json + jd_keywords.json
- 输出: tailored_resume.json + HTML 字符串
- 实现: DeepSeek 对齐重写 → Jinja2 + Tailwind 渲染 HTML → Playwright 异步输出 PDF

### M3: 面试辅助 (services/generator.py + search/tavily.py)

- 输入: jd_keywords.json + tailored_resume.json
- 输出: self_intro.md + company_report.md
- 实现: Tavily 搜索 → DeepSeek 生成 STAR 自我介绍

### LLM 层 (llm/)

```
llm/
├── client.py     # call(prompt, model="deepseek") 统一接口
├── prompts.py    # System Prompt 集中管理
└── fallback.py   # 3次重试 + 自动切 Kimi
```

### Worker (worker.py)

- asyncio 单线程异步执行
- 每步完成更新内存状态 → WebSocket 广播进度
- 支持单步重试（失败不从头开始）

## 6. 前端设计

- **技术**: Jinja2 SSR + Tailwind CSS (CDN) + 原生 WebSocket
- **页面**: index(上传) → progress(进度) → result(结果)

```
Upload → 提交 → Progress (M0→M1→M2→M3 流水线动画) → Result (PDF预览+下载)
```

- 上传页: 拖拽上传区 + 公司名输入
- 进度页: 4 步流水线，每步亮灯 + 文字提示，失败标红
- 结果页: 三卡片 — PDF 简历预览、自我介绍、公司报告

## 7. 错误处理

- **解析失败**: 文件格式校验（魔数检测），损坏文件拒绝
- **LLM 失败**: 3 次重试 → DeepSeek→Kimi 切换 → 额度告警
- **渲染失败**: Playwright 超时 30s kill，进程守护
- **全局**: try/except 在 service 层，route 层纯转发
- **前端**: WebSocket 推送失败步骤，支持单步重试

## 8. 测试策略

| 层级 | 测什么 | 怎么测 |
|------|--------|--------|
| parser | PDF/Word 文本提取 | 3 份真实简历固定输入 |
| llm/client | API 调用 + fallback | mock API 返回 |
| generator | Jinja2 模板输出 | 固定 json 断言 HTML |
| renderer | HTML→PDF 生成 | 断言文件存在且 >1KB |
| routes | HTTP 状态码 + schema | FastAPI TestClient |

- 框架: pytest + pytest-asyncio
- LLM 层 mock，不烧 token
- 目标: 核心路径全覆盖

## 9. 依赖清单 (requirements.txt)

```
python-dotenv
httpx
PyMuPDF
python-docx
Pillow
playwright
tavily-python
jinja2
fastapi
uvicorn
websockets
pydantic
python-multipart
aiofiles
pytest
pytest-asyncio
openai
```
