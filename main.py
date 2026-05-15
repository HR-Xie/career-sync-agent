import logging
import os

from fastapi import FastAPI, Request
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
    return templates.TemplateResponse(request, "index.html")


@app.get("/progress/{task_id}")
async def progress_page(request: Request, task_id: str):
    return templates.TemplateResponse(request, "progress.html", {"task_id": task_id})


@app.get("/result/{task_id}")
async def result_page(request: Request, task_id: str):
    return templates.TemplateResponse(request, "result.html", {"task_id": task_id})


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
