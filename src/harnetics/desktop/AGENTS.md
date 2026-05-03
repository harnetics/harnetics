# harnetics/desktop/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口，导出 DesktopRuntimePaths 与 build_sidecar_environment。
paths.py: 桌面版用户数据目录契约，统一 graph DB、Chroma、上传、导出、日志与 `.env` 的 sidecar 环境变量。

法则: 桌面版不得写安装目录；所有可变状态必须落到用户 app data 根目录。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
