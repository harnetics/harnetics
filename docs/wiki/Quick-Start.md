# Quick Start

## 前置要求
- Python >= 3.12
- uv
- Node.js >= 20
- npm

## 安装
```bash
git clone https://github.com/harnetics/harnetics.git
cd harnetics
uv sync --dev
cd frontend && npm install && cd ..
```

## 启动
```bash
uv run uvicorn harnetics:create_app --factory --reload --port 8000
```

前端热更新：
```bash
cd frontend && npm run dev
```

## 验证
```bash
uv run pytest -q
cd frontend && npm run build
```
