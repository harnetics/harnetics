# Quickstart: 草稿工作台增强

**Feature**: 006-draft-workbench-enhancement

## 前置条件

- Python 3.13+ 已安装
- Node.js 22+ 已安装
- 项目依赖已安装 (`uv sync` + `cd frontend && npm install`)

## 开发启动

```bash
# 安装新前端依赖
cd frontend && npm install react-markdown remark-gfm && cd ..

# 启动后端
uv run harnetics serve --port 8000

# 启动前端 (另一个终端)
cd frontend && npm run dev
```

## 验证清单

1. **Markdown 渲染**: 打开任意草稿详情页，确认内容以格式化 Markdown 显示（标题、列表、代码块）
2. **评估结果**: 生成新草稿后，侧栏应立即显示通过/告警/阻断统计
3. **引用来源**: 引用列表每条应显示章节标题和内容摘要（非空白）
4. **导出**: 点击导出按钮后浏览器下载 .md 文件
5. **历史列表**: 导航到 /drafts 页面，确认显示所有历史草稿及状态徽章

## 回归测试

```bash
# 后端
uv run pytest tests/ -x -q

# 特定草稿测试
uv run pytest tests/test_drafts.py tests/test_app.py -x -q
```
