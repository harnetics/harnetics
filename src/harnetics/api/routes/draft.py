"""
# [INPUT]: 依赖 engine.draft_generator.DraftGenerator、llm.client.HarneticsLLM、graph.store (drafts 表)
# [OUTPUT]: 对外提供 router: POST /api/draft/generate、GET /api/draft/{id}、GET /api/drafts、GET /api/draft/{id}/export
# [POS]: api/routes 的草稿域端点，US2 草稿生成的 HTTP 入口，显式复用 app.state.settings 的 LLM/API key，并接受 source_report_id
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from harnetics.engine.draft_generator import DraftGenerator
from harnetics.graph import store
from harnetics.llm.client import HarneticsLLM

router = APIRouter(prefix="/api/draft", tags=["draft"])
logger = logging.getLogger("uvicorn.error")


# ---- 请求体 --------------------------------------------------------

class DraftGenerateRequest(BaseModel):
    subject: str
    related_doc_ids: list[str] = Field(default_factory=list)
    template_id: str = ""
    source_report_id: str = ""
    extra: dict = Field(default_factory=dict)


# ---- 端点 ----------------------------------------------------------

@router.post("/generate")
def generate_draft(req: DraftGenerateRequest, request: Request) -> dict:
    """异步触发草稿生成（同步实现，返回完整 AlignedDraft）。"""
    request_dict = {
        "subject": req.subject,
        "related_doc_ids": req.related_doc_ids,
        "template_id": req.template_id,
        "source_report_id": req.source_report_id,
        **req.extra,
    }
    try:
        settings = request.app.state.settings
        logger.info(
            "draft.generate.start subject=%r related_doc_count=%d template_id=%s source_report_id=%s llm_model=%s llm_base=%s has_api_key=%s",
            req.subject,
            len(req.related_doc_ids),
            req.template_id or "<none>",
            req.source_report_id or "<none>",
            settings.llm_model,
            settings.llm_base_url or "<default>",
            bool(settings.llm_api_key),
        )
        llm = HarneticsLLM(
            model=settings.llm_model,
            api_base=settings.llm_base_url,
            api_key=settings.llm_api_key or None,
        )
        logger.info(
            "draft.generate.route configured_model=%s effective_model=%s configured_base=%s effective_base=%s",
            settings.llm_model,
            llm.model,
            settings.llm_base_url or "<default>",
            llm.api_base or "<default>",
        )
        draft = DraftGenerator(llm=llm).generate(request_dict)
    except Exception as exc:
        logger.exception(
            "draft.generate.failed subject=%r related_doc_count=%d template_id=%s source_report_id=%s",
            req.subject,
            len(req.related_doc_ids),
            req.template_id or "<none>",
            req.source_report_id or "<none>",
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    logger.info(
        "draft.generate.success draft_id=%s status=%s generated_by=%s citations=%d conflicts=%d",
        draft.draft_id,
        draft.status,
        getattr(draft, "generated_by", "") or "<unknown>",
        len(draft.citations),
        len(draft.conflicts),
    )

    return {
        "draft_id": draft.draft_id,
        "status": draft.status,
        "content_md": draft.content_md,
        "citations": [
            {
                "source_doc_id": c.source_doc_id,
                "source_section_id": c.source_section_id,
                "quote": c.quote,
                "confidence": c.confidence,
            }
            for c in draft.citations
        ],
        "conflicts": [
            {
                "doc_a_id": c.doc_a_id,
                "doc_b_id": c.doc_b_id,
                "description": c.description,
                "severity": c.severity,
            }
            for c in draft.conflicts
        ],
    }


@router.get("")
def list_drafts() -> list[dict]:
    """列出所有草稿（摘要字段）。"""
    with store.get_connection() as conn:
        rows = conn.execute(
            "SELECT draft_id, status, generated_by, created_at FROM drafts ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "draft_id": r["draft_id"],
            "status": r["status"],
            "generated_by": r["generated_by"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@router.get("/{draft_id}")
def get_draft(draft_id: str) -> dict:
    """获取草稿详情。"""
    with store.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM drafts WHERE draft_id = ?", (draft_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="draft not found")
    return {
        "draft_id": row["draft_id"],
        "status": row["status"],
        "content_md": row["content_md"],
        "citations": json.loads(row["citations_json"] or "[]"),
        "conflicts": json.loads(row["conflicts_json"] or "[]"),
        "eval_results": json.loads(row["eval_results_json"] or "[]"),
        "generated_by": row["generated_by"],
        "created_at": row["created_at"],
    }


@router.get("/{draft_id}/export", response_class=PlainTextResponse)
def export_draft(draft_id: str) -> str:
    """以 Markdown 格式导出草稿正文。"""
    with store.get_connection() as conn:
        row = conn.execute(
            "SELECT content_md FROM drafts WHERE draft_id = ?", (draft_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="draft not found")
    return row["content_md"]
