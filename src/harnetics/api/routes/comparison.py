"""
# [INPUT]: 依赖 FastAPI、engine.comparison_analyzer、graph.store、parsers (pdf/markdown/docx)、llm.client
# [OUTPUT]: 对外提供 router: POST /api/comparison/analyze、GET /api/comparison、GET /api/comparison/{id}、DELETE /api/comparison/{id}、GET /api/comparison/{id}/export
# [POS]: api/routes 的文档比对端点，接收双文件上传，调用 ComparisonAnalyzer，持久化并返回结构化审查意见
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse

from harnetics.engine.comparison_analyzer import ComparisonAnalyzer
from harnetics.graph import store
from harnetics.llm.client import HarneticsLLM
from harnetics.models.document import Section

router = APIRouter(prefix="/api/comparison", tags=["comparison"])

_ALLOWED_EXTS = frozenset((".pdf", ".md", ".txt", ".docx"))


# ================================================================
# 文件解析辅助
# ================================================================

def _parse_file(file_path: Path, suffix: str, doc_id: str) -> list[Section]:
    """根据扩展名调用对应解析器，返回 Section 列表。"""
    s = suffix.lower()
    if s == ".pdf":
        from harnetics.parsers.pdf_parser import parse_pdf
        return parse_pdf(str(file_path), doc_id)
    if s in (".md", ".txt"):
        from harnetics.parsers.markdown_parser import parse_markdown
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return parse_markdown(content, doc_id)
    if s == ".docx":
        from harnetics.parsers.docx_parser import parse_docx
        return parse_docx(str(file_path), doc_id)
    # 通用文本回退
    content = file_path.read_text(encoding="utf-8", errors="replace")
    return [
        Section(
            section_id=f"{doc_id}-sec-0",
            doc_id=doc_id,
            heading="全文",
            content=content,
            level=1,
            order_index=0,
        )
    ]


# ================================================================
# 序列化辅助
# ================================================================

def _section_to_dict(s: Section) -> dict:
    return {
        "section_id": s.section_id,
        "doc_id": s.doc_id,
        "heading": s.heading,
        "content": s.content,
        "level": s.level,
        "order_index": s.order_index,
    }


def _session_full(row: dict) -> dict:
    return {
        "session_id": row["session_id"],
        "req_filename": row["req_filename"],
        "resp_filename": row["resp_filename"],
        "req_sections": json.loads(row["req_sections_json"]),
        "resp_sections": json.loads(row["resp_sections_json"]),
        "analysis_md": row["analysis_md"],
        "findings": json.loads(row["findings_json"]),
        "status": row["status"],
        "created_at": row["created_at"],
    }


def _session_summary(row: dict) -> dict:
    findings = json.loads(row["findings_json"])
    covered = sum(1 for f in findings if f.get("status") == "covered")
    partial = sum(1 for f in findings if f.get("status") == "partial")
    missing = sum(1 for f in findings if f.get("status") == "missing")
    unclear = sum(1 for f in findings if f.get("status") == "unclear")
    return {
        "session_id": row["session_id"],
        "req_filename": row["req_filename"],
        "resp_filename": row["resp_filename"],
        "status": row["status"],
        "created_at": row["created_at"],
        "findings_count": len(findings),
        "covered": covered,
        "partial": partial,
        "missing": missing,
        "unclear": unclear,
    }


# ================================================================
# 路由
# ================================================================

@router.post("/analyze")
async def analyze_comparison(
    request: Request,
    req_file: UploadFile = File(..., description="要求文件（审查大纲）"),
    resp_file: UploadFile = File(..., description="应答文件（安全分析报告）"),
) -> dict:
    """上传两份文件，执行符合性比对审查，返回完整 session（含 findings）。"""
    req_filename = req_file.filename or "requirement.pdf"
    resp_filename = resp_file.filename or "response.pdf"
    req_suffix = Path(req_filename).suffix
    resp_suffix = Path(resp_filename).suffix

    if req_suffix.lower() not in _ALLOWED_EXTS:
        raise HTTPException(400, f"要求文件类型不支持：{req_suffix}，支持 {sorted(_ALLOWED_EXTS)}")
    if resp_suffix.lower() not in _ALLOWED_EXTS:
        raise HTTPException(400, f"应答文件类型不支持：{resp_suffix}，支持 {sorted(_ALLOWED_EXTS)}")

    session_id = (
        f"CMP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    )

    # ---- 保存并解析文件 ----
    req_tmp = Path(tempfile.mkdtemp()) / Path(req_filename).name
    resp_tmp = Path(tempfile.mkdtemp()) / Path(resp_filename).name
    try:
        req_tmp.write_bytes(await req_file.read())
        resp_tmp.write_bytes(await resp_file.read())
        req_sections = _parse_file(req_tmp, req_suffix, f"{session_id}-REQ")
        resp_sections = _parse_file(resp_tmp, resp_suffix, f"{session_id}-RESP")
    finally:
        req_tmp.unlink(missing_ok=True)
        resp_tmp.unlink(missing_ok=True)

    # ---- 持久化初始 session ----
    store.create_comparison_session(
        session_id=session_id,
        req_filename=req_filename,
        resp_filename=resp_filename,
        req_sections=[_section_to_dict(s) for s in req_sections],
        resp_sections=[_section_to_dict(s) for s in resp_sections],
    )

    # ---- LLM 分析 ----
    try:
        rt = request.app.state.runtime_settings
        llm = HarneticsLLM(
            model=rt.get("llm_model"),
            api_base=rt.get("llm_base_url"),
            api_key=rt.get("llm_api_key") or None,
        )
        result = ComparisonAnalyzer(llm=llm).analyze(
            session_id=session_id,
            req_sections=req_sections,
            resp_sections=resp_sections,
            req_filename=req_filename,
            resp_filename=resp_filename,
        )
        store.update_comparison_session(
            session_id=session_id,
            analysis_md=result["analysis_md"],
            findings=result["findings"],
            status="completed",
        )
    except Exception as exc:
        store.update_comparison_session(
            session_id=session_id,
            analysis_md=f"分析失败：{exc}",
            findings=[],
            status="failed",
        )
        raise HTTPException(500, f"比对分析失败：{exc}") from exc

    row = store.get_comparison_session(session_id)
    return _session_full(row)  # type: ignore[arg-type]


@router.get("")
def list_comparison_sessions() -> dict:
    rows = store.list_comparison_sessions()
    return {"sessions": [_session_summary(r) for r in rows]}


@router.get("/{session_id}/export")
def export_comparison_session(session_id: str) -> PlainTextResponse:
    row = store.get_comparison_session(session_id)
    if not row:
        raise HTTPException(404, "比对会话不存在")
    filename = f"{session_id}-审查报告.md"
    return PlainTextResponse(
        content=row["analysis_md"],
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{session_id}")
def get_comparison_session(session_id: str) -> dict:
    row = store.get_comparison_session(session_id)
    if not row:
        raise HTTPException(404, "比对会话不存在")
    return _session_full(row)


@router.delete("/{session_id}")
def delete_comparison_session(session_id: str) -> dict:
    if not store.get_comparison_session(session_id):
        raise HTTPException(404, "比对会话不存在")
    store.delete_comparison_session(session_id)
    return {"status": "deleted", "session_id": session_id}
