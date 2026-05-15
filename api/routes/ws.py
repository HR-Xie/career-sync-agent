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
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)
