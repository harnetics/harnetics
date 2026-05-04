"""
# [INPUT]: 依赖 FastAPI、engine.comparison_analyzer、engine.comparison_4step、graph.store、parsers (pdf/markdown/docx)、llm.client、datetime 时区转换
# [OUTPUT]: 对外提供 router: POST /api/comparison/analyze、POST /api/comparison/analyze-stream (SSE)、
#           POST /api/comparison/analyze-4step (SSE 四步流水线)、
#           GET /api/comparison、GET /api/comparison/{id}、DELETE /api/comparison/{id}、GET /api/comparison/{id}/export
# [POS]: api/routes 的文档比对端点，接收双文件上传，调用 ComparisonAnalyzer 或 Comparison4StepEngine，持久化并返回北京时间与结构化审查意见
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse

from harnetics.engine.comparison_analyzer import ComparisonAnalyzer
from harnetics.engine.comparison_4step import Comparison4StepEngine
from harnetics.graph import store
from harnetics.llm.client import HarneticsLLM
from harnetics.models.document import Section

router = APIRouter(prefix="/api/comparison", tags=["comparison"])
logger = logging.getLogger("harnetics.comparison.api")

_ALLOWED_EXTS = frozenset((".pdf", ".md", ".txt", ".docx"))
_BEIJING_TZ = timezone(timedelta(hours=8))
_MISSING_GLOBAL_SUMMARY = "全局结论：未生成全局结论"


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


async def _parse_uploaded_sections(
    req_file: UploadFile,
    resp_file: UploadFile,
    session_id: str,
    req_suffix: str,
    resp_suffix: str,
) -> tuple[list[Section], list[Section]]:
    """将上传文件落到临时目录后解析为章节列表。"""
    with TemporaryDirectory() as req_dir, TemporaryDirectory() as resp_dir:
        req_tmp = Path(req_dir) / Path(req_file.filename or "requirement.pdf").name
        resp_tmp = Path(resp_dir) / Path(resp_file.filename or "response.pdf").name
        req_tmp.write_bytes(await req_file.read())
        resp_tmp.write_bytes(await resp_file.read())
        req_sections = _parse_file(req_tmp, req_suffix, f"{session_id}-REQ")
        resp_sections = _parse_file(resp_tmp, resp_suffix, f"{session_id}-RESP")
    return req_sections, resp_sections


def _mark_session_failed(session_id: str, message: str) -> None:
    """统一写入失败态，避免会话只改 status 不留原因。"""
    row = store.get_comparison_session(session_id)
    if row is None:
        return
    try:
        findings = json.loads(row.get("findings_json", "[]"))
    except json.JSONDecodeError:
        findings = []
    store.update_comparison_session(
        session_id=session_id,
        analysis_md=f"分析失败：{message}",
        findings=findings,
        status="failed",
    )


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


def _to_beijing_time(value: str) -> str:
    """将 SQLite/ISO UTC 时间统一输出为北京时间字符串。"""
    raw = (value or "").strip()
    if not raw:
        return ""
    normalized = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return raw
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _fallback_global_summary(findings: list[dict]) -> str:
    covered = sum(1 for f in findings if f.get("status") == "covered")
    partial = sum(1 for f in findings if f.get("status") == "partial")
    missing = sum(1 for f in findings if f.get("status") == "missing")
    unclear = sum(1 for f in findings if f.get("status") == "unclear")
    return (
        f"自动计算：共审查{len(findings)}项，已覆盖{covered}项，部分覆盖{partial}项，"
        f"未覆盖{missing}项，待明确{unclear}项。"
    )


def _repair_legacy_global_summary(analysis_md: str, findings: list[dict]) -> str:
    """历史报告曾持久化占位全局结论，读取时用 findings 确定性修复。"""
    if _MISSING_GLOBAL_SUMMARY not in analysis_md:
        return analysis_md
    return analysis_md.replace(_MISSING_GLOBAL_SUMMARY, f"全局结论：{_fallback_global_summary(findings)}")


def _normalized_comparison_row(row: dict) -> dict:
    findings = json.loads(row["findings_json"])
    normalized = dict(row)
    normalized["findings_json"] = json.dumps(findings, ensure_ascii=False)
    if "analysis_md" in normalized:
        normalized["analysis_md"] = _repair_legacy_global_summary(row["analysis_md"], findings)
    normalized["created_at"] = _to_beijing_time(row["created_at"])
    if "analysis_md" in normalized and normalized["analysis_md"] != row["analysis_md"]:
        store.update_comparison_session(
            session_id=row["session_id"],
            analysis_md=normalized["analysis_md"],
            findings=findings,
            status=row["status"],
        )
    return normalized


def _session_full(row: dict) -> dict:
    row = _normalized_comparison_row(row)
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
    row = _normalized_comparison_row(row)
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
    req_sections, resp_sections = await _parse_uploaded_sections(
        req_file, resp_file, session_id, req_suffix, resp_suffix
    )

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


# ================================================================
# 流式 SSE 路由
# ================================================================

@router.post("/analyze-stream")
async def analyze_comparison_stream(
    request: Request,
    req_file: UploadFile = File(..., description="要求文件（审查大纲）"),
    resp_file: UploadFile = File(..., description="应答文件（安全分析报告）"),
) -> StreamingResponse:
    """上传两份文件，以 SSE 流式推送分批审查进度。

    事件格式：data: {JSON}\\n\\n
    事件类型：started / batch_progress / completed / error
    """
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

    logger.info(
        "comparison.api.stream.start session_id=%s req_filename=%s resp_filename=%s",
        session_id,
        req_filename,
        resp_filename,
    )

    # ---- 保存并解析文件 ----
    req_sections, resp_sections = await _parse_uploaded_sections(
        req_file, resp_file, session_id, req_suffix, resp_suffix
    )

    store.create_comparison_session(
        session_id=session_id,
        req_filename=req_filename,
        resp_filename=resp_filename,
        req_sections=[_section_to_dict(s) for s in req_sections],
        resp_sections=[_section_to_dict(s) for s in resp_sections],
    )
    store.append_comparison_findings(session_id, [], "analyzing")

    logger.info(
        "comparison.api.stream.session_created session_id=%s req_sections=%d resp_sections=%d",
        session_id,
        len(req_sections),
        len(resp_sections),
    )

    rt = request.app.state.runtime_settings
    llm = HarneticsLLM(
        model=rt.get("llm_model"),
        api_base=rt.get("llm_base_url"),
        api_key=rt.get("llm_api_key") or None,
    )
    analyzer = ComparisonAnalyzer(llm=llm)

    def _event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _generate():
        try:
            for event in analyzer.analyze_streaming(
                session_id=session_id,
                req_sections=req_sections,
                resp_sections=resp_sections,
                req_filename=req_filename,
                resp_filename=resp_filename,
            ):
                if event["type"] == "batch_progress":
                    logger.info(
                        "comparison.api.stream.batch_progress session_id=%s batch=%s/%s batch_findings=%d total_findings=%d missing_filled=%s extra_ignored=%s",
                        session_id,
                        event.get("batch"),
                        event.get("total_batches"),
                        len(event.get("batch_findings", [])),
                        event.get("total_findings", 0),
                        event.get("missing_filled", 0),
                        event.get("extra_ignored", 0),
                    )
                    store.append_comparison_findings(
                        session_id, event["batch_findings"], "analyzing"
                    )
                elif event["type"] == "completed":
                    logger.info(
                        "comparison.api.stream.completed session_id=%s total_findings=%d",
                        session_id,
                        event.get("total_findings", 0),
                    )
                    store.update_comparison_session(
                        session_id=session_id,
                        analysis_md=event["analysis_md"],
                        findings=event["findings"],
                        status="completed",
                    )
                elif event["type"] == "error" and event.get("batch") is None:
                    # 全局错误（非单批）
                    logger.error(
                        "comparison.api.stream.global_error session_id=%s message=%s",
                        session_id,
                        event.get("message", ""),
                    )
                    _mark_session_failed(session_id, event.get("message", "未知错误"))

                yield _event(event)
        except Exception as exc:  # noqa: BLE001
            logger.exception("comparison.api.stream.abort session_id=%s", session_id)
            _mark_session_failed(session_id, str(exc))
            yield _event({"type": "error", "message": str(exc)})

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        },
    )


# ================================================================
# 四步流水线 SSE 路由
# ================================================================

@router.post("/analyze-4step")
async def analyze_comparison_4step(
    request: Request,
    req_file: UploadFile = File(..., description="要求文件（审查大纲）"),
    resp_file: UploadFile = File(..., description="应答文件（安全分析报告）"),
) -> StreamingResponse:
    """四步流水线比对审查（向量匹配增强）：SSE 推送步骤事件。

    步骤事件类型：
      step_started      — 步骤开始（step: 1~4）
      scanning_done     — 步骤1完成（需求列表）
      matching_progress — 步骤2进度
      finding_batch     — 步骤3每批评估结果
      review_done       — 步骤4全局校验完成
      completed         — 全部完成
      error             — 错误
    """
    req_filename = req_file.filename or "requirement.pdf"
    resp_filename = resp_file.filename or "response.pdf"
    req_suffix = Path(req_filename).suffix
    resp_suffix = Path(resp_filename).suffix

    if req_suffix.lower() not in _ALLOWED_EXTS:
        raise HTTPException(400, f"要求文件类型不支持：{req_suffix}，支持 {sorted(_ALLOWED_EXTS)}")
    if resp_suffix.lower() not in _ALLOWED_EXTS:
        raise HTTPException(400, f"应答文件类型不支持：{resp_suffix}，支持 {sorted(_ALLOWED_EXTS)}")

    session_id = (
        f"CMP4-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    )

    logger.info(
        "comparison.api.4step.start session_id=%s req=%s resp=%s",
        session_id, req_filename, resp_filename,
    )

    # ---- 保存并解析文件 ----
    req_sections, resp_sections = await _parse_uploaded_sections(
        req_file, resp_file, session_id, req_suffix, resp_suffix
    )

    store.create_comparison_session(
        session_id=session_id,
        req_filename=req_filename,
        resp_filename=resp_filename,
        req_sections=[_section_to_dict(s) for s in req_sections],
        resp_sections=[_section_to_dict(s) for s in resp_sections],
    )
    store.append_comparison_findings(session_id, [], "analyzing")

    logger.info(
        "comparison.api.4step.session_created session_id=%s req_sections=%d resp_sections=%d",
        session_id, len(req_sections), len(resp_sections),
    )

    rt = request.app.state.runtime_settings
    llm = HarneticsLLM(
        model=rt.get("llm_model"),
        api_base=rt.get("llm_base_url"),
        api_key=rt.get("llm_api_key") or None,
    )
    engine = Comparison4StepEngine(
        llm=llm,
        embedding_model=rt.get("embedding_model") or "",
        embedding_api_key=rt.get("embedding_api_key") or "",
        embedding_base_url=rt.get("embedding_base_url") or "",
    )

    def _event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _generate():
        try:
            for event in engine.analyze_4step_streaming(
                session_id=session_id,
                req_sections=req_sections,
                resp_sections=resp_sections,
                req_filename=req_filename,
                resp_filename=resp_filename,
            ):
                etype = event.get("type")
                if etype == "finding_batch":
                    logger.info(
                        "comparison.api.4step.finding_batch session_id=%s evaluated=%s/%s",
                        session_id, event.get("evaluated"), event.get("total"),
                    )
                    store.append_comparison_findings(
                        session_id, event.get("findings", []), "analyzing"
                    )
                elif etype == "completed":
                    logger.info(
                        "comparison.api.4step.completed session_id=%s findings=%d",
                        session_id, event.get("total_findings", 0),
                    )
                    store.update_comparison_session(
                        session_id=session_id,
                        analysis_md=event.get("analysis_md", ""),
                        findings=event.get("findings", []),
                        status="completed",
                    )
                elif etype == "error":
                    logger.error(
                        "comparison.api.4step.error session_id=%s message=%s",
                        session_id, event.get("message", ""),
                    )
                    _mark_session_failed(session_id, event.get("message", "未知错误"))

                yield _event(event)
        except Exception as exc:  # noqa: BLE001
            logger.exception("comparison.api.4step.abort session_id=%s", session_id)
            _mark_session_failed(session_id, str(exc))
            yield _event({"type": "error", "message": str(exc)})

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("")
def list_comparison_sessions() -> dict:
    rows = store.list_comparison_sessions()
    return {"sessions": [_session_summary(r) for r in rows]}


@router.get("/{session_id}/export")
def export_comparison_session(session_id: str) -> PlainTextResponse:
    row = store.get_comparison_session(session_id)
    if not row:
        raise HTTPException(404, "比对会话不存在")
    row = _normalized_comparison_row(row)
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
