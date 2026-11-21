# UniOrchestrator (Chuxin) — unified app orchestration framework

**English** · [中文](README.zh-CN.md)

One abstraction layer that supervises pluggable runtimes, plus a REST + WebSocket API and a built-in web panel.

- ✅ **Stable today**: Linux, hosting Waydroid in a child process to run Android APKs
- 🧪 **Experimental** (opt in with `UNIO_EXPERIMENTAL=1`): Linux hosting touchHLE, used only for iPhone OS 2–5 retro IPA research (no signature bypass / AMFI / FairPlay)
- 📌 **Roadmap**: Windows / macOS platform support; a Mach-O compatibility slot (the interface is reserved)

> Upstream runtimes (Waydroid / touchHLE) are **supplied by the user** and invoked as isolated child processes;
> the framework itself is **MIT** and copies no upstream source code.

---

## Disclaimer (read first)

1. This project is a **home-grown orchestration framework**. The upstream runtimes (Waydroid / touchHLE etc.) are **external, independent programs** that the user prepares and licenses themselves; they are coupled to this framework's code in no way, and this repository contains no upstream source code.
2. The touchHLE slot **only supports ancient IPAs that upstream itself natively supports (iPhone OS 2–5), not modern iOS apps**; the project contains **no signature bypass, AMFI or FairPlay logic** of any kind.
3. The framework does not validate or vouch for the upstream programs or the APK/IPA content they host; whoever loads content is responsible for it.
4. The experimental path is research-only; for production use read [docs/08-security.md](docs/08-security.md) first.
5. The framework binds to 127.0.0.1 by default; before exposing it, add authentication and a firewall yourself.

## Quick start (v0.1 prototype)

```bash
cd UniOrchestrator
./run.sh                      # start the service → http://127.0.0.1:8731 (web panel)
# experimental channel (needs your own touchHLE binary):
UNIO_EXPERIMENTAL=1 ./run.sh
# upstream binary locations can be overridden with environment variables:
UNIO_WAYDROID_BIN=/path/to/waydroid UNIO_TOUCHHLE_BIN=/path/to/touchHLE
```

Zero-dependency demo: pick the `mock` runtime in the panel and the whole pipeline — create / start / frame stream / input / logs / stop — runs end to end.

## Upstream dependencies (external programs, user-supplied, each under its own license)

| Upstream | Role | Repository | License | Integration |
|---|---|---|---|---|
| Waydroid (+ LXC) | Android container backend | github.com/waydroid | LXC components GPL-2.0; Android images Apache-2.0 (downloaded artifacts) | Spawned as a subprocess, never linked |
| touchHLE | Retro iOS emulator | github.com/touchHLE/touchHLE | See its own LICENSE (this framework copies none of its code) | Spawn only, with whitelisted arguments |
| Darling (Mach-O slot reference) | Not implemented | github.com/darlinghq/darling | GPL-2.0 | Idea reference only |

**This framework's code is MIT (see LICENSE).** The boundary between framework and upstream is a process boundary, not a code boundary.

## Version roadmap

| Version | Scope | Status |
|---|---|---|
| v0.1 | Python prototype: interfaces / gating / whitelists / WS pipeline all validated (what this repo contains) | ✅ |
| v0.2 | Isomorphic migration to Rust (Axum + tokio); cgroup quotas; Waydroid frame capture | Planned |
| v1.0 | Linux stable package (Android + Mock only) | Planned |
| v2.0 | Windows (Win32 window layer) / macOS (Cocoa); Mach-O implementation | Roadmap |

## Documentation

- [docs/00-arch.md](docs/00-arch.md) — architecture mind map / module split / dependency boundaries / platform gating matrix
- [docs/01-interfaces.md](docs/01-interfaces.md) — the unified abstraction interfaces
- [docs/08-security.md](docs/08-security.md) — whitelists / isolation / sandboxing
