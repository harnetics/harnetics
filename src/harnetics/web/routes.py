# [INPUT]: 依赖 fastapi.APIRouter
# [OUTPUT]: 对外提供 web 路由的最小挂载点
# [POS]: harnetics/web 的 HTTP 入口壳，供后续 Task 4 扩展
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from fastapi import APIRouter


router = APIRouter()
