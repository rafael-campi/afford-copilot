FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
COPY apps/api apps/api
COPY packages packages
COPY data/mercado data/mercado
COPY data/rag data/rag
RUN uv sync --frozen --no-dev --package afford-api

RUN useradd --create-home --uid 10001 afford
USER afford
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
