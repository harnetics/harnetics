# Quickstart: OpenAI-compatible LLM 调用收敛

## 1. 配置 OpenAI-compatible 网关

```bash
cat > .env <<'EOF'
HARNETICS_LLM_MODEL=claude-sonnet-4-6-think
HARNETICS_LLM_BASE_URL=https://aihubmix.com/v1
HARNETICS_LLM_API_KEY=sk-your-key
HARNETICS_EMBEDDING_MODEL=jina-embeddings-v5-text-small
HARNETICS_EMBEDDING_BASE_URL=https://aihubmix.com/v1
HARNETICS_EMBEDDING_API_KEY=sk-your-key
EOF
```

预期：服务直接使用原始模型名 `claude-sonnet-4-6-think` 与 `jina-embeddings-v5-text-small` 调用远端网关，不需要 `openai/` 前缀。

## 2. 启动服务并检查状态

```bash
uv run python -m harnetics.cli.main serve --reload
curl http://localhost:8000/api/status
```

预期：
- `llm_model` 为 `claude-sonnet-4-6-think`
- `llm_effective_model` 为 `openai/claude-sonnet-4-6-think`
- `llm_effective_base_url` 为 `https://aihubmix.com/v1`
- `embedding_base_url` 为 `https://aihubmix.com/v1`
- `config_env_file` 指向当前命中的 `.env`

## 3. 验证草稿生成

```bash
curl -X POST http://localhost:8000/api/draft/generate \
  -H 'Content-Type: application/json' \
  -d '{"subject":"试车文档","related_doc_ids":["DOC-SYS-001"]}'
```

预期：草稿生成成功；如果失败，错误中包含 effective model/base，且不含 API key。

## 4. 验证影响分析复用同一路由

```bash
curl -X POST http://localhost:8000/api/impact/analyze \
  -H 'Content-Type: application/json' \
  -d '{"doc_id":"DOC-SYS-001","old_version":"v1.0","new_version":"v2.0"}'
```

预期：若命中 AI 判定路径，其 LLM 使用与草稿生成相同的 effective route；若命中 ai_vector 路径，其 embedding 也复用同一网关语义。

## 5. 运行 targeted regression

```bash
.venv/bin/python -m pytest tests/test_llm_client.py tests/test_graph_store.py tests/test_env_routing.py tests/test_app.py tests/test_e2e_mvp_scenario.py -q
```

预期：目标回归全部通过。

## 6. 验证本地显式 fallback

```bash
cat > .env <<'EOF'
HARNETICS_LLM_MODEL=gemma4:26b
HARNETICS_LLM_BASE_URL=http://localhost:11434
EOF
curl http://localhost:8000/api/status
```

预期：状态端点显示本地 explicit 路由；未配置远端时不报错。