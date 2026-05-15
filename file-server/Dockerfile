FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.10.2 /uv /uvx /bin/

ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY api/pyproject.toml ./api/pyproject.toml
COPY database/pyproject.toml ./database/pyproject.toml
COPY file-server/pyproject.toml ./file-server/pyproject.toml
COPY shared/pyproject.toml ./shared/pyproject.toml

COPY shared/ ./shared/
RUN uv sync --frozen --no-dev --project file-server

# Copy file-server code
COPY file-server/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
