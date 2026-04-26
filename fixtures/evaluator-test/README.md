# evaluator-test/ — 六校验器测试语料指南

本目录为 Harnetics 六个在线校验器提供**专属测试语料**，每个子目录对应一个校验器，
包含 PASS / WARN / FAIL 三种预期结果的文档对。

---

## 目录结构

```
evaluator-test/
├── EA2/   引注现实性（Citation Reality）
├── EA3/   引注版本新鲜度（Version Freshness）
├── EA4/   无循环引用（No Cyclic References）
├── EA5/   技术段落覆盖率（Coverage Rate）
├── EB1/   接口参数与 ICD 一致性（ICD Consistency）
└── ED3/   冲突明确标记（Conflict Marked）
```

---

## 前置条件

### 1. 启动服务

```bash
# 后端
harnetics serve              # 默认 http://localhost:8000

# 前端（另开终端）
cd frontend && npm run dev   # http://localhost:5173
```

### 2. 确认 LLM / Embedding 已配置

访问 `http://localhost:5173/settings`，填写 LLM Base URL 与 API Key。

---

## EA2 — 引注现实性

**校验逻辑**：草稿正文中所有 `[📎 DOC-XXX-NNN §x]` 引注，对应文档必须已存在于图谱。

| 文件 | 导入操作 | EA2 预期结果 |
|------|---------|------------|
| `EA2/DOC-EA2-REAL.md` | 先导入（作为真实源文档） | — |
| `EA2/DOC-EA2-DRAFT-PASS.md` | 生成时引用 DOC-EA2-REAL | **PASS** |
| `EA2/DOC-EA2-DRAFT-FAIL.md` | 引用 DOC-EA2-GHOST（未导入） | **FAIL** |

**测试步骤**：

```bash
# 1. 导入真实文档
harnetics ingest fixtures/evaluator-test/EA2/DOC-EA2-REAL.md

# 2. 在 UI 中打开草稿工作台，新建草稿并粘贴 DOC-EA2-DRAFT-PASS.md 内容
#    → EA2 应显示绿色 PASS

# 3. 新建另一份草稿，粘贴 DOC-EA2-DRAFT-FAIL.md 内容（引用 DOC-EA2-GHOST）
#    → EA2 应显示红色 FAIL
```

---

## EA3 — 引注版本新鲜度

**校验逻辑**：草稿引用的文档若 `status = Superseded`，报 WARN。

| 文件 | 导入操作 | EA3 预期结果 |
|------|---------|------------|
| `EA3/DOC-EA3-CURRENT.md` | 先导入（Approved 当前版本） | — |
| `EA3/DOC-EA3-OLD.md` | 先导入（Superseded 废止版本） | — |
| `EA3/DOC-EA3-DRAFT-MIXED.md` | 引用两份文档 | 场景 A：**PASS**；场景 B：**WARN** |

**测试步骤**：

```bash
# 1. 导入两份源文档
harnetics ingest fixtures/evaluator-test/EA3/DOC-EA3-CURRENT.md
harnetics ingest fixtures/evaluator-test/EA3/DOC-EA3-OLD.md

# 2. 草稿工作台中粘贴 DOC-EA3-DRAFT-MIXED.md
#    → 场景 A 段落（引用 DOC-EA3-CURRENT）EA3 应显示 PASS
#    → 场景 B 段落（引用 DOC-EA3-OLD）EA3 应显示 WARN
```

---

## EA4 — 无循环引用

**校验逻辑**：对整个文档图进行 DFS，检测到有向环则报 FAIL。

### 场景 A：线性链（PASS）

```bash
harnetics ingest fixtures/evaluator-test/EA4/DOC-EA4-A.md
harnetics ingest fixtures/evaluator-test/EA4/DOC-EA4-B.md
harnetics ingest fixtures/evaluator-test/EA4/DOC-EA4-C.md
# 导入三份文档后在 UI 中生成任意草稿 → EA4 应显示 PASS
```

### 场景 B：循环引用（FAIL）

```bash
# ⚠️  以下操作会污染图谱！建议在测试环境或临时 DB 中执行
harnetics ingest fixtures/evaluator-test/EA4/DOC-EA4-CYC-X.md
harnetics ingest fixtures/evaluator-test/EA4/DOC-EA4-CYC-Y.md
# X → Y、Y → X 形成环，EA4 应显示 FAIL
```

> **注意**：EA4 对全图执行 DFS，而不是只检查当前草稿。
> 导入循环文档后，所有后续草稿的 EA4 都会报 FAIL，直到删除循环文档。
> 可在文档库页面点击「删除」移除 DOC-EA4-CYC-X 与 DOC-EA4-CYC-Y 以恢复。

---

## EA5 — 技术段落覆盖率

**校验逻辑**：正文中包含数字的段落视为"技术段落"，其中有 `📎` 引注的比例必须 ≥ 80%。

| 文件 | 技术段落数 | 有引注 | 覆盖率 | EA5 预期结果 |
|------|-----------|--------|--------|------------|
| `EA5/DOC-EA5-HIGH-COV.md` | 5 | 5 | 100% | **PASS** |
| `EA5/DOC-EA5-LOW-COV.md` | 5 | 1 | 20% | **WARN** |

**测试步骤**：

