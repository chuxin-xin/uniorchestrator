"""TouchHLERuntime（experimental，默认关闭）。
- 仅 spawn 用户自备的 touchHLE 原生二进制，参数全部过 whitelist.validate()
- UNIO_EXPERIMENTAL=1 才注册进插件表（registry 门控）
- 无签名绕过 / AMFI / FairPlay 逻辑；仅官方原生兼容的远古 IPA（研究用途）
"""
from __future__ import annotations

import asyncio
import os
import shutil
from ..types import InputEvent, InstanceConfig, InstanceStatus, LogLine
from ..whitelist import WhitelistError, validate

_BIN = os.environ.get("UNIO_TOUCHHLE_BIN", "touchHLE")
_APPS_DIR = os.environ.get("UNIO_APPS_DIR", "apps")


def _have_bin() -> bool:
    return shutil.which(_BIN) is not None


class TouchHLERuntime:
    name = "touchhle"
    channel = "experimental"

    def __init__(self) -> None:
        self._insts: dict[str, dict] = {}

    async def create_instance(self, cfg: InstanceConfig) -> str:
        iid = f"touchhle-{cfg.name}"
        st = {
            "cfg": cfg,
            "status": InstanceStatus.MISSING_BIN if not _have_bin() else InstanceStatus.CREATED,
            "logs": [LogLine.now("touchhle", f"create {iid} bin={'ok' if _have_bin() else 'MISSING'}")],
            "proc": None,
        }
        self._insts[iid] = st
        return iid

    def _safe_app_path(self, rel: str) -> str:
        """app 路径铁律：必须落在 _APPS_DIR 内（realpath 防 ../ 逃逸）。"""
        base = os.path.realpath(_APPS_DIR)
        p = os.path.realpath(os.path.join(base, rel))
        if not p.startswith(base + os.sep):
            raise WhitelistError("app path escapes allow dir")
        if not (p.endswith(".ipa") or p.endswith(".app")):
            raise WhitelistError("app must be .ipa or .app")
        return p

    async def start(self, iid: str) -> None:
        st = self._insts.get(iid)
        if not st:
            raise KeyError(iid)
        cfg = st["cfg"]
        # 顺序铁律：白名单先验（快速失败）→ 再看二进制缺失（降级态）
        try:
            argv = validate(cfg.extra)
            if cfg.app:
                app_path = self._safe_app_path(cfg.app)
        except WhitelistError as e:
            st["status"] = InstanceStatus.FAILED
            st["logs"].append(LogLine.now("touchhle", f"config reject: {e}", "error"))
            return
        if st["status"] == InstanceStatus.MISSING_BIN:
            st["logs"].append(LogLine.now("touchhle", "start refused: touchHLE binary missing (user-provided upstream)", "error"))
            return
        try:
            cmd = [_BIN]
            if cfg.app:
                cmd.append(app_path)
            cmd += argv
            if cfg.window.orientation == "landscape":
                cmd.append("--landscape-left")
            elif cfg.window.orientation == "upside-down":
                cmd.append("--upside-down")
            if not cfg.window.fullscreen and os.environ.get("UNIO_HEADLESS") == "1":
                cmd.append("--headless")
            st["logs"].append(LogLine.now("touchhle", f"spawn: {' '.join(cmd)}"))
            st["proc"] = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            st["status"] = InstanceStatus.RUNNING
        except (OSError, Exception) as e:  # noqa: BLE001  spawn 失败不 500
            st["status"] = InstanceStatus.FAILED
            st["logs"].append(LogLine.now("touchhle", f"spawn failed: {e}", "error"))

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
            st["logs"].append(LogLine.now("touchhle", "stop"))

    def get_status(self, iid: str) -> InstanceStatus:
        st = self._insts.get(iid)
        return st["status"] if st else InstanceStatus.FAILED

    async def push_input(self, iid: str, ev: InputEvent) -> bool:
        # v1: touchHLE 输入为窗口/控制器侧原生，API 注入 = roadmap；记录不执行
        st = self._insts.get(iid)
        if st:
            st["logs"].append(LogLine.now("touchhle", f"input queued (v1 no-op): {ev.kind}", "warn"))
        return False

    def frames(self, iid: str):
        return []  # 窗口原生自绘；帧抓取 = roadmap

    def logs(self, iid: str, n: int = 200) -> list[LogLine]:
        st = self._insts.get(iid)
        return list(st["logs"][-n:]) if st else []
