# Quickstart: LLM Connectivity and Impact Localization Hardening

## 1. 配置本地 Ollama

```bash
export HARNETICS_LLM_MODEL="gemma4:26b"
export HARNETICS_LLM_BASE_URL="http://localhost:11434"
curl http://localhost:11434/api/tags
```

## 2. 运行回归测试

```bash
uv run pytest tests/test_llm_client.py tests/test_e2e_mvp_scenario.py -q
```

## 3. 手工验证草稿生成

```bash
uv run python -m harnetics.cli.main serve --reload
curl -X POST http://localhost:8000/api/draft/generate \
  -H 'Content-Type: application/json' \
  -d '{"subject":"推进与结构接口规格草稿","related_doc_ids":[],"template_id":""}'
```

预期：

- 未要求用户显式写 `ollama/` 前缀
- 失败时返回可诊断的 `detail`

## 4. 手工验证章节级影响定位

```bash
curl -X POST http://localhost:8000/api/impact/analyze \
  -H 'Content-Type: application/json' \
  -d '{"doc_id":"DOC-SYS-001","old_version":"v3.0","new_version":"v3.1"}'
```

预期：

- 至少一个 `impacted_docs[].affected_sections` 非空
- `DOC-DES-001` / `DOC-TST-003` 等下游文档出现章节定位结果