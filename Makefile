.PHONY: dev test lint migrate seed clean

dev:
	docker-compose up -d postgres redis minio
	@echo "Waiting for services to be ready..."
	@sleep 5
	@make migrate
	@echo "Starting development servers..."
	docker-compose up api worker web

test:
	@echo "Running API tests..."
	cd apps/api && pytest
	@echo "Running worker tests..."
	cd apps/worker && pytest
	@echo "Running web tests..."
	cd apps/web && npm test

lint:
	@echo "Linting Python code..."
	ruff check apps/api/src apps/worker/src packages/common/src
	mypy apps/api/src apps/worker/src packages/common/src
	@echo "Linting TypeScript code..."
	cd apps/web && npm run lint

migrate:
	@echo "Running database migrations..."
	cd apps/api && alembic upgrade head

seed:
	@echo "Seeding demo data..."
	python scripts/dev/seed_demo_data.py

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

build:
	docker-compose build

stop:
	docker-compose stop

logs:
	docker-compose logs -f

