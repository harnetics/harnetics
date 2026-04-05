# harnetics/web/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
routes.py: FastAPI `APIRouter` 挂载点，承载文档导入、列表筛选、详情与草稿生成/编辑/导出路由。
templates/: Jinja2 模板目录，承载 catalog 页面、草稿创建页、草稿工作台与页面母版。

法则: HTTP 层只编排请求与响应，检索、生成与校验留在上层服务。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
