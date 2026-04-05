# [INPUT]: 依赖 Repository 查询出的文档与模板记录
# [OUTPUT]: 对外提供 tokenize、RetrievalPlan 与 RetrievalPlanner
# [POS]: harnetics 的候选检索规划器，负责“先选来源，再生成草稿”
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from dataclasses import dataclass
import re


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+")


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


@dataclass(slots=True)
class RetrievalPlan:
    template: object
    documents: list[object]


class RetrievalPlanner:
    def __init__(self, repository) -> None:
        self.repository = repository

    def plan(
        self,
        topic: str,
        department: str,
        target_doc_type: str,
        target_system_level: str,
    ) -> RetrievalPlan:
        topic_tokens = tokenize(topic)
        candidates = [
            document
            for document in self.repository.list_documents()
            if document.doc_type != "Template"
        ]
        ranked = sorted(
            candidates,
            key=lambda document: self._score(
                document=document,
                topic_tokens=topic_tokens,
                department=department,
                target_doc_type=target_doc_type,
                target_system_level=target_system_level,
            ),
            reverse=True,
        )
        return RetrievalPlan(
            template=self.repository.get_default_template(),
            documents=ranked[:5],
        )

    def _score(
        self,
        *,
        document,
        topic_tokens: set[str],
        department: str,
        target_doc_type: str,
        target_system_level: str,
    ) -> tuple[int, int, int, int, int]:
        title_tokens = tokenize(document.title)
        return (
            len(topic_tokens & title_tokens),
            int(document.department == department),
            int(document.doc_type == target_doc_type),
            int(document.system_level == target_system_level),
            -(document.id or 0),
        )
