# [INPUT]: 依赖 Repository、LLM client 与 DraftValidator
# [OUTPUT]: 对外提供 DraftService 的草稿生成、编辑后重算与 prompt 拼装能力
# [POS]: harnetics 的草稿编排服务，负责把候选来源编成可校验草稿并维护工作台状态
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from time import perf_counter

from harnetics.models import DraftRecord, GenerationRunRecord


class DraftService:
    def __init__(self, repository, llm_client, validator) -> None:
        self.repository = repository
        self.llm_client = llm_client
        self.validator = validator

    def generate(
        self,
        *,
        topic: str,
        department: str,
        target_doc_type: str,
        target_system_level: str,
        selected_document_ids: list[int],
        template_id: int,
    ):
        started = perf_counter()
        template = self.repository.get_template(template_id)
        sections = self._collect_sections(selected_document_ids)
        prompt = self._build_prompt(topic=topic, template=template, sections=sections)
        content = self.llm_client.generate_markdown(prompt=prompt)
        draft_id = self.repository.insert_draft(
            DraftRecord(
                id=None,
                topic=topic,
                department=department,
                target_doc_type=target_doc_type,
                target_system_level=target_system_level,
                status="generated",
                content_markdown=content,
                exported_at=None,
            )
        )
        self.repository.insert_generation_run(
            GenerationRunRecord(
                id=None,
                draft_id=draft_id,
                selected_document_ids=",".join(str(item) for item in selected_document_ids),
                selected_template_id=template_id,
                status="completed",
                duration_ms=int((perf_counter() - started) * 1000),
                input_summary=topic,
            )
        )
        self._refresh_state(
            draft_id=draft_id,
            selected_document_ids=selected_document_ids,
            content=content,
        )
        return self.repository.get_draft_detail(draft_id)

    def update_content(self, *, draft_id: int, content: str):
        selected_document_ids = self.repository.get_selected_document_ids_for_draft(draft_id)
        self.repository.update_draft_content(draft_id, content)
        self._refresh_state(
            draft_id=draft_id,
            selected_document_ids=selected_document_ids,
            content=content,
            reset_existing=True,
        )
        return self.repository.get_draft_detail(draft_id)

    def _collect_sections(self, selected_document_ids: list[int]) -> list[object]:
        sections: list[object] = []
        for document_id in selected_document_ids:
            detail = self.repository.get_document_detail(document_id)
            sections.extend(detail.sections)
        return sections

    def _build_prompt(self, *, topic: str, template, sections: list[object]) -> str:
        source_text = "\n".join(
            f"[SECTION:{section.id}] {section.heading}\n{section.content}"
            for section in sections
        )
        return (
            f"主题：{topic}\n"
            f"模板：{template.structure}\n"
            f"来源：\n{source_text}\n"
            "输出 Markdown，并在每个段落后添加 [CITATION:<section_id>]。"
        )

    def _refresh_state(
        self,
        *,
        draft_id: int,
        selected_document_ids: list[int],
        content: str,
        reset_existing: bool = False,
    ) -> None:
        if reset_existing:
            self.repository.clear_citations(draft_id)
            self.repository.clear_validation_issues(draft_id)
        allowed_section_ids = {
            section.id
            for section in self._collect_sections(selected_document_ids)
            if section.id is not None
        }
        citations = self.repository.attach_citations_from_markers(
            draft_id,
            content,
            allowed_section_ids=allowed_section_ids,
        )
        issues = self.validator.validate(
            selected_document_ids=selected_document_ids,
            citations=citations,
            content=content,
        )
        self.repository.insert_validation_issues(draft_id, issues)
        self.repository.update_draft_status(draft_id, self._status_for(issues))

    def _status_for(self, issues: list[object]) -> str:
        severities = {issue.severity for issue in issues}
        if "blocking" in severities:
            return "blocked"
        if "warning" in severities:
            return "warning"
        return "ready"
