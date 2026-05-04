# .github/workflows/
> L2 | 父级: /.github/AGENTS.md

成员清单
ci.yml: 主 CI 流水线，覆盖后端 pytest、前端 build 与 main 分支 Docker 发布。
desktop-release.yml: 桌面发布流水线，在 `v*.*.*` 标签或手动触发时构建 Windows x64、macOS arm64、macOS x64（`macos-15-intel`）安装包并上传 release assets。

法则: 普通 CI 与发布构建分离；release job 必须显式失败，不产出残缺安装包。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
