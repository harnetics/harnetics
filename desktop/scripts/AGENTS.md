# desktop/scripts/
> L2 | 父级: /desktop/AGENTS.md

成员清单
fix-macos-dmg.mjs: macOS DMG 后处理脚本，挂载最新 Tauri DMG、隐藏 `.VolumeIcon.icns`、重新压缩镜像；非 macOS 平台直接跳过。

法则: 脚本只修正打包产物元数据，不改业务代码，不依赖用户运行时状态。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
