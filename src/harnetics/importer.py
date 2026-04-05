# [INPUT]: 依赖 pathlib、frontmatter、yaml 与 Repository
# [OUTPUT]: 对外提供受控 Markdown/YAML 的解析、校验和入库服务
# [POS]: harnetics 的导入边界层
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

import frontmatter
import yaml

from harnetics.models import DocumentRecord, SectionRecord, TemplateRecord
from harnetics.repository import Repository


REQUIRED_METADATA = {
    "doc_id",
    "title",
    "version",
    "status",
    "department",
    "doc_type",
    "system_level",
    "engineering_phase",
}


@dataclass(slots=True)
class ImportResult:
    document: DocumentRecord
    section_count: int


class ImportService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def import_file(self, path: Path) -> ImportResult:
        suffix = path.suffix.lower()
        if suffix == ".md":
            document, sections, template = self._parse_markdown(path)
        elif suffix in {".yaml", ".yml"}:
            document, sections, template = self._parse_yaml(path)
        else:
            raise ValueError(f"unsupported file type: {suffix}")

        document_id = self.repository.insert_document(document)
        stored_document = replace(document, id=document_id)
        stored_sections = [
            replace(section, id=None, document_id=document_id)
            for section in sections
        ]
        self.repository.replace_sections(document_id, stored_sections)
        if template is not None:
            self.repository.upsert_template(
                replace(template, id=None, document_id=document_id),
            )
        return ImportResult(document=stored_document, section_count=len(stored_sections))

    def _parse_markdown(self, path: Path) -> tuple[DocumentRecord, list[SectionRecord], TemplateRecord | None]:
        post = frontmatter.loads(self._strip_html_comment_block(path.read_text(encoding="utf-8")))
        self._require_metadata(post.metadata)
        document = self._build_document(path, post.metadata)
        sections = [
            SectionRecord(
                id=None,
                document_id=0,
                heading="body",
                level=1,
                sequence=1,
                content=post.content,
                trace_refs="",
            )
        ]
        template = self._build_template(document, post.content) if document.doc_type == "Template" else None
        return document, sections, template

    def _parse_yaml(self, path: Path) -> tuple[DocumentRecord, list[SectionRecord], None]:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        metadata = payload.get("metadata", {})
        self._require_metadata(metadata)
        document = self._build_document(path, metadata)
        sections = [
            SectionRecord(
                id=None,
                document_id=0,
                heading=str(interface["name"]),
                level=2,
                sequence=index,
                content=yaml.safe_dump(interface, allow_unicode=True),
                trace_refs="",
            )
            for index, interface in enumerate(payload.get("interfaces", []), start=1)
        ]
        return document, sections, None

    def _build_document(self, path: Path, metadata: dict[str, object]) -> DocumentRecord:
        return DocumentRecord(
            id=None,
            doc_id=str(metadata["doc_id"]),
            title=str(metadata["title"]),
            department=str(metadata["department"]),
            doc_type=str(metadata["doc_type"]),
            system_level=str(metadata["system_level"]),
            engineering_phase=str(metadata["engineering_phase"]),
            version=str(metadata["version"]),
            status=str(metadata["status"]),
            source_path=str(path),
            imported_at=datetime.now(UTC).isoformat(),
        )

    def _build_template(self, document: DocumentRecord, structure: str) -> TemplateRecord:
        return TemplateRecord(
            id=None,
            document_id=0,
            name=document.title,
            required_sections="1. 概述\n2. 测试依据\n3. 测试项目",
            structure=structure,
        )

    def _require_metadata(self, metadata: dict[str, object]) -> None:
        missing = REQUIRED_METADATA - set(metadata.keys())
        if missing:
            raise ValueError(f"missing required metadata: {', '.join(sorted(missing))}")

    def _strip_html_comment_block(self, text: str) -> str:
        stripped = text.lstrip()
        if not stripped.startswith("<!--"):
            return text
        end = stripped.find("-->")
        if end == -1:
            return text
        return stripped[end + 3 :].lstrip("\r\n")
