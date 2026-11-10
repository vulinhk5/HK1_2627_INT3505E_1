# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir uv && uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH
COPY pyproject.toml ./
COPY src ./src

RUN uv pip install --no-cache .


FROM python:3.12-slim AS runtime
RUN groupadd -r app && useradd -r -g app -d /app app
WORKDIR /app
COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --chown=app:app wsgi.py gunicorn.conf.py ./

COPY --chown=app:app migrations ./migrations
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_URL=sqlite:////tmp/product.db

USER app
EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/ready', timeout=2)"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
