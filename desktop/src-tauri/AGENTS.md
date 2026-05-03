# desktop/src-tauri/
> L2 | 父级: /desktop/AGENTS.md

成员清单
Cargo.toml: Rust/Tauri 包配置，声明 sidecar 生命周期所需依赖。
build.rs: Tauri 构建脚本入口。
tauri.conf.json: 桌面应用元数据、bundle 目标、frontend dist 路径与 sidecar 配置。
capabilities/default.json: Tauri v2 默认能力配置，保持最小权限。
icons/: Tauri 应用图标资源目录，当前含最小占位图。
src/main.rs: 桌面壳入口，动态端口、用户数据目录、sidecar 启停与窗口加载；优先从 `.app/Contents/MacOS` 解析 sidecar，规避 macOS resource_dir 不可用。

法则: Rust 层只做本地进程编排；任何业务规则回到 Python API 或 React 前端。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
