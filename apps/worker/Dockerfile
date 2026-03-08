FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL and build tools
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY apps/worker/pyproject.toml ./pyproject.toml
COPY packages/common/pyproject.toml ./packages/common/pyproject.toml

# Install Python dependencies using pip (more reliable than poetry in Docker)
RUN pip install --no-cache-dir poetry && \
    poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir \
        celery[redis] \
        redis \
        sqlalchemy \
        alembic \
        pydantic \
        pydantic-settings \
        psycopg2-binary \
        boto3 \
        polars \
        pyarrow \
        pandas \
        scikit-learn \
        azure-storage-blob \
        azure-identity

# Copy application code
COPY apps/worker/src ./src
COPY packages/common/src ./packages/common/src

# Set Python path
ENV PYTHONPATH=/app/src:/app/packages/common/src

# Run worker (PYTHONPATH includes /app/src, so uepi_worker is importable)
CMD ["celery", "-A", "uepi_worker.main", "worker", "--loglevel=info"]
