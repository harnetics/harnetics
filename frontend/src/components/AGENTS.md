# components/
> L2 | 父级: /frontend/src/AGENTS.md

成员清单
Header.tsx: 全局导航栏，负责主路由入口与当前页高亮。
Footer.tsx: 全局页脚。
Hero.tsx: 原型首页 hero，当前未接入生产路由。
MarkdownRenderer.tsx: 通用 Markdown 渲染组件，封装 react-markdown + remark-gfm + Tailwind prose 样式。
ui/: 基础 UI 组件源码副本（shadcn 风格）。

法则: 组件保持无业务副作用；路由与数据获取留在 pages/。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
