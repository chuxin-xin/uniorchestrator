"""API 网关（交付件 4）：REST + WebSocket + 内嵌面板。
v0.1 = FastAPI（Rust 迁移目标 Axum，路由表逐一对应）。
鉴权：v1 默认仅绑 127.0.0.1（见 docs/08-security.md），令牌鉴权 = roadmap。
"""
from __future__ import annotations

import asyncio
import base64
import os
import time

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .registry import PluginRegistry
from .scheduler import Scheduler
from .types import InstanceConfig, InstanceStatus, InputEvent, ResourceQuota, WindowConfig

REGISTRY = PluginRegistry()
SCHED = Scheduler(REGISTRY)

app = FastAPI(title="UniOrchestrator", version="0.1.0")

_WEB = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")


class QuotaIn(BaseModel):
    cpu: int = 200_000
    mem_mb: int = 512


class WindowIn(BaseModel):
    width: int = 640
    height: int = 960
    orientation: str = "portrait"
    fullscreen: bool = False


class StartIn(BaseModel):
    runtime: str = "mock"
    name: str = "demo"
    app: str = ""
    extra: dict = {}
    quota: QuotaIn | None = None
    window: WindowIn | None = None


class StopIn(BaseModel):
    instance_id: str


class InputIn(BaseModel):
    kind: str
    data: dict = {}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_WEB)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "version": app.version}


@app.get("/runtime/plugins")
def plugins() -> list[dict]:
    return REGISTRY.list()


@app.post("/instance/start")
async def instance_start(body: StartIn) -> dict:
    try:
        cfg = InstanceConfig(
            name=body.name,
            runtime=body.runtime,
            app=body.app,
            extra=body.extra,
            quota=ResourceQuota(cpu_quota_us=body.quota.cpu,
                                mem_max_bytes=body.quota.mem_mb * 1024 * 1024) if body.quota else ResourceQuota(),
            window=WindowConfig(width=body.window.width, height=body.window.height,
                                orientation=body.window.orientation,
                                fullscreen=body.window.fullscreen) if body.window else WindowConfig(),
        )
        iid = await SCHED.create(cfg)
        st = await SCHED.start(iid)
        return {"instance_id": iid, "status": st.value}
    except KeyError as e:
        raise HTTPException(404, f"runtime not available: {e}")


@app.post("/instance/stop")
async def instance_stop(body: StopIn) -> dict:
    try:
        await SCHED.stop(body.instance_id)
        return {"instance_id": body.instance_id, "status": "stopped"}
    except KeyError:
        raise HTTPException(404, "unknown instance")


@app.get("/instance/list")
def instance_list() -> list[dict]:
    return SCHED.list_instances()


@app.get("/instance/{iid}/logs")
def instance_logs(iid: str, n: int = 200) -> list[dict]:
    cfg = SCHED.index.get(iid)
    if not cfg:
        raise HTTPException(404, "unknown instance")
    lines = REGISTRY.get(cfg.runtime).logs(iid, n)
    return [{"ts": l.ts, "level": l.level, "source": l.source, "msg": l.msg} for l in lines]


@app.post("/instance/{iid}/input")
async def instance_input(iid: str, body: InputIn) -> dict:
    try:
        cfg = SCHED.index.get(iid)
        if not cfg:
            raise KeyError(iid)
    except KeyError:
        raise HTTPException(404, "unknown instance")
    ok = await SCHED.push_input(iid, InputEvent(kind=body.kind, data=body.data))
    if not ok:
        raise HTTPException(409, "instance not running (input not queued)")
    return {"accepted": True}


@app.websocket("/instance/{iid}/stream")
async def instance_stream(ws: WebSocket, iid: str) -> None:
    await ws.accept()
    cfg = SCHED.index.get(iid)
    if not cfg:
        await ws.close(code=4004)
        return
    rt = REGISTRY.get(cfg.runtime)
    try:
        while True:
            frames = rt.frames(iid)
            if frames:
                ts, jpeg = frames[0] if isinstance(frames, list) else None
                if jpeg is not None:
                    await ws.send_json({"ts": ts, "frame": base64.b64encode(jpeg).decode()})
                else:
                    await ws.send_json({"ts": time.time(), "frame": None, "note": "frame source not wired in v0.1"})
            else:
                await ws.send_json({"ts": time.time(), "frame": None})
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
