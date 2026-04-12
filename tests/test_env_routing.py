# [INPUT]: 依赖本地 HTTP 伪 provider、config.get_settings、engine.draft_generator、llm.client 与 graph.embeddings
# [OUTPUT]: 提供 env 路由回归测试，锁定 bare 模型名在 OpenAI-compatible 网关下的端到端可用性与实际模型路由持久化
# [POS]: tests 目录中的环境配置契约测试，验证 .env + 自定义 base_url 能同时驱动 LLM、Embedding 与草稿元数据
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from harnetics.config import get_settings
from harnetics.engine.draft_generator import DraftGenerator
from harnetics.graph.embeddings import EmbeddingStore
from harnetics.llm.client import HarneticsLLM
from harnetics.models.document import Section


class _FakeProviderHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._write_json(
                200,
                {
                    "data": [
                        {"id": "claude-sonnet-4-6"},
                        {"id": "jina-embeddings-v5-text-small"},
                    ]
                },
            )
            return
        self._write_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
        payload = json.loads(body or b"{}")

        if self.path == "/v1/chat/completions":
            self._write_json(
                200,
                {
                    "choices": [
                        {"message": {"content": "# fake draft\n\n内容由本地 fake provider 返回。"}}
                    ]
                },
            )
            return

        if self.path == "/v1/embeddings":
            inputs = payload.get("input", [])
            data = []
            for index, text in enumerate(inputs):
                base = float((len(text) % 7) + 1)
                data.append({"index": index, "embedding": [base, base / 10.0, 0.5]})
            self._write_json(200, {"data": data})
            return

        self._write_json(404, {"error": "not found"})

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _write_json(self, status: int, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


@contextmanager
def _fake_provider_server() -> tuple[str, ThreadingHTTPServer]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeProviderHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/v1", server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_env_openai_compatible_gateway_supports_bare_models(tmp_path: Path, monkeypatch) -> None:
    with _fake_provider_server() as (base_url, _server):
        monkeypatch.chdir(tmp_path)
        for key in list(os.environ):
            if key.startswith("HARNETICS_") or key.startswith("OPENAI_"):
                monkeypatch.delenv(key, raising=False)

        env_file = tmp_path / ".env"
        monkeypatch.setenv("HARNETICS_ENV_FILE", str(env_file))
        env_file.write_text(
            "\n".join(
                [
                    "HARNETICS_LLM_MODEL=claude-sonnet-4-6",
                    f"HARNETICS_LLM_BASE_URL={base_url}",
                    "HARNETICS_LLM_API_KEY=sk-test",
                    "HARNETICS_EMBEDDING_MODEL=jina-embeddings-v5-text-small",
                    f"HARNETICS_EMBEDDING_BASE_URL={base_url}",
                    "HARNETICS_EMBEDDING_API_KEY=sk-test",
                    f"HARNETICS_CHROMA_DIR={tmp_path / 'chroma'}",
                ]
            ),
            encoding="utf-8",
        )

        settings = get_settings()
        llm = HarneticsLLM(
            model=settings.llm_model,
            api_base=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )

        assert llm.model == "openai/claude-sonnet-4-6"
        assert llm.availability_status() == (True, "")
        assert "fake draft" in llm.generate_draft("system", "context", "request")

        store = EmbeddingStore(
            persist_path=str(settings.chromadb_path),
            model_name=settings.embedding_model,
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
        )
        store.index_sections(
            "DOC-TEST-001",
            [
                Section(
                    section_id="DOC-TEST-001-sec-1",
                    doc_id="DOC-TEST-001",
                    heading="1 涡轮泵试验",
                    content="定义涡轮泵试验工况和验收准则。",
                )
            ],
        )

        hits = store.search_similar("涡轮泵试验", top_k=3)

        assert store._model_name == "openai/jina-embeddings-v5-text-small"
        assert hits
        assert hits[0]["section_id"] == "DOC-TEST-001-sec-1"


def test_draft_generator_records_effective_llm_route(monkeypatch) -> None:
    class FakeLLM:
        model = "openai/claude-sonnet-4-6"

        def generate_draft(self, system_prompt: str, context: str, user_request: str) -> str:
            return "# fake draft\n\n内容由远端 provider 返回。"

    class FakeConnection:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple]] = []

        def execute(self, sql: str, params: tuple):
            self.calls.append((sql, params))
            return None

    fake_conn = FakeConnection()

    @contextmanager
    def fake_get_connection():
        yield fake_conn

    monkeypatch.setattr("harnetics.engine.draft_generator.store.get_connection", fake_get_connection)

    from harnetics.evaluators.base import EvaluatorBus
    monkeypatch.setattr("harnetics.engine.draft_generator.build_default_bus", lambda: EvaluatorBus())

    draft = DraftGenerator(llm=FakeLLM()).generate(
        {
            "subject": "姿控推进接口变更",
            "related_doc_ids": [],
            "template_id": "",
        }
    )

    assert draft.generated_by == "openai/claude-sonnet-4-6"
    assert fake_conn.calls
    assert fake_conn.calls[0][1][-1] == "openai/claude-sonnet-4-6"


def test_draft_generator_falls_back_to_class_name_when_llm_model_is_not_string(monkeypatch) -> None:
    class FakeLLM:
        model = object()

        def generate_draft(self, system_prompt: str, context: str, user_request: str) -> str:
            return "# fake draft"

    class FakeConnection:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple]] = []

        def execute(self, sql: str, params: tuple):
            self.calls.append((sql, params))
            return None

    fake_conn = FakeConnection()

    @contextmanager
    def fake_get_connection():
        yield fake_conn

    monkeypatch.setattr("harnetics.engine.draft_generator.store.get_connection", fake_get_connection)

    from harnetics.evaluators.base import EvaluatorBus
    monkeypatch.setattr("harnetics.engine.draft_generator.build_default_bus", lambda: EvaluatorBus())

    draft = DraftGenerator(llm=FakeLLM()).generate(
        {
            "subject": "姿控推进接口变更",
            "related_doc_ids": [],
            "template_id": "",
        }
    )

    assert draft.generated_by == "FakeLLM"
    assert fake_conn.calls
    assert fake_conn.calls[0][1][-1] == "FakeLLM"