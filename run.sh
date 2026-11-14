#!/usr/bin/env bash
# UniOrchestrator v0.1 原型启动器（stable 通道；experimental 需 UNIO_EXPERIMENTAL=1）
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi "uvicorn[standard]"
exec ./.venv/bin/uvicorn unio.gateway:app --host 127.0.0.1 --port "${UNIO_PORT:-8731}"