```bash
# 在草稿工作台中依次粘贴两份文档内容并评估
# DOC-EA5-HIGH-COV.md → EA5 绿色 PASS
# DOC-EA5-LOW-COV.md  → EA5 黄色 WARN
```

---

## EB1 — 接口参数与 ICD 一致性

**校验逻辑**：草稿中出现「参数名 + 数值」组合，若 ICD 图谱中有同名参数，
二者数值必须一致（精确匹配）。

| 文件 | 导入操作 | EB1 预期结果 |
|------|---------|------------|
| `EB1/DOC-EB1-ICD.yaml` | 先导入（提供 ICD 参数真相） | — |
| `EB1/DOC-EB1-DRAFT-PASS.md` | 草稿参数与 ICD 一致（燃烧室压力=10 MPa） | **PASS** |
| `EB1/DOC-EB1-DRAFT-FAIL.md` | 草稿参数与 ICD 不一致（写 15 MPa） | **FAIL** |

**测试步骤**：

```bash
# 1. 导入 ICD 参数文档
harnetics ingest fixtures/evaluator-test/EB1/DOC-EB1-ICD.yaml

# 2. 草稿工作台粘贴 DOC-EB1-DRAFT-PASS.md 内容 → EB1 PASS
# 3. 草稿工作台粘贴 DOC-EB1-DRAFT-FAIL.md 内容 → EB1 FAIL

# 验证 ICD 参数已注册
curl http://localhost:8000/api/icd-parameters | python3 -m json.tool
```

> **关键**：草稿内容中参数名必须**从行首开始**，格式为
> `「参数名」为/是 数值 单位`，否则 `_PARAM_PATTERN` 正则可能无法匹配。
> 例如：`燃烧室压力为 10 MPa` ✅ / `系统要求燃烧室压力为 10 MPa` ❌

---

## ED3 — 冲突明确标记

**校验逻辑**：冲突检测器发现的冲突（`draft.conflicts` 列表）数量必须 ≤ 草稿正文中的 `⚠️` 标记数。

| 文件 | conflicts 列表 | 正文 ⚠️ 数 | ED3 预期结果 |
|------|--------------|----------|------------|
| `ED3/DOC-ED3-DRAFT-PASS.md` | 2 处 | 2 个 ⚠️ | **PASS** |
| `ED3/DOC-ED3-DRAFT-FAIL.md` | 2 处 | 0 个 ⚠️ | **FAIL** |

> **重要**：ED3 的 `conflicts` 字段由冲突检测器在生成草稿时注入，
> **不从 markdown frontmatter 读取**。单独导入 MD 文件不会触发冲突检测。

**测试步骤（通过 UI 草稿工作台）**：

1. 打开 `http://localhost:5173/drafts`，新建草稿。
2. 选择一份含跨系统冲突参数的主题（需图谱中已有多份 ICD 文档包含同名不同值的参数）。
3. 生成草稿后，前端评估面板 → ED3 自动显示结果。
4. 在草稿内容中添加或删除 `⚠️` 标记后重新评估，观察 ED3 在 PASS / FAIL 之间切换。

**通过 API 直接测试 ED3**：

```bash
# 调用评估 API，手动注入 conflicts 列表
curl -X POST http://localhost:8000/api/drafts/{draft_id}/evaluate \
  -H "Content-Type: application/json" \
  -d '{"evaluator_id": "ED.3"}'
```

---

## 一键批量导入所有源文档

```bash
# 导入所有非草稿源文档（用于为草稿评估准备图谱数据）
harnetics ingest fixtures/evaluator-test/EA2/DOC-EA2-REAL.md
harnetics ingest fixtures/evaluator-test/EA3/DOC-EA3-CURRENT.md
harnetics ingest fixtures/evaluator-test/EA3/DOC-EA3-OLD.md
harnetics ingest fixtures/evaluator-test/EA4/DOC-EA4-A.md
harnetics ingest fixtures/evaluator-test/EA4/DOC-EA4-B.md
harnetics ingest fixtures/evaluator-test/EA4/DOC-EA4-C.md
harnetics ingest fixtures/evaluator-test/EB1/DOC-EB1-ICD.yaml
```

---

## 验证校验结果

1. 打开草稿工作台 `http://localhost:5173/drafts`。
2. 点击「新建草稿」，粘贴对应 DRAFT 文档内容（或通过 `主题` 选择）。
3. 点击「评估」按钮，右侧校验面板按颜色分级显示结果：
   - 🟢 **PASS** — 通过
   - 🟡 **WARN** — 警告（可提交，但建议修改）
   - 🔴 **FAIL / BLOCK** — 阻断（必须修改后才能提交）
   - ⚪ **SKIP** — 跳过（前置条件不满足，无法评估）

---

## 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|--------|
| EA2 总是 SKIP | 图谱为空或引注格式不对 | 检查引注格式必须为 `[📎 DOC-XXX-NNN §x]`（3位大写字母前缀） |
| EB1 总是 SKIP | 图谱中无 ICD 参数 | 先执行 `harnetics ingest EB1/DOC-EB1-ICD.yaml` |
| EA4 所有草稿都 FAIL | 图谱存在循环文档 | 在文档库中删除 DOC-EA4-CYC-X 和 DOC-EA4-CYC-Y |
| ED3 总是 PASS | 该草稿无 conflicts 记录 | 需要先通过冲突检测器生成有冲突的草稿 |
