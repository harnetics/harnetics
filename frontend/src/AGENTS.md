# src/
> L2 | 父级: /frontend/AGENTS.md

成员清单
App.tsx: 根路由装配，串联 Header/Footer 与 9 个页面路由。
main.tsx: React 挂载入口。
index.css: Tailwind v4 主题变量与全局样式。
vite-env.d.ts: Vite 客户端类型声明。

components/: 共享布局与基础 UI 组件。
pages/: 路由页实现，承接后端 API 数据。
context/: React Context 提供者目录，当前含主题状态 ThemeContext.tsx。
lib/: 工具与 API 通信层。
types/: 前端领域类型真相源。
data/: 原型 mock 数据参考。

法则: 页面只编排状态与视图；数据契约统一收口到 lib/types。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
