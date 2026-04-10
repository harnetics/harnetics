# frontend/
> L2 | 父级: /AGENTS.md

React 18 + TypeScript 5.7 + Vite 6 + Tailwind CSS v4 + shadcn/ui (amethyst-haze) SPA 前端

## 成员清单

.gitignore: node_modules 与 dist 排除
index.html: Vite 入口 HTML
package.json: 依赖声明 (react/react-dom/react-router-dom/shadcn-ui/lucide-react/tailwind)
tsconfig.json: TypeScript 根配置
tsconfig.app.json: App 代码 TypeScript 配置
tsconfig.node.json: Node 工具链 TypeScript 配置
vite.config.ts: Vite 构建 + Tailwind v4 插件 + /api 代理 → localhost:8000

src/App.tsx: 根组件，BrowserRouter 路由表 (9 路由)
src/main.tsx: ReactDOM 入口
src/index.css: Tailwind v4 + amethyst-haze 主题变量
src/vite-env.d.ts: Vite 类型声明

src/types/index.ts: 全部前端领域类型 (Document/Section/Edge/Draft/Impact/Dashboard)
src/lib/api.ts: fetch 封装 — fetchDocuments/fetchDocument/fetchDraft/generateDraft 等
src/lib/utils.ts: cn() Tailwind 合并工具

src/components/Header.tsx: 导航栏 (react-router-dom Link)
src/components/Footer.tsx: 页脚
src/components/Hero.tsx: 首页英雄区 (未使用)
src/components/ui/*.tsx: 13 个 shadcn/ui 组件 (alert/badge/button/card/input/label/progress/scroll-area/select/separator/table/tabs/textarea)

src/pages/Dashboard.tsx: 仪表盘 — 调用 /api/status
src/pages/Documents.tsx: 文档库列表 — 调用 /api/documents
src/pages/DocumentDetail.tsx: 文档详情 — 调用 /api/documents/:id
src/pages/DraftNew.tsx: 草稿创建工作台 — 调用 /api/draft/generate
src/pages/DraftShow.tsx: 草稿详情 — 调用 /api/draft/:id
src/pages/Impact.tsx: 影响分析首页 — 调用 /api/impact
src/pages/ImpactReport.tsx: 影响报告详情 — 调用 /api/impact/:id
src/pages/Graph.tsx: 文档图谱 SVG — 调用 /api/graph
src/pages/DesignSystem.tsx: 设计系统展示页 (静态)

src/data/mock.ts: prototype2 原始 mock 数据 (开发参考用)

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
