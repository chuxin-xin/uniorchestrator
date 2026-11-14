"""AndroidRuntime（stable）：waydroid 子进程托管。
- 上游（waydroid/LXC/Android 容器镜像）由用户自备，框架只 spawn，不复制不链接
- 二进制缺失 → 实例降级 missing_binary（可诊断，不 500）
- 输入转发走 `waydroid adb input ...`（waydroid 官方 adb 代理）
- 画面帧流：waydroid 窗口为原生自绘，无帧 API → v1 返回空流 + TODO（roadmap）
"""
from __future__ import annotations

import asyncio
import os
import shutil
import time
from ..types import AppRuntime, InputEvent, InstanceConfig, InstanceStatus, LogLine
from ..whitelist import WhitelistError

_BIN = os.environ.get("UNIO_WAYDROID_BIN", "waydroid")


def _have_waydroid() -> bool:
    return shutil.which(_BIN) is not None


class AndroidRuntime:
    name = "android"
    channel = "stable"

    def __init__(self) -> None:
        self._insts: dict[str, dict] = {}

    async def create_instance(self, cfg: InstanceConfig) -> str:
        if not _have_waydroid():
            # 登记但置降级态；start 时返回可诊断失败
            pass
        iid = f"android-{cfg.name}"
        self._insts[iid] = {
            "cfg": cfg,
            "status": InstanceStatus.MISSING_BIN if not _have_waydroid() else InstanceStatus.CREATED,
            "logs": [LogLine.now("android", f"create {iid} bin={'ok' if _have_waydroid() else 'MISSING'}")],
            "proc": None,
        }
        return iid

    async def start(self, iid: str) -> None:
        st = self._insts.get(iid)
        if not st:
            raise KeyError(iid)
        if st["status"] == InstanceStatus.MISSING_BIN:
            st["logs"].append(LogLine.now("android", "start refused: waydroid not found; install upstream (external dependency)", "error"))
            return
        cfg = st["cfg"]
        # 启动前需用户已 `waydroid init`（上游自备，框架不代下载）
        cmd = [_BIN, "session", "launch"]
        if cfg.window.fullscreen:
            cmd.append("--show-window")
        if cfg.app:
            cmd += ["--", cfg.app]
        st["logs"].append(LogLine.now("android", f"spawn: {' '.join(cmd)}"))
        try:
            st["proc"] = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            st["status"] = InstanceStatus.RUNNING
        except Exception as e:  # noqa: BLE001
            st["status"] = InstanceStatus.FAILED
            st["logs"].append(LogLine.now("android", f"spawn failed: {e}", "error"))

    async def _forward_input(self, iid: str, ev: InputEvent) -> bool:
        st = self._insts[iid]
        if st["status"] != InstanceStatus.RUNNING:
            return False
        d = ev.data
        if ev.kind == "tap":
            args = ["input", "tap", str(int(d.get("x", 0))), str(int(d.get("y", 0)))]
        elif ev.kind == "swipe":
            args = ["input", "swipe", str(int(d.get("x1", 0))), str(int(d.get("y1", 0))),
                    str(int(d.get("x2", 0))), str(int(d.get("y2", 0)))]
        elif ev.kind == "key":
            args = ["input", "keyevent", str(d.get("code", 3))]
        else:
            return False
        proc = await asyncio.create_subprocess_exec(
            _BIN, "adb", *args,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        st["logs"].append(LogLine.now("android", f"input {' '.join(args)}"))
        return True

    async def stop(self, iid: str) -> None:
        st = self._insts.get(iid)
        if st:
            proc = st.get("proc")
            if proc and proc.returncode is None:
                proc.terminate()
                try:
                    await proc.wait()
                except Exception:
                    pass
            st["status"] = InstanceStatus.STOPPED
            st["logs"].append(LogLine.now("android", "stop"))

    def get_status(self, iid: str) -> InstanceStatus:
        st = self._insts.get(iid)
        return st["status"] if st else InstanceStatus.FAILED

    async def push_input(self, iid: str, ev: InputEvent) -> bool:
        return await self._forward_input(iid, ev)

    def frames(self, iid: str):
        # v1 TODO: waydroid 窗口画面抓取（平台原生窗口，roadmap）→ 空流
        return []

    def logs(self, iid: str, n: int = 200) -> list[LogLine]:
        st = self._insts.get(iid)
        return list(st["logs"][-n:]) if st else []
