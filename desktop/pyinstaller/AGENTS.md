# desktop/pyinstaller/
> L2 | 父级: /desktop/AGENTS.md

成员清单
harnetics-server.spec: PyInstaller sidecar 配置，将 `harnetics.cli.main` 打成 Tauri 可启动的后端服务二进制。

法则: sidecar 只包装现有 CLI serve 入口；不得复制业务代码或引入第二套启动语义。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
