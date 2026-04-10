# [INPUT]: 依赖 parsers (markdown/yaml/icd)、graph.store CRUD、models (DocumentNode/Section/DocumentEdge)
# [OUTPUT]: 对外提供 DocumentIndexer 类与 extract_relations()
# [POS]: graph 包的文档入库引擎，负责解析文件、写入图谱、提取关系
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import frontmatter

from harnetics.graph import store
from harnetics.models.document import DocumentEdge, DocumentNode, Section
from harnetics.models.icd import ICDParameter
from harnetics.parsers.icd_parser import parse_icd_yaml
from harnetics.parsers.markdown_parser import parse_markdown
from harnetics.parsers.yaml_parser import parse_yaml

_DOC_ID_RE = re.compile(r"DOC-[A-Z]{3}-\d{3}")
_LEADING_HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*", re.DOTALL)

# ---- 根据文档类型推断关系 ----
_TYPE_KEYWORDS: dict[str, str] = {
    "ICD": "constrained_by",
    "Requirement": "derived_from",
}


def extract_relations(doc_id: str, content: str) -> list[DocumentEdge]:
    """正则扫描文档引用，推断关系类型。"""
    refs = set(_DOC_ID_RE.findall(content))
    refs.discard(doc_id)
    edges: list[DocumentEdge] = []
    for target_id in sorted(refs):
        # 判断关系类型
        target_doc = store.get_document(target_id)
        if target_doc and target_doc.doc_type == "ICD":
            relation = "constrained_by"
        elif target_doc and target_doc.doc_type == "Requirement":
            relation = "derived_from"
        else:
            relation = "references"
        edges.append(
            DocumentEdge(
                source_doc_id=doc_id,
                source_section_id="",
                target_doc_id=target_id,
                target_section_id="",
                relation=relation,
                confidence=1.0,
            )
        )
    return edges


class DocumentIndexer:
    """文档入库索引器：解析 → 存储 → 建关系。"""

    def __init__(self, embedding_store=None) -> None:
        self._embedding_store = embedding_store

    def ingest_document(
        self, file_path: str, metadata: dict | None = None
    ) -> DocumentNode:
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")
        ext = p.suffix.lower()
        meta = metadata or {}

        # ---- 从文件名或 frontmatter/metadata 块提取 doc_id ----
        doc_id = meta.get("doc_id") or self._extract_doc_id(p.stem, content, ext)
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        if ext in (".yaml", ".yml"):
            return self._ingest_yaml(p, content, doc_id, content_hash, meta)
        return self._ingest_markdown(p, content, doc_id, content_hash, meta)

    # ---- Markdown ----
    def _ingest_markdown(
        self, path: Path, content: str, doc_id: str,
        content_hash: str, meta: dict,
    ) -> DocumentNode:
        # frontmatter 提取
        normalized_content = _LEADING_HTML_COMMENT_RE.sub("", content, count=1)
        post = frontmatter.loads(normalized_content)
        fm: dict = dict(post.metadata) if post.metadata else {}
        fm.update({k: v for k, v in meta.items() if v})

        doc = DocumentNode(
            doc_id=doc_id,
            title=fm.get("title", path.stem),
            doc_type=fm.get("doc_type", "Document"),
            department=fm.get("department", ""),
            system_level=fm.get("system_level", ""),
            engineering_phase=fm.get("engineering_phase", ""),
            version=fm.get("version", "v1.0"),
            status=fm.get("status", "draft"),
            content_hash=content_hash,
            file_path=str(path),
        )
        store.insert_document(doc)

        sections = parse_markdown(post.content, doc_id)
        store.insert_sections(sections)
        if self._embedding_store is not None:
            self._embedding_store.index_sections(doc_id, sections)

        edges = extract_relations(doc_id, content)
        self._safe_insert_edges(edges)

        return doc

    # ---- YAML ----
    def _ingest_yaml(
        self, path: Path, content: str, doc_id: str,
        content_hash: str, meta: dict,
    ) -> DocumentNode:
        data = parse_yaml(content)
        fm = data.get("metadata", {}) or {}
        fm.update({k: v for k, v in meta.items() if v})

        doc = DocumentNode(
            doc_id=doc_id,
            title=fm.get("title", path.stem),
            doc_type=fm.get("doc_type", "Document"),
            department=fm.get("department", ""),
            system_level=fm.get("system_level", ""),
            engineering_phase=fm.get("engineering_phase", ""),
            version=fm.get("version", "v1.0"),
            status=fm.get("status", "draft"),
            content_hash=content_hash,
            file_path=str(path),
        )
        store.insert_document(doc)

        # YAML 文档也拆 section（description 等文本块）
        desc = fm.get("description", "")
        if desc:
            sec = Section(
                section_id=f"{doc_id}-sec-0", doc_id=doc_id,
                heading="description", content=str(desc).strip(),
                level=1, order_index=0,
            )
            sections = [sec]
            store.insert_sections(sections)
            if self._embedding_store is not None:
                self._embedding_store.index_sections(doc_id, sections)

        edges = extract_relations(doc_id, content)
        self._safe_insert_edges(edges)

        # ICD 参数
        if fm.get("doc_type") == "ICD" or "ICD" in doc_id.upper():
            params = parse_icd_yaml(content, doc_id)
            store.insert_icd_parameters(params)

        return doc

    # ---- 辅助 ----
    @staticmethod
    def _extract_doc_id(stem: str, content: str, ext: str) -> str:
        m = _DOC_ID_RE.search(stem)
        if m:
            return m.group(0)
        m = _DOC_ID_RE.search(content[:500])
        if m:
            return m.group(0)
        return stem

    @staticmethod
    def _safe_insert_edges(edges: list[DocumentEdge]) -> None:
        """只插入 target_doc_id 已存在的边。"""
        valid = [e for e in edges if store.get_document(e.target_doc_id)]
        store.insert_edges(valid)

    def ingest_directory(
        self, dir_path: str, recursive: bool = True
    ) -> list[DocumentNode]:
        root = Path(dir_path)
        pattern = "**/*" if recursive else "*"
        docs: list[DocumentNode] = []
        for p in sorted(root.glob(pattern)):
            if p.name == "AGENTS.md":
                continue
            if p.suffix.lower() in (".md", ".yaml", ".yml") and p.is_file():
                docs.append(self.ingest_document(str(p)))
        return docs
