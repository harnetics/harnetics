# Quickstart: AI 向量驱动的影响分析与草稿联动

## 本地验证步骤

### 1. 环境配置验证

```bash
# 创建 .env 文件（云端模型）
cat > .env << 'EOF'
HARNETICS_LLM_MODEL=deepseek/deepseek-chat
HARNETICS_LLM_API_KEY=sk-your-key
HARNETICS_EMBEDDING_MODEL=openai/text-embedding-3-small
HARNETICS_EMBEDDING_API_KEY=sk-your-key
EOF

# 或者使用本地模型（默认配置，无需 .env）
# 启动服务
python -m harnetics.api.app

# 验证配置生效
curl http://localhost:8000/api/status | python -m json.tool
# 预期：llm_model="deepseek/deepseek-chat", embedding_model="openai/text-embedding-3-small"
```

### 2. 向量影响分析验证

```bash
# 触发影响分析
curl -X POST http://localhost:8000/api/impact/analyze \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "DOC-FMA-001", "new_version": "3.1"}'

# 检查返回：
# - analysis_mode 应为 "ai_vector"（有向量索引时）
# - affected_sections 应为对象数组（含 reason），而非全部章节
# - 受影响章节数量 << 文档总章节数
```

### 3. 草稿台向量检索验证

```bash
# 搜索候选文档
curl "http://localhost:8000/api/documents/search?q=涡轮泵性能试验&top_k=5"

# 检查返回：
# - results 数量 ≤ top_k
# - 每项有 relevance_score
# - 最相关文档排在最前
```

### 4. 影响报告→草稿台联动验证

```
1. 打开影响报告页面 /impact/{report_id}
2. 点击某个受影响文档的"生成对齐草稿"按钮
3. 验证跳转到 /draft?trigger_doc_id=X&impacted_doc_id=Y&report_id=Z
4. 验证草稿台主题已自动填写、来源文档已自动勾选
5. 直接点击"开始生成"，验证草稿正常生成
```

### 5. 降级验证

```bash
# 删除 .env 中的 API key，或停止 Ollama
# 重启服务后触发影响分析
# 预期：analysis_mode="heuristic"，系统正常运行但使用规则引擎
```

## 冒烟测试

```bash
pytest tests/ -q
# 预期：所有现有测试通过 + 新增测试通过
```
