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
from harnetics.engine.evolution.signals import delete_signal_by_draft_id
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
        rt = request.app.state.runtime_settings
        llm_model = rt.get("llm_model")
        llm_base = rt.get("llm_base_url")
        llm_key = rt.get("llm_api_key")
        logger.info(
            "draft.generate.start subject=%r related_doc_count=%d template_id=%s source_report_id=%s llm_model=%s llm_base=%s has_api_key=%s",
            req.subject,
            len(req.related_doc_ids),
            req.template_id or "<none>",
            req.source_report_id or "<none>",
            llm_model,
            llm_base or "<default>",
            bool(llm_key),
        )
        llm = HarneticsLLM(
            model=llm_model,
            api_base=llm_base,
            api_key=llm_key or None,
        )
        logger.info(
            "draft.generate.route configured_model=%s effective_model=%s configured_base=%s effective_base=%s",
            llm_model,
            llm.model,
            llm_base or "<default>",
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
        "eval_results": json.loads(draft.eval_results_json or "[]"),
        "generated_by": getattr(draft, "generated_by", "") or "",
        "created_at": getattr(draft, "created_at", "") or "",
    }


@router.get("")
def list_drafts() -> list[dict]:
    """列出所有草稿（摘要字段 + subject + eval_summary）。"""
    with store.get_connection() as conn:
        rows = conn.execute(
            "SELECT draft_id, status, generated_by, created_at, request_json, eval_results_json FROM drafts ORDER BY created_at DESC"
        ).fetchall()
    result = []
    for r in rows:
        # 提取 subject
        subject = ""
        try:
            req = json.loads(r["request_json"] or "{}")
            subject = req.get("subject", "")
        except (json.JSONDecodeError, TypeError):
            pass
        # 统计 eval_summary
        eval_summary = None
        try:
            evals = json.loads(r["eval_results_json"] or "[]")
            if evals:
                eval_summary = {"pass": 0, "warn": 0, "block": 0}
                for ev in evals:
                    lv = ev.get("level", "")
                    if lv == "Pass":
                        eval_summary["pass"] += 1
                    elif lv == "Warning":
                        eval_summary["warn"] += 1
                    elif lv == "Blocker":
                        eval_summary["block"] += 1
        except (json.JSONDecodeError, TypeError):
            pass
        result.append({
            "draft_id": r["draft_id"],
            "status": r["status"],
            "generated_by": r["generated_by"],
            "created_at": r["created_at"],
            "subject": subject,
            "eval_summary": eval_summary,
        })
    return result


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


@router.delete("/{draft_id}", status_code=204)
def delete_draft(draft_id: str) -> None:
    """删除单条草稿记录及其进化信号。"""
    with store.get_connection() as conn:
        result = conn.execute(
            "DELETE FROM drafts WHERE draft_id = ?", (draft_id,)
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="draft not found")
        conn.commit()
    delete_signal_by_draft_id(draft_id)
