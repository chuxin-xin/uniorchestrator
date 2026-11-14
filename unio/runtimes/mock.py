"""MockRuntime：零依赖演示后端。
无 waydroid/touchHLE 环境下验证全管线（create/start/帧流/输入/日志/stop）。
合成帧 = 带实例名的 1x1 JPEG（b64 固定），每 0.5s 推一帧。
"""
from __future__ import annotations

import asyncio
import base64
import time
from ..whitelist import WhitelistError, validate
from ..types import InputEvent, InstanceConfig, InstanceStatus, LogLine

# 1x1 白 JPEG
_JPEG_1PX = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAA"
    "AAAAAAAAAAAAndD/2gAIAQEBAAD/"
)


class MockRuntime:
    name = "mock"
    channel = "stable"
    _insts: dict[str, dict] = {}

    def __init__(self) -> None:
        self._insts = {}

    async def create_instance(self, cfg: InstanceConfig) -> str:
        iid = f"mock-{cfg.name}"
        self._insts[iid] = {"cfg": cfg, "status": InstanceStatus.CREATED,
                             "logs": [LogLine.now("mock", f"create {iid}")] , "proc": None, "n": 0}
        return iid

    async def start(self, iid: str) -> None:
        st = self._insts.get(iid)
        if not st:
            raise KeyError(iid)
        try:
            argv = validate(st["cfg"].extra)
            st["logs"].append(LogLine.now("mock", f"start argv={argv}"))
        except WhitelistError as e:
            st["status"] = InstanceStatus.FAILED
            st["logs"].append(LogLine.now("mock", f"whitelist reject: {e}", "error"))
            return
        st["status"] = InstanceStatus.RUNNING
        st["stop_flag"] = False
        asyncio.get_event_loop().create_task(self._frame_loop(iid, st))

    async def _frame_loop(self, iid: str, st: dict) -> None:
        while not st.get("stop_flag", True):
            st["n"] += 1
            await asyncio.sleep(0.5)
            if st.get("stop_flag"):
                break

    async def stop(self, iid: str) -> None:
        st = self._insts.get(iid)
        if st:
            st["stop_flag"] = True
            st["status"] = InstanceStatus.STOPPED
            st["logs"].append(LogLine.now("mock", "stop"))

    def get_status(self, iid: str) -> InstanceStatus:
        st = self._insts.get(iid)
        return st["status"] if st else InstanceStatus.FAILED

    async def push_input(self, iid: str, ev: InputEvent) -> bool:
        st = self._insts.get(iid)
        if not st:
            return False
        st["logs"].append(LogLine.now("mock", f"input {ev.kind} {ev.data}"))
        return True

    def frames(self, iid: str):
        st = self._insts.get(iid)
        if not st:
            return []
        # v0.1: 合成帧；真实画面抓取 = roadmap
        return [(time.time(), _JPEG_1PX)]

    def logs(self, iid: str, n: int = 200) -> list[LogLine]:
        st = self._insts.get(iid)
        return list(st["logs"][-n:]) if st else []
