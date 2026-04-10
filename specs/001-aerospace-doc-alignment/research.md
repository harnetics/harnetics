# Research: Aerospace Document Alignment

**Phase**: 0 — Outline & Research
**Date**: 2026-04-10
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

---

## R1: Document Parsing Strategy

**Decision**: Python `markdown` library for Markdown parsing; `PyYAML` for YAML parsing; custom ICD parser for structured parameter extraction.

**Rationale**:
- Markdown 文档按标题层级（`#`, `##`, `###`）拆分为 Section tree，每个 Section 保留 heading、content、level、order_index
- PyYAML 以 `safe_load` 读取通用 YAML，ICD YAML 有固定 schema（`parameters` list with `param_id`, `name`, `interface_type`, `subsystem_a/b`, `value`, `unit`, `range`, `owner_department`）
- ICD parser 是 YAML parser 的特化——先 `safe_load`，再按 ICD schema 校验并提取 `ICDParameter` 对象列表
- 不引入 `markdown-it-py` 等重量 AST parser——标题分割已够用，无需 inline token 级别解析

**Alternatives Considered**:
- `mistune` / `markdown-it-py`：功能过剩，MVP 只需按标题拆分，不需解析行内标记
- LLM 辅助解析：PRD 明确排除，MVP 只用规则

---

## R2: Relation Extraction

**Decision**: 正则表达式提取文档编号引用（`DOC-[A-Z]{3}-\d{3}`）+ ICD 参数编号引用（`ICD-[A-Z]{3}-\d{3}`），建立 `references` / `traces_to` / `constrained_by` 类型的文档间 Edge。

**Rationale**:
- 航天文档编号格式高度规范（DOC-SYS-001、DOC-ICD-001 等），正则匹配精度极高
- fixture 文档中预埋了明确的文档编号引用，可直接字符串匹配
- 关系类型推断规则：
  - 需求文档引用 ICD → `derived_from`
  - 设计文档引用需求 → `traces_to`
  - 测试文档引用设计 → `traces_to`
  - 任何文档引用 ICD → `constrained_by`
  - 同编号不同版本 → `supersedes`
  - 影响分析结果 → `impacts`
- 置信度：精确编号匹配 = 1.0，上下文推断 = 0.85

**Alternatives Considered**:
- LLM 辅助关系抽取：PRD §13 明确排除，Phase 1 再考虑
- NER + 知识图谱工具（Neo4j, spaCy）：过重，SQLite + 自定义 Edge 表足够

---

## R3: Vector Store

**Decision**: chromadb (local persistent mode) + `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` 嵌入模型。

**Rationale**:
- chromadb 轻量、纯 Python、本地持久化、无服务端依赖——与 SQLite 的"零依赖"哲学一致
- `paraphrase-multilingual-MiniLM-L12-v2`：
  - 支持中英双语（航天文档中英混合）
  - 模型体积 ~470MB，CPU 推理可用，GPU 推理更快
  - 768 维向量，检索精度够用
- 嵌入粒度：Section 级别（非全文、非句子），平衡检索精度与上下文完整性
- 每个 Section 嵌入时附带 metadata：`{doc_id, section_id, heading, doc_type, department}`
- 检索策略：草稿生成时先按 metadata filter（department, doc_type）缩小范围，再向量相似度排序

**Alternatives Considered**:
- FAISS：更快但需手动管理索引持久化，chromadb 开箱即用
- Qdrant/Milvus：需独立服务，违背单机部署约束
- OpenAI embeddings：违背 offline-only 约束

---

## R4: LLM Integration

**Decision**: `litellm` 封装 Ollama API，模型 `ollama/gemma4:26b-it-a4b-q4_K_M`，temperature=0.3，max_tokens=8192。

**Rationale**:
- litellm 提供统一 API 抽象——未来切换模型（如 Qwen2.5、DeepSeek）无需改业务代码
- Ollama 本地部署，HTTP API on `localhost:11434`，litellm 原生支持 `ollama/` 前缀
- Gemma 4 26B A4B（MoE, 4B active params）：
  - 26B 总参数的知识量 + 4B 活跃参数的推理速度
  - Q4_K_M 量化 ~15GB，单卡 RTX 4090 可运行
  - 32K 上下文窗口，可容纳 7-10 份文档的关键章节
  - 中英双语表现优于同量级模型
- temperature=0.3：技术文档需要严谨，低随机性
- max_tokens=8192：足够生成完整测试大纲（8 章节）
- System prompt 强制规则：必须引注、不许捏造、冲突标记

**Alternatives Considered**:
- 直接调用 Ollama REST API：缺少重试、超时等生产级处理
- vLLM / llama.cpp server：Ollama 已集成 llama.cpp，额外部署无意义
- Cloud API (OpenAI/Claude)：违背 offline-only 安全约束

---

## R5: Evaluator Architecture

