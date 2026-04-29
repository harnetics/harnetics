# 第三方引用、致谢与许可证边界说明

本文档用于公开记录 Harnetics 当前对第三方项目的引用、感谢与许可证边界。

## EvoMap / Evolver

Harnetics 最近引入的自进化（Self-Evolution）链路，参考并对接了 [EvoMap / Evolver](https://github.com/EvoMap/evolver) 的部分公开设计与工作流。在此对 Evolver 项目及其作者表示感谢。

### 引用与感谢

- 项目：`EvoMap/evolver`
- 仓库：<https://github.com/EvoMap/evolver>
- 文档入口：<https://github.com/EvoMap/evolver?tab=readme-ov-file>
- 当前上游许可证：`GPL-3.0-or-later`（请以上游仓库最新声明为准）

Harnetics 当前自进化链路重点参考了以下公开内容：

- GEP（Genome Evolution Protocol）相关术语与工作流表达
- Gene / Capsule / EvolutionEvent 等演化资产命名
- 围绕 `evolver` CLI 的本地演化上下文生成与消费方式
- 对“经验沉淀 → 下次运行注入 → 形成可回看进化轨迹”这一闭环的产品化表述

### 当前项目中的相关位置

- `src/harnetics/engine/evolution/`
- `README.md`
- `README_EN.md`
- `docs/CHANGELOG.md`
- 前端 Evolution 页面与对应 API 说明

### 当前边界说明

截至本文档更新时，Harnetics 对 Evolver 的使用与引用主要体现在：

1. **协议/概念层参考**：参考其公开 README、协议术语与工作流表达。
2. **工具互操作**：在本地运行环境中调用独立安装的 `evolver` CLI，读取其输出的 GEP 上下文，用于增强 Harnetics 草稿生成前的 system prompt。
3. **公开致谢与来源标注**：在 README 与本说明文档中保留对上游项目的引用和感谢。

Harnetics 仓库维护者会持续审查相关实现边界；如果未来引入、复制、改写或分发任何受 `GPL-3.0-or-later` 覆盖的 Evolver 源代码或其衍生内容，将按对应许可证要求进一步调整本项目的分发方式、许可证声明与合规材料。

### 备注

- 本说明文档用于提升来源透明度与开源协作礼仪，不替代正式法律意见。
- 如上游项目的许可证、归属声明或额外要求发生变化，请以其官方仓库最新说明为准，并同步更新本文件。