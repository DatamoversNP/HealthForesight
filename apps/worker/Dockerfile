# Celery worker — must include apps/api/src (tasks import uepi_api.*).
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# API requirements cover shared analytics/DB stack; add Celery explicitly.
COPY apps/api/requirements.txt ./apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt \
    reportlab python-pptx pillow

COPY apps/worker/src ./src
COPY packages/common/src ./packages/common/src
COPY apps/api/src ./apps/api/src

COPY apps/worker/docker-entrypoint-azure.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PYTHONPATH=/app/src:/app/apps/api/src:/app/packages/common/src

ENTRYPOINT ["/docker-entrypoint.sh"]
