"""交付件 2（代码形态）：统一抽象接口。
Rust 迁移对应 types.rs（trait + 结构体），方法签名逐一对应。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Optional, Protocol, runtime_checkable


class InstanceStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    MISSING_BIN = "missing_binary"


@dataclass
class ResourceQuota:
    """cgroup v2 best-effort 配额（失败不阻断启动，见 docs/08-security.md）"""
    cpu_quota_us: int = 200_000          # 默认 2 核
    mem_max_bytes: int = 512 * 1024 * 1024

    def apply_cgroup(self, tag: str, pid: int) -> bool:
        """尽力而为：cgroup v2 可用则建组写限额，不可用/失败返回 False。"""
        try:
            import os
            base = "/sys/fs/cgroup"
            if not os.path.isdir(f"{base}/unio-{tag}"):
                os.makedirs(f"{base}/unio-{tag}")
                with open(f"{base}/unio-{tag}/cgroup.procs", "w") as f:
                    f.write(str(pid))
                with open(f"{base}/unio-{tag}/cpu.max", "w") as f:
                    f.write(f"{self.cpu_quota_us} 100000")
                with open(f"{base}/unio-{tag}/memory.max", "w") as f:
                    f.write(str(self.mem_max_bytes))
                return True
            return False
        except Exception:
            return False


@dataclass
class WindowConfig:
    width: int = 640
    height: int = 960
    orientation: str = "portrait"       # portrait | landscape | upside-down
    fullscreen: bool = False


@dataclass
class InstanceConfig:
    name: str
    runtime: str = "mock"               # mock | android | touchhle
    app: str = ""                       # apps/ 目录下相对路径；空 = 无应用（纯演示）
    quota: ResourceQuota = field(default_factory=ResourceQuota)
    window: WindowConfig = field(default_factory=WindowConfig)
    extra: dict = field(default_factory=dict)   # 由运行时做白名单过滤
    shared_dir: str = ""

    @property
    def tag(self) -> str:
        return f"{self.runtime}:{self.name}"


@dataclass
class InputEvent:
    kind: str                           # tap | swipe | key | text
    data: dict = field(default_factory=dict)


@dataclass
class LogLine:
    ts: float
    level: str
    source: str
    msg: str

    @staticmethod
    def now(source: str, msg: str, level: str = "info") -> "LogLine":
        return LogLine(time.time(), level, source, msg)


class FrameStream:
    """帧流抽象：async 生成器产出 (ts, jpeg_bytes)；WS 网关推 b64。"""


@runtime_checkable
class AppRuntime(Protocol):
    name: str
    channel: str                        # stable | experimental

    async def create_instance(self, cfg: InstanceConfig) -> str: ...
    async def start(self, iid: str) -> None: ...
    async def stop(self, iid: str) -> None: ...
    def get_status(self, iid: str) -> InstanceStatus: ...
    async def push_input(self, iid: str, ev: InputEvent) -> bool: ...
    def frames(self, iid: str) -> AsyncIterator[tuple[float, bytes]]: ...
    def logs(self, iid: str, n: int = 200) -> list[LogLine]: ...
