# [INPUT]: 依赖 parsers (markdown/yaml/icd/docx/xlsx/pdf)、graph.store CRUD、models (DocumentNode/Section/DocumentEdge)
# [OUTPUT]: 对外提供 DocumentIndexer 类与 extract_relations()
# [POS]: graph 包的文档入库引擎，负责解析文件、写入图谱、提取关系；支持 .md/.yaml/.docx/.xlsx/.csv/.pdf
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

# 富格式解析器（lazy-imported 在各 _ingest_* 方法内）
_OFFICE_EXTS = frozenset((".docx", ".xlsx", ".csv", ".pdf"))

_DOC_ID_RE = re.compile(r"DOC-[A-Z]{3}-\d{3}")
_LEADING_HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*", re.DOTALL)
_TRACE_TOKEN_RE = re.compile(r"\b(?:REQ-[A-Z]+-\d+|ICD-[A-Z]+-\d+|TH1-[A-Z]+-\d+)\b")
_SECTION_REF_RE = re.compile(r"(?:DOC-[A-Z]{3}-\d{3}\s*)?§\s*([0-9]+(?:\.[0-9]+)*)")
_HEADING_REF_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)*)\b")

# ---- 根据文档类型推断关系 ----
_TYPE_KEYWORDS: dict[str, str] = {
    "ICD": "constrained_by",
    "Requirement": "derived_from",
}


def extract_relations(doc_id: str, content: str) -> list[DocumentEdge]:
    """正则扫描文档引用，推断关系类型。"""
    refs = set(_DOC_ID_RE.findall(content))
    refs.discard(doc_id)
    return [
        DocumentEdge(
            source_doc_id=doc_id,
            source_section_id="",
            target_doc_id=target_id,
            target_section_id="",
            relation=_relation_for_target(target_id),
            confidence=0.6,
        )
        for target_id in sorted(refs)
    ]


def extract_section_relations(doc_id: str, sections: list[Section]) -> list[DocumentEdge]:
    """在章节级抽取引用关系，并尽量定位到目标章节。"""
    edges: list[DocumentEdge] = []
    seen: set[tuple[str, str, str, str]] = set()

    for section in sections:
        section_text = _section_text(section)
        refs = set(_DOC_ID_RE.findall(section_text))
        refs.discard(doc_id)
        for target_id in sorted(refs):
            target_section_ids = _infer_target_section_ids(target_id, section_text)
            if target_section_ids:
                for target_section_id in target_section_ids:
                    _append_edge(
                        edges,
                        seen,
                        source_doc_id=doc_id,
                        source_section_id=section.section_id,
                        target_doc_id=target_id,
                        target_section_id=target_section_id,
                        relation=_relation_for_target(target_id),
                        confidence=1.0,
                    )
                continue

            _append_edge(
                edges,
                seen,
                source_doc_id=doc_id,
                source_section_id=section.section_id,
                target_doc_id=target_id,
                target_section_id="",
                relation=_relation_for_target(target_id),
                confidence=0.85,
            )

    return edges


def _append_edge(
    edges: list[DocumentEdge],
    seen: set[tuple[str, str, str, str]],
    *,
    source_doc_id: str,
    source_section_id: str,
    target_doc_id: str,
    target_section_id: str,
    relation: str,
    confidence: float,
) -> None:
    key = (source_section_id, target_doc_id, target_section_id, relation)
    if key in seen:
        return
    seen.add(key)
    edges.append(
        DocumentEdge(
            source_doc_id=source_doc_id,
            source_section_id=source_section_id,
            target_doc_id=target_doc_id,
            target_section_id=target_section_id,
            relation=relation,
            confidence=confidence,
        )
    )


def _relation_for_target(target_id: str) -> str:
    target_doc = store.get_document(target_id)
    if target_doc and target_doc.doc_type == "ICD":
        return "constrained_by"
    if target_doc and target_doc.doc_type == "Requirement":
        return "derived_from"
    return "references"


