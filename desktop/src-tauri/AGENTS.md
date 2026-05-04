# desktop/src-tauri/
> L2 | 父级: /desktop/AGENTS.md

成员清单
Cargo.toml: Rust/Tauri 包配置，声明 sidecar 生命周期所需依赖。
build.rs: Tauri 构建脚本入口。
tauri.conf.json: 桌面应用元数据、bundle 目标、frontend dist 路径、正式应用图标、DMG 固定布局与 sidecar 配置；主窗口默认隐藏，等待后端健康后显示。
capabilities/default.json: Tauri v2 默认能力配置，保持最小权限。
icons/: Tauri 应用图标资源目录，包含 PNG/ICO/ICNS 三种安装包图标格式。
src/main.rs: 桌面壳入口，动态端口、用户数据目录、sidecar 启停、bootstrap 日志转发与窗口延迟显示；优先从 `.app/Contents/MacOS` 解析 sidecar，规避 macOS resource_dir 不可用。

法则: Rust 层只做本地进程编排；任何业务规则回到 Python API 或 React 前端。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
