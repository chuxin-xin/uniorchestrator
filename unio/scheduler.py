"""调度核心（交付件 3）：实例生命周期 + 实例索引。
Rust 迁移：对应 tokio + 实例表；语义不变。
"""
from __future__ import annotations

from .registry import PluginRegistry
from .types import InstanceConfig, InstanceStatus, InputEvent


class Scheduler:
    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry
        self.index: dict[str, InstanceConfig] = {}

    def runtime(self, name: str):
        rt = self.registry.get(name)
        if rt is None:
            raise KeyError(f"runtime {name!r} not registered (experimental gate?)")
        return rt

    async def create(self, cfg: InstanceConfig) -> str:
        rt = self.runtime(cfg.runtime)
        iid = await rt.create_instance(cfg)
        self.index[iid] = cfg
        return iid

    async def start(self, iid: str) -> InstanceStatus:
        cfg = self.index.get(iid)
        if not cfg:
            raise KeyError(iid)
        await self.runtime(cfg.runtime).start(iid)
        # TODO(v0.2): cgroup v2 配额应用（types.ResourceQuota.apply_cgroup，需拿到子进程 pid）
        rt = self.runtime(cfg.runtime)
        return rt.get_status(iid)

    async def stop(self, iid: str) -> None:
        cfg = self.index.get(iid)
        if not cfg:
            raise KeyError(iid)
        await self.runtime(cfg.runtime).stop(iid)

    def status(self, iid: str) -> InstanceStatus:
        cfg = self.index.get(iid)
        if not cfg:
            return InstanceStatus.FAILED
        return self.runtime(cfg.runtime).get_status(iid)

    async def push_input(self, iid: str, ev: InputEvent) -> bool:
        cfg = self.index.get(iid)
        if not cfg:
            raise KeyError(iid)
        rt = self.runtime(cfg.runtime)
        if rt.get_status(iid) != InstanceStatus.RUNNING:
            return False   # gateway 映射 409
        return await rt.push_input(iid, ev)

    def list_instances(self) -> list[dict]:
        out = []
        for iid, cfg in self.index.items():
            out.append({
                "instance_id": iid,
                "runtime": cfg.runtime,
                "name": cfg.name,
                "channel": self.runtime(cfg.runtime).channel,
                "status": self.status(iid).value,
            })
        return out