def _infer_target_section_ids(target_doc_id: str, source_text: str) -> list[str]:
    target_sections = store.get_sections(target_doc_id)
    if not target_sections:
        return []

    source_tokens = _extract_trace_tokens(source_text)
    source_section_refs = _extract_section_refs(source_text)
    if not source_tokens and not source_section_refs:
        return []

    matches: list[tuple[int, str]] = []
    for section in target_sections:
        score = 0
        target_tokens = _extract_trace_tokens(_section_text(section))
        heading_ref = _extract_heading_ref(section.heading)
        if heading_ref and heading_ref in source_section_refs:
            score += 3
        if target_tokens & source_tokens:
            score += 2 * len(target_tokens & source_tokens)
        if score > 0:
            matches.append((score, section.section_id))

    matches.sort(key=lambda item: (-item[0], item[1]))
    ordered: list[str] = []
    seen_ids: set[str] = set()
    for _, section_id in matches:
        if section_id not in seen_ids:
            seen_ids.add(section_id)
            ordered.append(section_id)
    return ordered


def _section_text(section: Section) -> str:
    return "\n".join(part for part in (section.heading, section.content) if part)


def _extract_trace_tokens(text: str) -> set[str]:
    return {match.group(0) for match in _TRACE_TOKEN_RE.finditer(text)}


def _extract_section_refs(text: str) -> set[str]:
    refs = {match.group(1) for match in _SECTION_REF_RE.finditer(text)}
    heading_ref = _extract_heading_ref(text.strip())
    if heading_ref:
        refs.add(heading_ref)
    return refs


def _extract_heading_ref(text: str) -> str | None:
    match = _HEADING_REF_RE.match(text)
    return match.group(1) if match else None


