# UEPI - Utilization Elasticity & Policy Impact Intelligence

A cloud-agnostic SaaS platform for analyzing healthcare policy impacts, utilization patterns, and provider behavior.

## Architecture

- **Backend**: Python + FastAPI (API), Celery/Arq (jobs), SQLAlchemy, Pydantic
- **Frontend**: React + TypeScript + Vite + MUI
- **Data**: PostgreSQL (metadata), S3-compatible object storage (Parquet)
- **Analytics**: Polars/DuckDB for MVP
- **Auth**: OIDC (Azure AD, Okta, Auth0, Google)
- **Infrastructure**: Kubernetes + Terraform + Helm
- **Observability**: OpenTelemetry + Prometheus + Grafana + Loki

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Make

### Local Development

```bash
# Start all services
make dev

# Run tests
make test

# Run linters
make lint

# Run database migrations
make migrate

# Seed demo data
make seed
```

### Services

- **API**: http://localhost:8000
- **Web**: http://localhost:3050
- **MinIO Console**: http://localhost:9001 (admin/admin123)
- **PostgreSQL**: localhost:5432 (uepi/uepi)
- **Redis**: localhost:6379

## Project Structure

```
uepi/
├── apps/
│   ├── api/          # FastAPI service
│   ├── worker/       # Background jobs
│   └── web/          # React frontend
├── packages/
│   └── common/       # Shared Python code
├── infra/
│   ├── terraform/    # Infrastructure as Code
│   └── helm/         # Kubernetes deployments
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── docker-compose.yml
```

## Documentation

- [Architecture](./docs/architecture.md)
- [API Documentation](./docs/api.md)
- [Data Model](./docs/data-model.md)
- [Runbook](./docs/runbook.md)
- [Threat Model](./docs/threat-model.md)

## Development Workflow

1. Create feature branch
2. Make changes
3. Run tests and linters
4. Submit PR (triggers CI)
5. Merge to main (deploys to staging)

## License

Proprietary

