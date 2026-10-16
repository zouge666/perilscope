FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev
ENV PATH="/app/.venv/bin:$PATH" DATA_DIR=/app/data
EXPOSE 8000
CMD ["uvicorn", "loss_experience.main:app", "--host", "0.0.0.0", "--port", "8000"]