class DocumentIndexer:
    """文档入库索引器：解析 → 存储 → 建关系。"""

    def __init__(self, embedding_store=None) -> None:
        self._embedding_store = embedding_store

    def ingest_document(
        self, file_path: str, metadata: dict | None = None
    ) -> DocumentNode:
        p = Path(file_path)
        ext = p.suffix.lower()
        meta = metadata or {}

        # ---- 富格式（二进制）走独立分支，不尝试 read_text ----
        if ext == ".docx":
            doc_id = meta.get("doc_id") or p.stem
            content_hash = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            return self._ingest_docx(p, doc_id, content_hash, meta)
        if ext in (".xlsx", ".csv"):
            doc_id = meta.get("doc_id") or p.stem
            content_hash = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            return self._ingest_office(p, ext, doc_id, content_hash, meta)
        if ext == ".pdf":
            doc_id = meta.get("doc_id") or p.stem
            content_hash = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            return self._ingest_pdf(p, doc_id, content_hash, meta)

        content = p.read_text(encoding="utf-8")

        # ---- 从文件名或 frontmatter/metadata 块提取 doc_id ----
        doc_id = meta.get("doc_id") or self._extract_doc_id(p.stem, content, ext)
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        if ext in (".yaml", ".yml"):
            return self._ingest_yaml(p, content, doc_id, content_hash, meta)
        return self._ingest_markdown(p, content, doc_id, content_hash, meta)

    # ---- Word (.docx) ----
    def _ingest_docx(
        self, path: Path, doc_id: str, content_hash: str, meta: dict,
    ) -> DocumentNode:
        from harnetics.parsers.docx_parser import parse_docx

        sections = parse_docx(str(path), doc_id)
        title = meta.get("title") or (sections[0].heading if sections else path.stem)
        doc = DocumentNode(
            doc_id=doc_id,
            title=title,
            doc_type=meta.get("doc_type", "Document"),
            department=meta.get("department", ""),
            system_level=meta.get("system_level", ""),
            engineering_phase=meta.get("engineering_phase", ""),
            version=meta.get("version", "v1.0"),
            status=meta.get("status", "draft"),
            content_hash=content_hash,
            file_path=str(path),
        )
        store.insert_document(doc)
        store.insert_sections(sections)
        if self._embedding_store is not None:
            self._embedding_store.index_sections(doc_id, sections)
        combined = "\n".join(s.content for s in sections)
        edges = extract_section_relations(doc_id, sections) or extract_relations(doc_id, combined)
        self._safe_insert_edges(doc_id, edges)
        return doc

    # ---- Excel (.xlsx) / CSV ----
    def _ingest_office(
        self, path: Path, ext: str, doc_id: str, content_hash: str, meta: dict,
    ) -> DocumentNode:
        if ext == ".csv":
            from harnetics.parsers.xlsx_parser import parse_csv
            sections = parse_csv(str(path), doc_id)
        else:
            from harnetics.parsers.xlsx_parser import parse_xlsx
            sections = parse_xlsx(str(path), doc_id)

        title = meta.get("title") or path.stem
        doc = DocumentNode(
            doc_id=doc_id,
            title=title,
            doc_type=meta.get("doc_type", "Document"),
            department=meta.get("department", ""),
            system_level=meta.get("system_level", ""),
            engineering_phase=meta.get("engineering_phase", ""),
            version=meta.get("version", "v1.0"),
            status=meta.get("status", "draft"),
            content_hash=content_hash,
            file_path=str(path),
        )
        store.insert_document(doc)
        store.insert_sections(sections)
        if self._embedding_store is not None:
            self._embedding_store.index_sections(doc_id, sections)
        combined = "\n".join(s.content for s in sections)
        edges = extract_section_relations(doc_id, sections) or extract_relations(doc_id, combined)
        self._safe_insert_edges(doc_id, edges)
        return doc

    # ---- PDF ----
    def _ingest_pdf(
        self, path: Path, doc_id: str, content_hash: str, meta: dict,
    ) -> DocumentNode:
        from harnetics.parsers.pdf_parser import parse_pdf

        sections = parse_pdf(str(path), doc_id)
        title = meta.get("title") or path.stem
        doc = DocumentNode(
            doc_id=doc_id,
            title=title,
            doc_type=meta.get("doc_type", "Document"),
            department=meta.get("department", ""),
            system_level=meta.get("system_level", ""),
            engineering_phase=meta.get("engineering_phase", ""),
            version=meta.get("version", "v1.0"),
            status=meta.get("status", "draft"),
            content_hash=content_hash,
            file_path=str(path),
        )
        store.insert_document(doc)
        store.insert_sections(sections)
        if self._embedding_store is not None:
            self._embedding_store.index_sections(doc_id, sections)
        combined = "\n".join(s.content for s in sections)
        edges = extract_section_relations(doc_id, sections) or extract_relations(doc_id, combined)
        self._safe_insert_edges(doc_id, edges)
        return doc

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

        edges = extract_section_relations(doc_id, sections)
        if not edges:
            edges = extract_relations(doc_id, content)
        self._safe_insert_edges(doc_id, edges)

        return doc

    # ---- YAML ----
    def _ingest_yaml(
        self, path: Path, content: str, doc_id: str,
        content_hash: str, meta: dict,
    ) -> DocumentNode:
        data = parse_yaml(content)
        fm = data.get("metadata", {}) or {}
        fm.update({k: v for k, v in meta.items() if v})
        sections: list[Section] = []

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

        edges = extract_section_relations(doc_id, sections)
        if not edges:
            edges = extract_relations(doc_id, content)
        self._safe_insert_edges(doc_id, edges)

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
    def _safe_insert_edges(source_doc_id: str, edges: list[DocumentEdge]) -> None:
        """只保留有效 target，并用最新结果替换该文档的全部 outgoing edges。"""
        valid = [e for e in edges if store.get_document(e.target_doc_id)]
        store.replace_edges_for_source(source_doc_id, valid)

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