**Decision**: `BaseEvaluator` 抽象基类 + `EvaluatorBus` runner pattern。每个 Evaluator 独立实现 `evaluate(draft, graph) -> EvalResult`。

**Rationale**:
- 8 个 Evaluator 各自独立、无相互依赖，天然适合 Strategy 模式
- `EvaluatorBus` 持有 Evaluator 注册表，按顺序运行所有注册 Evaluator，收集 `EvalResult` 列表
- 每个 `EvalResult` 含：evaluator_id, name, status (pass/fail/warn/skip), level (block/warn), detail, locations
- 阻断逻辑：Bus 运行完毕后检查是否有 `level=block && status=fail`，若有则阻止导出
- 每个 Evaluator 可独立单元测试——输入 mock draft + mock graph，验证输出

**8 个 MVP Evaluator**:

| ID   | 名称           | 实现策略                                          | 级别 |
|------|----------------|---------------------------------------------------|------|
| EA.1 | 引注完整性     | 正则匹配含数字段落，检查 📎 标记存在              | block |
| EA.2 | 引用真实性     | 提取 DOC-XXX-XXX，查 documents 表                 | block |
| EA.3 | 版本最新       | 比对引用版本与 documents 表最新版本               | warn  |
| EA.4 | 无循环引用     | edges 表 DFS 环检测                               | block |
| EA.5 | 覆盖率 ≥80%   | 技术段落数 / 有引注段落数                         | warn  |
| EB.1 | ICD 一致性     | 草稿参数值 vs icd_parameters 表值                 | block |
| ED.1 | 无捏造指标     | 每个数字交叉验证源文档                            | block |
| ED.3 | 冲突已标记     | conflicts 列表 vs 草稿正文 ⚠️ 标记              | block |

**Alternatives Considered**:
- 插件系统（entry_points 注册）：MVP 阶段过度工程，直接导入即可
- 并行执行 Evaluator：8 个 Evaluator 都是本地计算，串行毫秒级，无需并行

---

## R6: Frontend Technology

**Decision**: FastAPI + Jinja2 (server-side rendering) + HTMX (dynamic interaction) + Tailwind CSS + DaisyUI (styling) + vis-network.js (graph visualization)。

**Rationale**:
- Server-side rendering + HTMX = "SPA 体验，零 JS 框架"
  - 无需 Node.js 构建工具链，无需 npm
  - HTMX 通过 HTML attributes (`hx-get`, `hx-post`, `hx-swap`) 实现动态交互
  - 草稿生成进度用 HTMX polling 或 SSE 实现
- Tailwind CSS + DaisyUI：
  - DaisyUI 提供开箱即用的组件（table, card, badge, modal, progress），减少手写样式
  - 深色/浅色主题切换通过 DaisyUI `data-theme` 实现
  - CDN 引入，无构建步骤
- vis-network.js：
  - 轻量图谱可视化（~300KB），支持节点拖拽、点击事件、过滤
  - 无 npm 依赖，CDN 引入
  - nodes + edges JSON 数据由 `/api/graph` 端点提供
- 前端原型（`docs/design-docs/prototype2/`）使用 React+shadcn/ui，但后端实现改用 Jinja2+HTMX，降低部署复杂度

**Alternatives Considered**:
- React / Vue / Svelte SPA：需要 Node.js 构建、前后端分离增加部署复杂度
- Django + Django Templates：FastAPI 异步性能更优，且 LLM 调用需异步支持
- Alpine.js：HTMX 对服务端渲染交互更优雅，Alpine 更适合纯客户端状态

---

## R7: Database Design

**Decision**: SQLite（单文件数据库），schema 直接使用 PRD §5.4 定义。

**Rationale**:
- 单文件部署——`var/harnetics.db` 一个文件包含全部关系数据
- 无需数据库服务——与 "aerospace offline" 约束完美契合
- 7 张核心表：documents, sections, edges, icd_parameters, versions, drafts, impact_reports
- CHECK 约束确保枚举值合法（doc_type 11 种、system_level 5 种、relation 6 种等）
- 外键 + CASCADE 保证引用完整性
- 索引策略：按查询热路径建索引（doc_id, source/target_doc_id, relation, department, doc_type）
- JSON 字段（tags, request_json, citations_json 等）用 TEXT 存储 JSON 字符串，Python 侧 json.loads/dumps

**Alternatives Considered**:
- PostgreSQL：需要数据库服务，违背单机零依赖约束
- DuckDB：分析型 OLAP 不适合 OLTP 读写模式
- TinyDB / JSON files：无 SQL、无约束、无索引，规模增长后不可维护

---

## Summary

所有技术决策已确认，无 NEEDS CLARIFICATION 残留。核心原则：**最小依赖、本地离线、单文件部署、正则优先 LLM**。技术栈完全对齐 PRD §4.2 和 §12 的定义。
