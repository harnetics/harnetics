# desktop/
> L2 | 父级: /AGENTS.md

成员清单
AGENTS.md: 桌面打包模块地图，约束 Tauri 壳、sidecar 构建与发布产物边界。
package.json: 桌面壳 Node 脚本与 Tauri CLI 依赖，复用 `frontend/dist` 作为前端资源。
tsconfig.json: 桌面工具链 TypeScript 配置，占位供 Tauri/Node 脚本扩展。
scripts/: 桌面打包后处理脚本目录，当前修正 macOS DMG 隐藏图标元数据。
pyinstaller/: Python 后端 sidecar 打包配置目录。
src-tauri/: Tauri v2 Rust 应用，负责窗口、动态端口、sidecar 生命周期与安装包配置。

法则: 桌面层只管进程生命周期和安装包，不承载业务逻辑；业务仍属于 `frontend/` 与 `src/harnetics/`。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
