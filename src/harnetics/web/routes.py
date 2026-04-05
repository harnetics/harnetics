# [INPUT]: 依赖 FastAPI 请求对象、Jinja2 模板、Repository 与 ImportService
# [OUTPUT]: 对外提供文档导入、文档列表和文档详情路由
# [POS]: harnetics/web 的文档目录 HTTP 入口，负责 catalog 页面和上传落盘
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import HTMLResponse
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
