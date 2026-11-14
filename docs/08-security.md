# 08 · 安全说明（交付件 8）

## 1. 参数白名单（touchHLE 通道）

`unio/whitelist.py` 只放行 touchHLE 官方 `OPTIONS_HELP.txt` 公开参数（当前集合，随官方更新）：

- 布尔开关：`--fullscreen --headless --no-error-popup --print-fps --force-composition
  --ignore-gl-errors --allow-network-access --upside-down --landscape-left
  --landscape-right --disable-analog-stick-tilt-controls`
- 封闭枚举：`--device-family={iphone,ipad}` `--gles1={gles1_on_gl2,gles1_native}`
- 数值域：`--scale-hack≥1` `--deadzone∈[0,1]` `--x/y-tilt-range/offset`（可负）
- `--preferred-languages`：ISO 639 短码逗号列表

**未知键 / 越域值 → `WhitelistError`，实例置 failed，不 spawn。** 不透传、不 shell、
`create_subprocess_exec` 以 argv 向量传参（shell=False 语义，无命令注入面）。

## 2. 子进程隔离

- 上游运行时全部是用户自备的独立二进制；框架与其之间**只有进程边界**（spawn + 参数 + 管道）
- 不静态链接、不复制上游代码、不做二进制修改/内存补丁
- touchHLE 的 app 路径必须落在 `UNIO_APPS_DIR`（默认 `apps/`）内，`realpath` 防 `../` 逃逸，
  且后缀必须 `.ipa/.app`

## 3. 沙箱资源限制

- `ResourceQuota`（默认 2 核 / 512MB）：cgroup v2 best-effort 应用（v0.1 标记 TODO，v0.2 落地）
- 框架服务默认**仅绑定 127.0.0.1**；远程访问 = 用户自建反代 + 鉴权（v1 内置令牌鉴权 = roadmap）

## 4. 门控

- `UNIO_EXPERIMENTAL=1` 才注册 touchHLE 运行时；stable 包默认关闭
- 上游二进制缺失 → 实例降级 `missing_binary`（可诊断，不 500）
- 输入事件仅在 `running` 实例接受，否则 409，不排队

## 5. 免责（与 README 同步）

- 复古 iOS 研究用途；无签名绕过 / AMFI / FairPlay 逻辑；不支持现代 iOS
- 加载的 APK/IPA 内容由用户自行负责
- 上游协议风险与框架代码隔离（进程边界），但用户需自行满足上游 LICENSE 要求
