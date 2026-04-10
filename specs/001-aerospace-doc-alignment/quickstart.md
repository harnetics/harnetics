# Quickstart: Harnetics 航天文档对齐系统

**Date**: 2026-04-10
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

---

## Prerequisites

| 依赖           | 最低版本 | 说明                                      |
|----------------|----------|-------------------------------------------|
| Python         | 3.11+    | 推荐 3.12                                  |
| Ollama         | latest   | 本地 LLM 运行时                            |
| GPU            | —        | RTX 4090 (24GB) 或 Apple M4 Max            |
| 磁盘空间       | 50 GB    | 模型 15GB + 数据 + 系统                    |
| RAM            | 32 GB    |                                            |

---

## Installation

### Option A: 本地安装（推荐开发）

```bash
# 1. 克隆项目
git clone <repo-url> harnetics
cd harnetics

# 2. 安装项目（含全部依赖）
pip install -e ".[dev]"

# 3. 安装 Ollama 并拉取模型
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma4:26b-it-a4b-q4_K_M

# 4. 初始化数据库
harnetics init

# 5. 导入 fixture 文档
harnetics ingest ./fixtures/ --recursive

# 6. 启动 Web 服务
harnetics serve --port 8080
```

### Option B: Docker Compose

```bash
# 1. 克隆项目
git clone <repo-url> harnetics
cd harnetics

# 2. 启动（首次会构建镜像 + 拉取模型）
docker compose up -d

# 3. 等待 Ollama 拉取模型（首次约 15GB）
docker compose logs -f ollama

# 4. 打开浏览器
open http://localhost:8080
```

---

## Verify: Smoke Test

系统启动后，执行以下步骤验证功能正常：

### 1. 检查系统状态

```bash
curl http://localhost:8080/api/status
```

**Expected**:
```json
{
  "status": "ok",
  "documents_count": 10,
  "edges_count": 15,
  "ollama_available": true
}
```

### 2. 验证文档库

浏览器打开 `http://localhost:8080/documents`，确认：
- 10 份 fixture 文档全部显示
- 按"动力系统部"筛选显示 4 份文档（DOC-DES-001, DOC-TST-001/002/003）
- 点击 DOC-ICD-001 详情，可看到 12 个 ICD 参数

### 3. 验证文档图谱

浏览器打开 `http://localhost:8080/graph`，确认：
- 10 个文档节点全部显示
- 至少 15 条关系边
- DOC-ICD-001 在视觉中心
- 节点按部门颜色区分

### 4. 验证草稿生成

浏览器打开 `http://localhost:8080/draft`：
1. 选择：部门=动力系统部，类型=测试大纲，层级=分系统层
2. 输入主题：`TQ-12液氧甲烷发动机地面全工况热试车测试大纲`
3. 确认推荐的 7 份相关文档
4. 点击"生成对齐草稿"
5. 等待生成完成（<3 分钟）

**Expected**:
- 草稿覆盖模板所有必填章节（8 章）
- 每个技术指标有 📎 引注标记
- 至少 1 处 ⚠️ 冲突标记（DOC-TST-003 ICD 版本不一致）
- Evaluator 结果：0 阻断，≤2 告警

### 5. 验证变更影响分析

浏览器打开 `http://localhost:8080/impact`：
1. 选择 DOC-ICD-001
2. 点击"分析影响"
3. 等待分析完成（<30 秒）

**Expected**:
- 4 份受影响文档被识别
- DOC-DES-001, DOC-TST-001/002/003 标记为受影响
- 影响级别标注正确

---

## Key Test Scenarios

### Scenario 1: Full Fixture Import

```bash
# 清空数据库 -> 重新入库 -> 验证完整性
harnetics init --reset
harnetics ingest ./fixtures/ --recursive
curl http://localhost:8080/api/status
# 验证: documents_count=10, edges_count>=15
```

### Scenario 2: Draft Generation Quality

```bash
# 通过 API 生成草稿
curl -X POST http://localhost:8080/api/draft/generate \
  -H "Content-Type: application/json" \
  -d '{
    "requester_department": "动力系统部",
    "doc_type": "TestPlan",
    "system_level": "Subsystem",
    "subject": "TQ-12液氧甲烷发动机地面全工况热试车测试大纲",
    "parent_doc_id": "DOC-SYS-001",
    "template_id": "DOC-TPL-001",
    "related_doc_ids": ["DOC-ICD-001", "DOC-DES-001", "DOC-TST-001"]
  }'
# 验证: status=completed, citations 非空, eval_results 全部 pass/warn
```

### Scenario 3: Evaluator Catches Pre-planted Issues

预埋的 4 处不一致必须被检测：

| # | 不一致                                         | 预期 Evaluator |
|---|------------------------------------------------|----------------|
| T1| DOC-TST-003 引用 ICD v2.1（当前 v2.3）          | EA.3 warn      |
| T2| DOC-TST-003 推力值 600 kN（应 650 kN）          | EB.1 fail      |
| T3| DOC-TST-002 发动机质量 500 kg（ICD ≤480 kg）   | EB.1 fail      |
| T4| DOC-TST-001 缺少 REQ-SYS-004 追溯              | Phase 1 (EC.2) |

### Scenario 4: Automated Test Suite

```bash
# 运行全部测试
pytest tests/ -v

# 仅运行 parser 测试（无 GPU 需求）
pytest tests/test_parsers/ -v

# 仅运行 evaluator 测试（无 GPU 需求）
pytest tests/test_evaluators/ -v

# 端到端测试（需要 Ollama 运行）
pytest tests/test_e2e/ -v
```

---

## CLI Commands

```bash
harnetics init              # 创建数据库 + 初始化 schema
harnetics init --reset      # 清空数据库重新初始化
harnetics ingest <path>     # 导入文档（单文件或目录）
harnetics ingest <path> --recursive  # 递归导入目录
harnetics serve             # 启动 Web 服务 (default: 0.0.0.0:8080)
harnetics serve --port 9090 # 指定端口
```
