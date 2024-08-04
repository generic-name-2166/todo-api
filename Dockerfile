FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir wheels -r requirements.txt


FROM python:3.12-slim AS runner

WORKDIR /app

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

COPY src src
COPY pyproject.toml .
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8000

ENTRYPOINT [ "fastapi", "run", "src/todo_api/main.py" ]
