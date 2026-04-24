# [INPUT]: 依赖 chromadb、sentence-transformers、openai SDK 与 models.document.Section
# [OUTPUT]: 对外提供 EmbeddingStore 类（本地/云端 embedding 双模式）；新增 delete_by_doc(doc_id) 向量删除
# [POS]: graph 包的向量检索层，负责章节级语义索引、相似性搜索与文档级聚合检索，并统一 OpenAI-compatible embedding 调用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from openai import OpenAI

from harnetics.models.document import Section

_COLLECTION_NAME = "harnetics_sections"
_OPENAI_EMBEDDING_PREFIX = "text-embedding-"
_LOCAL_MODEL_HINTS = (
    "paraphrase-",
    "all-",
    "bge-",
    "e5-",
    "gte-",
    "nomic-embed",
    "mxbai-embed",
    "sentence-transformers/",
)


# ================================================================
# 云端 embedding function — 包装 OpenAI-compatible embeddings.create()
# ================================================================

class _OpenAICompatibleEmbeddingFunction:
    """ChromaDB 自定义 EmbeddingFunction，路由到 OpenAI-compatible embeddings.create()。"""

    def __init__(self, model: str, api_key: str = "", base_url: str = "") -> None:
        self._model = _normalize_embedding_model(
            model,
            api_key=api_key,
            base_url=base_url,
        )
        self._request_model = _request_embedding_model(self._model)
        self._api_key = _request_embedding_api_key(api_key or None, self._model)
        self._base_url = _request_embedding_api_base(self._model, base_url or None)

    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=60.0,
        )
        resp = client.embeddings.create(
            model=self._request_model,
            input=input,
        )
        return [list(item.embedding) for item in resp.data]

    def embed_documents(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return self(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return self(input)

    @staticmethod
    def name() -> str:
        return "openai-compatible"

    @staticmethod
    def build_from_config(config: dict) -> "_OpenAICompatibleEmbeddingFunction":
        return _OpenAICompatibleEmbeddingFunction(
            model=str(config.get("model", "")),
            base_url=str(config.get("base_url", "")),
        )

    def get_config(self) -> dict:
        return {
            "model": self._model,
            "base_url": self._base_url or "",
        }

    def is_legacy(self) -> bool:
        return False


def _normalize_embedding_model(model_name: str, api_key: str = "", base_url: str = "") -> str:
    """将 bare 远程 embedding 模型名归一化为可诊断的 provider/model 形式。"""
    normalized = model_name.strip()
    if not normalized or "/" in normalized:
        return normalized
    if normalized.startswith(_OPENAI_EMBEDDING_PREFIX):
        return f"openai/{normalized}"
    if (api_key or base_url) and not _looks_like_local_model(normalized):
        return f"openai/{normalized}"
    return normalized


def _request_embedding_model(model_name: str) -> str:
    normalized = model_name.strip()
    if "/" in normalized:
        return normalized.split("/", 1)[1]
    return normalized


def _request_embedding_api_base(model_name: str, base_url: str | None) -> str:
    normalized = (base_url or "").rstrip("/")
    if normalized:
        if model_name.startswith("ollama/") and not normalized.endswith("/v1"):
            return f"{normalized}/v1"
        return normalized
    if model_name.startswith("ollama/"):
        return "http://localhost:11434/v1"
    return "https://api.openai.com/v1"


def _request_embedding_api_key(api_key: str | None, model_name: str) -> str:
    if api_key:
        return api_key
    if model_name.startswith("ollama/"):
        return "ollama"
    raise RuntimeError("missing embedding api key")


def _looks_like_local_model(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    return any(normalized.startswith(prefix) for prefix in _LOCAL_MODEL_HINTS)


def _uses_remote_embeddings(model_name: str, api_key: str = "", base_url: str = "") -> bool:
    """判断是否应走远程 embedding provider，而不是本地 sentence-transformers。"""
    normalized = _normalize_embedding_model(model_name, api_key=api_key, base_url=base_url)
    if "/" in normalized:
        return True
    if api_key or base_url:
        return not _looks_like_local_model(normalized)
    return False


class EmbeddingStore:
    """ChromaDB 向量存储，承载章节级语义检索。支持本地 sentence-transformers 与云端 OpenAI-compatible embedding。"""

    def __init__(
        self,
        persist_path: str,
        model_name: str,
        api_key: str = "",
        base_url: str = "",
    ) -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=persist_path)
        self._model_name = _normalize_embedding_model(
            model_name,
            api_key=api_key,
            base_url=base_url,
        )
        self._ef = self._build_ef(
            self._model_name,
            api_key=api_key,
            base_url=base_url,
        )
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=self._ef,
        )

    @staticmethod
    def _build_ef(model_name: str, api_key: str = "", base_url: str = ""):
        if _uses_remote_embeddings(model_name, api_key=api_key, base_url=base_url):
            return _OpenAICompatibleEmbeddingFunction(model=model_name, api_key=api_key, base_url=base_url)
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        return SentenceTransformerEmbeddingFunction(model_name=model_name)

    # ---- 索引 --------------------------------------------------------

    def index_sections(self, doc_id: str, sections: list[Section]) -> None:
        if not sections:
            return
        ids = [s.section_id for s in sections]
        documents = [f"{s.heading}\n{s.content}" for s in sections]
        metadatas = [
            {"doc_id": s.doc_id, "heading": s.heading,
             "level": s.level, "order_index": s.order_index}
            for s in sections
        ]
        self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    # ---- 章节级检索 ---------------------------------------------------

    def search_similar(
        self, query: str, top_k: int = 10, filters: dict | None = None
    ) -> list[dict]:
        where = filters if filters else None
        results = self._collection.query(
            query_texts=[query], n_results=top_k, where=where,
        )
        hits: list[dict] = []
        if not results["ids"] or not results["ids"][0]:
            return hits
        for i, sid in enumerate(results["ids"][0]):
            hit: dict = {"section_id": sid}
            if results["metadatas"]:
                hit.update(results["metadatas"][0][i])
            if results["documents"]:
                hit["text"] = results["documents"][0][i]
            if results["distances"]:
                hit["distance"] = results["distances"][0][i]
            hits.append(hit)
        return hits

    # ---- 文档级聚合检索 -----------------------------------------------

    def search_documents(self, query: str, top_k: int = 10) -> list[dict]:
        """按 query 检索章节后按 doc_id 聚合，取每个文档下最高相关度。"""
        section_hits = self.search_similar(query, top_k=top_k * 3)
        doc_best: dict[str, dict] = {}
        for hit in section_hits:
            doc_id = hit.get("doc_id", "")
            if not doc_id:
                continue
            distance = hit.get("distance", 999.0)
            score = max(0.0, 1.0 - distance)
            if doc_id not in doc_best or score > doc_best[doc_id]["relevance_score"]:
                doc_best[doc_id] = {"doc_id": doc_id, "relevance_score": round(score, 4)}
        ranked = sorted(doc_best.values(), key=lambda d: d["relevance_score"], reverse=True)
        return ranked[:top_k]

    # ---- 状态查询 -----------------------------------------------------

    def section_count(self) -> int:
        return self._collection.count()

    # ---- 删除 --------------------------------------------------------

    def delete_by_doc(self, doc_id: str) -> None:
        """从向量库移除指定文档的所有章节条目（按 metadata.doc_id 过滤）。"""
        if not hasattr(self, "_collection"):
            return
        try:
            self._collection.delete(where={"doc_id": doc_id})
        except Exception:
            pass  # ChromaDB 在集合为空时可能抛异常，静默忽略
