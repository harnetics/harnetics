FROM python:3.12-slim

# ---- 系统依赖 ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

# ---- pip + uv ----
RUN pip install --no-cache-dir uv

WORKDIR /app

# ---- 依赖层（先复制 pyproject.toml，利用 Docker 缓存）----
COPY pyproject.toml ./
RUN uv pip install --system --no-cache-dir -e ".[dev]" 2>/dev/null || \
    uv pip install --system --no-cache-dir \
        "fastapi>=0.116.0" \
        "python-multipart>=0.0.26" \
        "python-frontmatter>=1.1.0" \
        "PyYAML>=6.0.2" \
        "httpx>=0.28.1" \
        "uvicorn>=0.35.0" \
        "openai>=1.5.0" \
        "chromadb>=0.6.0" \
        "sentence-transformers>=3.4.0" \
        "python-dotenv>=1.0.0" \
        "typer>=0.15.0" \
        "rich>=13.9.0"

# ---- 源码 ----
COPY src/ ./src/
COPY fixtures/ ./fixtures/

# ---- 运行时目录 ----
RUN mkdir -p var/chroma

ENV PYTHONPATH=/app/src
ENV HARNETICS_GRAPH_DB_PATH=/app/var/harnetics.db
ENV HARNETICS_CHROMA_DIR=/app/var/chroma

EXPOSE 8000

ENTRYPOINT ["python", "-m", "harnetics.cli.main"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
