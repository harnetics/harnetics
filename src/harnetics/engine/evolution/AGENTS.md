# engine/evolution/
> L2 | 父级: src/harnetics/engine/AGENTS.md

草稿生成自进化子模块 — 基于 EvoMap/evolver GEP 协议，实现本机经验积累与迭代进化。

## 成员清单

`__init__.py`: 模块入口，暴露 `get_evolution_context()` 与 `write_draft_signal()`
`signals.py`: 信号写入器 — 每次草稿生成后将评估结果追加到 `memory/signals/draft-signals.jsonl`，供 evolver 扫描
`runner.py`: evolver CLI 调用器 — 草稿生成前调用 `evolver`，捕获 GEP 演化提示词注入 system prompt；evolver 未安装时静默降级

## 工作原理

```
草稿生成请求
    ↓
[runner] get_evolution_context() — 调用 evolver CLI，读取 memory/ 历史信号，返回 GEP 提示词
    ↓
[DraftGenerator] 将 GEP 上下文注入 system prompt → 调用 LLM → 评估
    ↓
[signals] write_draft_signal() — 将本次评估结果写入 memory/signals/
    ↓
下次生成时 evolver 读取信号，选择更合适的 Gene
```

## 前端可视化

`/api/evolution/stats` 端点（`api/routes/evolution.py`）读取 `memory/signals/draft-signals.jsonl`，
为前端 `Evolution.tsx` 页面提供：当前策略、阻断率、信号时间轴、标签分布、失败检查器统计。


## 演化策略自动选择

| 最近 20 条信号 blocked 比率 | 策略 |
|---|---|
| 0% | `innovate` — 功能探索 |
| 1%–29% | `balanced` — 稳步演化 |
| 30%–59% | `harden` — 稳定优先 |
| ≥60% | `repair-only` — 紧急修复 |

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
