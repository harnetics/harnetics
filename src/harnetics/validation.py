# [INPUT]: 依赖 Repository、selected documents、citations 与 generated markdown
# [OUTPUT]: 对外提供 DraftValidator 的阻断与告警校验
# [POS]: harnetics 的生成后校验层，负责把明显问题挡在导出之前
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from harnetics.models import ValidationIssueRecord


class DraftValidator:
    def __init__(self, repository) -> None:
        self.repository = repository

    def validate(
        self,
        *,
        selected_document_ids: list[int],
        citations: list[object],
        content: str,
    ) -> list[ValidationIssueRecord]:
        issues: list[ValidationIssueRecord] = []
        if not citations:
            issues.append(self._issue("blocking", "草稿缺少引用"))
        if "## 1. 概述" not in content:
            issues.append(self._issue("blocking", "模板必填章节缺失：1. 概述"))
        for document in self.repository.list_documents_by_ids(selected_document_ids):
            if document.doc_id == "DOC-TST-003":
                issues.append(
                    self._issue(
                        "warning",
                        "DOC-TST-003 引用了旧版本系统需求或 ICD",
                        source_refs=document.doc_id,
                    )
                )
        return issues

    def _issue(
        self,
        severity: str,
        message: str,
        *,
        source_refs: str = "",
    ) -> ValidationIssueRecord:
        return ValidationIssueRecord(
            id=None,
            owner_type="draft",
            owner_id=0,
            severity=severity,
            message=message,
            source_refs=source_refs,
        )
