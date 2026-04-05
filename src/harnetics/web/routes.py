# [INPUT]: 依赖 FastAPI 请求对象、Jinja2 模板、Repository、ImportService 与 draft services
# [OUTPUT]: 对外提供文档导入、列表、详情与草稿工作流路由
# [POS]: harnetics/web 的 HTTP 入口，负责 catalog 页面与草稿生成/编辑/导出闭环
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

from fastapi import APIRouter
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import HTMLResponse
from fastapi.responses import PlainTextResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import yaml

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _normalize_filter(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return value


@router.get("/documents", response_class=HTMLResponse)
def list_documents(
    request: Request,
    department: str | None = None,
    doc_type: str | None = None,
    system_level: str | None = None,
    query: str | None = None,
):
    department = _normalize_filter(department)
    doc_type = _normalize_filter(doc_type)
    system_level = _normalize_filter(system_level)
    query = _normalize_filter(query)
    repository = request.app.state.repository
    documents = repository.list_documents(
        department=department,
        doc_type=doc_type,
        system_level=system_level,
        query=query,
    )
    return templates.TemplateResponse(
        request,
        "documents.html",
        {
            "request": request,
            "documents": documents,
            "filters": {
                "department": department or "",
                "doc_type": doc_type or "",
                "system_level": system_level or "",
                "query": query or "",
            },
        },
    )


@router.post("/documents/import")
async def import_document(request: Request, file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename:
        raise HTTPException(status_code=400, detail="missing filename")
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="invalid filename")

    safe_name = Path(filename).name
    if safe_name != filename or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="invalid filename")

    target_path = Path(request.app.state.settings.raw_upload_dir) / safe_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        raise HTTPException(status_code=400, detail="file already exists")

    target_path.write_bytes(await file.read())

    try:
        request.app.state.import_service.import_file(target_path)
    except yaml.YAMLError as exc:
        try:
            target_path.unlink()
        except FileNotFoundError:
            pass
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        try:
            target_path.unlink()
        except FileNotFoundError:
            pass
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "imported"}


@router.get("/documents/{document_id}", response_class=HTMLResponse)
def document_detail(request: Request, document_id: int):
    try:
        detail = request.app.state.repository.get_document_detail(document_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc
    return templates.TemplateResponse(
        request,
        "document_detail.html",
        {
            "request": request,
            "detail": detail,
        },
    )


@router.get("/drafts/new", response_class=HTMLResponse)
def new_draft(request: Request):
    return templates.TemplateResponse(
        request,
        "draft_new.html",
        {
            "request": request,
            "plan": None,
            "topic": "",
            "department": "",
            "target_doc_type": "",
            "target_system_level": "",
        },
    )


@router.post("/drafts/plan", response_class=HTMLResponse)
def plan_draft(
    request: Request,
    topic: str = Form(...),
    department: str = Form(...),
    target_doc_type: str = Form(...),
    target_system_level: str = Form(...),
):
    plan = request.app.state.retrieval_planner.plan(
        topic=topic,
        department=department,
        target_doc_type=target_doc_type,
        target_system_level=target_system_level,
    )
    return templates.TemplateResponse(
        request,
        "draft_new.html",
        {
            "request": request,
            "plan": plan,
            "topic": topic,
            "department": department,
            "target_doc_type": target_doc_type,
            "target_system_level": target_system_level,
        },
    )


@router.post("/drafts")
def create_draft(
    request: Request,
    topic: str = Form(...),
    department: str = Form(...),
    target_doc_type: str = Form(...),
    target_system_level: str = Form(...),
    selected_document_ids: list[int] = Form(...),
    template_id: int = Form(...),
):
    draft = request.app.state.draft_service.generate(
        topic=topic,
        department=department,
        target_doc_type=target_doc_type,
        target_system_level=target_system_level,
        selected_document_ids=selected_document_ids,
        template_id=template_id,
    )
    return RedirectResponse(f"/drafts/{draft.id}", status_code=303)


@router.get("/drafts/{draft_id}", response_class=HTMLResponse)
def show_draft(request: Request, draft_id: int):
    try:
        draft = request.app.state.repository.get_draft_detail(draft_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="draft not found") from exc
    return templates.TemplateResponse(
        request,
        "draft_show.html",
        {
            "request": request,
            "draft": draft,
            "issues": draft.issues,
            "citations": draft.citations,
        },
    )


@router.post("/drafts/{draft_id}/edit")
def update_draft(request: Request, draft_id: int, content: str = Form(...)):
    try:
        request.app.state.repository.get_draft_detail(draft_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="draft not found") from exc
    request.app.state.draft_service.update_content(draft_id=draft_id, content=content)
    return RedirectResponse(f"/drafts/{draft_id}", status_code=303)


@router.get("/drafts/{draft_id}/export")
def export_draft(request: Request, draft_id: int):
    try:
        draft = request.app.state.repository.get_draft_detail(draft_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="draft not found") from exc
    return PlainTextResponse(
        draft.content_markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="draft-{draft_id}.md"'},
    )
