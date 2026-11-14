# UniOrchestrator（Chuxin）｜统一应用编排调度框架

一套抽象接口托管运行时，REST+WebSocket API + 内置 Web 管理面板

- ✅ **当前稳定**：Linux 平台，子进程托管 Waydroid 运行安卓 APK
- 🧪 **实验模块**（`UNIO_EXPERIMENTAL=1` 手动开启）：Linux 托管 touchHLE，
  仅用于 iPhone OS 2–5 复古 IPA 研究（无签名绕过 / AMFI / FairPlay）
- 📌 **Roadmap**：Windows / macOS 平台适配；Mach-O 兼容插槽（接口已预留）

> 上游运行时（Waydroid / touchHLE）全部**用户自备**、以独立子进程隔离调用；
> 框架本体 **MIT** 协议，不复制上游源码。

---

## 免责（必读）

1. 本项目为**自研调度框架**，上游运行时（Waydroid / touchHLE 等）是**外部独立程序**，
   由用户自行准备并自行遵守其开源协议与本框架代码零耦合；本仓库不包含任何上游源码。
2. touchHLE 插件**仅支持官方原生兼容的远古 IPA（iPhone OS 2–5），不支持现代 iOS 应用**；
   项目内**无任何签名绕过、AMFI、FairPlay 相关逻辑**。
3. 本框架不校验、不担保上游程序及其托管应用（APK/IPA）的合法性；使用者对加载内容自行负责。
4. experimental 功能仅供研究；生产用途请先读 [docs/08-security.md](docs/08-security.md)。
5. 本框架默认仅绑定 127.0.0.1，对外暴露前必须自行加鉴权与防火墙。

## 快速开始（v0.1 原型）

```bash
cd UniOrchestrator
./run.sh                      # 起服务 → http://127.0.0.1:8731 （面板）
# experimental 通道（需自备 touchHLE 二进制）：
UNIO_EXPERIMENTAL=1 ./run.sh
# 上游二进制位置可用环境变量覆盖：
UNIO_WAYDROID_BIN=/path/to/waydroid UNIO_TOUCHHLE_BIN=/path/to/touchHLE
```

零依赖演示：面板选 `mock` 运行时即可跑通 create/start/帧流/输入/日志/stop 全管线。

## 上游依赖清单（外部程序，用户自备，协议各自独立）

| 上游 | 用途 | 仓库 | 协议 | 集成方式 |
|---|---|---|---|---|
| Waydroid (+ LXC) | Android 容器后端 | github.com/waydroid | LXC 组件 GPL-2.0；Android 镜像 Apache-2.0（下载件） | 仅 spawn 子进程，不链接 |
| touchHLE | 复古 iOS 模拟器 | github.com/touchHLE/touchHLE | 见其仓库 LICENSE（本框架不复制其代码） | 仅 spawn + 白名单参数 |
| Darling（Mach-O 插槽参考） | 未实现 | github.com/darlinghq/darling | GPL-2.0 | 仅思路参考 |

**本框架代码：MIT（见 LICENSE）。** 框架与上游之间是进程边界，不是代码边界。

## 版本路线

| 版本 | 内容 | 状态 |
|---|---|---|
| v0.1 | Python 原型：接口/门控/白名单/WS 管线全量验证（本仓库当前） | ✅ |
| v0.2 | 同构迁移 Rust（Axum + tokio）；cgroup 配额落地；waydroid 画面抓取 | 计划 |
| v1.0 | Linux stable 包（仅 Android + Mock） | 计划 |
| v2.0 | Windows（Win32 窗口层）/ macOS（Cocoa）；Mach-O 实现 | Roadmap |

## 文档

- [docs/00-arch.md](docs/00-arch.md) — 架构思维导图 / 模块划分 / 依赖边界 / 平台门控矩阵
- [docs/01-interfaces.md](docs/01-interfaces.md) — 统一抽象接口
- [docs/08-security.md](docs/08-security.md) — 白名单 / 隔离 / 沙箱
