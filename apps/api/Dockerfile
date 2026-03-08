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
COPY apps/api/pyproject.toml ./pyproject.toml
COPY packages/common/pyproject.toml ./packages/common/pyproject.toml

# Install Python dependencies using pip (more reliable than poetry in Docker)
RUN pip install --no-cache-dir poetry && \
    poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir \
        fastapi \
        uvicorn[standard] \
        python-multipart \
        sqlalchemy \
        alembic \
        "pydantic[email]" \
        pydantic-settings \
        python-jose[cryptography] \
        httpx \
        requests \
        psycopg2-binary \
        redis \
        boto3 \
        polars \
        pyarrow \
        pandas \
        azure-storage-file-share \
        prometheus-client

# Copy application code
COPY apps/api/src ./src
COPY packages/common/src ./packages/common/src

# Set Python path (CRITICAL - this ensures uepi_api is importable)
ENV PYTHONPATH=/app/src:/app/packages/common/src

# Set storage path to /home/data (persistent in Azure App Service)
ENV STORAGE_PATH=/home/data

# Create data directory with proper permissions
RUN mkdir -p /home/data && chmod 777 /home/data

# Expose port (Azure App Service will set PORT env var)
EXPOSE 8000

# Note: Removed HEALTHCHECK - Azure App Service handles health checks differently

# Copy startup script (with debug output)
COPY apps/api/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Run application using startup script (provides debug output)
# Use exec form for better signal handling in Azure
# Azure App Service may not properly handle /bin/sh, so use direct python call as fallback
CMD ["sh", "-c", "/app/start.sh"]
