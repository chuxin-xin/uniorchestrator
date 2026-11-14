# 01 · 统一抽象接口（交付件 2）

> 代码形态：`unio/types.py`（Python Protocol）；Rust 迁移目标 `types.rs`（trait），方法签名逐一对应。

## AppRuntime（所有后端实现同一套接口，上层调度器无感）

```
interface AppRuntime {
    name: str            # 运行时标识: "mock" | "android" | "touchhle"
    channel: str         # "stable" | "experimental"

    create_instance(config: InstanceConfig) -> InstanceId
    start(instance_id: InstanceId) -> Result
    stop(instance_id: InstanceId) -> Result
    get_status(instance_id: InstanceId) -> InstanceStatus
    push_input(instance_id: InstanceId, input_event: InputEvent) -> Result
    get_frame_stream(instance_id: InstanceId) -> FrameStream     # async 生成器
    get_log(instance_id: InstanceId, n = 200) -> LogLine[]
}
```

## 公共结构体

| 结构 | 字段 | 说明 |
|---|---|---|
| InstanceConfig | name, runtime, app, quota, window, extra, shared_dir | app 为 apps 目录下相对路径；extra 由运行时做白名单过滤 |
| ResourceQuota | cpu_quota_us(默认 200000=2核), mem_max_bytes(默认 512MB) | cgroup v2 best-effort 应用，失败不阻断启动 |
| WindowConfig | width, height, orientation(portrait/landscape), fullscreen | 转发给上游原生窗口 |
| InputEvent | kind: tap\|swipe\|key\|text, data | 后端自定 data 语义（如 tap: {x,y}） |
| InstanceStatus | created/running/stopped/failed/missing_binary | missing_binary = 上游二进制未装，降级态 |
| LogLine | ts, level, source, msg | 各后端 stdout/事件统一入环 |
| FrameStream | async (ts, b64_jpeg) | v1: mock 合成帧；waydroid 画面抓取 = roadmap TODO（窗口原生自绘） |

## 运行时语义约定

- `create_instance` 只登记配置，不拉进程；`start` 才 spawn
- 上游二进制缺失：实例进入 `missing_binary`，API 返回可诊断信息，不 500
- experimental 运行时未开闸（`UNIO_EXPERIMENTAL`）：`create` 直接 `failed`，原因 "experimental disabled"
- 输入事件在 `stopped` 态推送 = 返回 409，不排队
