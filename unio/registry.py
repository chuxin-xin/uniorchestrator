"""插件管理器：stable / experimental 门控。
- stable 构建：仅 Mock + Android
- UNIO_EXPERIMENTAL=1：追加 touchHLE（experimental，默认关闭）
- MachORuntime：预留插槽（register 接口已留，无实现）
"""
from __future__ import annotations

import os
from .runtimes.mock import MockRuntime
from .runtimes.android_rt import AndroidRuntime


class PluginRegistry:
    def __init__(self) -> None:
        self._runtimes: dict[str, object] = {}
        self._register(MockRuntime())
        self._register(AndroidRuntime())
        if os.environ.get("UNIO_EXPERIMENTAL") == "1":
            from .runtimes.touchhle_rt import TouchHLERuntime
            self._register(TouchHLERuntime())

    def _register(self, rt) -> None:
        self._runtimes[rt.name] = rt

    def register(self, rt) -> None:
        """预留插槽：Mach-O 等后续运行时在此挂接。"""
        self._runtimes[rt.name] = rt

    def get(self, name: str):
        return self._runtimes.get(name)

    def list(self) -> list[dict]:
        return [{"name": r.name, "channel": r.channel} for r in self._runtimes.values()]
