FROM node:22-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM ghcr.io/astral-sh/uv:0.8.17@sha256:e4644cb5bd56fdc2c5ea3ee0525d9d21eed1603bccd6a21f887a938be7e85be1 AS uv-binary

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HARNETICS_GRAPH_DB_PATH=/app/var/harnetics.db \
    HARNETICS_CHROMA_DIR=/app/var/chroma \
    UV_NO_CACHE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# ---- uv 二进制：从官方镜像复制，避免依赖仓库外的本地缓存文件 ----
COPY --from=uv-binary /uv /usr/local/bin/uv

# ---- 安装项目依赖：先复制元数据与源码，再直接安装项目包 ----
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY fixtures/ ./fixtures/
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# ---- 运行时镜像：保留 API/CLI/Chroma/OpenAI 路径，省略本地 sentence-transformers + torch 大包 ----
RUN uv pip install \
        "fastapi>=0.116.0" \
        "python-frontmatter>=1.1.0" \
        "PyYAML>=6.0.2" \
        "httpx>=0.28.1" \
        "uvicorn>=0.35.0" \
        "chromadb>=0.6.0" \
        "python-dotenv>=1.0.0" \
        "typer>=0.15.0" \
        "rich>=13.9.0" \
        "openai>=1.5.0" \
        "python-multipart>=0.0.26" \
    && uv pip install --no-deps .

# ---- 运行时目录 ----
RUN mkdir -p /app/var/chroma

EXPOSE 8000

ENTRYPOINT ["python", "-m", "harnetics.cli.main"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
