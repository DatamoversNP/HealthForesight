# HealthForesight API - Docker image (dependencies at build time, no Oryx/startup timeout)
FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2 and optional libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy API and shared package (from repo root context)
COPY apps/api/requirements.txt ./apps/api/
COPY apps/api/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
COPY apps/api/src ./apps/api/src
COPY apps/api/alembic ./apps/api/alembic
COPY apps/api/alembic.ini ./apps/api/
COPY packages/common/src ./packages/common/src
# What-if / simulate runs inline on the API via BackgroundTasks and imports uepi_worker.whatif
COPY apps/worker/src ./apps/worker/src

# Install Python dependencies at build time (avoids 10-min startup on Azure)
RUN pip install --no-cache-dir -r apps/api/requirements.txt

WORKDIR /app/apps/api/src
ENV PYTHONPATH=/app/apps/api/src:/app/packages/common/src:/app/apps/worker/src
# Do not set PORT here — Azure injects it. Default 8080 only in entrypoint when unset.
EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
