.PHONY: help install install-dev test test-cov lint format clean server export-openapi watch-api generate-clients setup-hooks docker-build docker-run docker-dev docker-stop docker-logs docker-clean

help:
	@echo "md2cf - Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  make install      - Install package"
	@echo "  make install-dev  - Install package with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make server       - Start REST API server (with auto-reload)"
	@echo "  make watch-api    - Watch API changes and auto-export OpenAPI"
	@echo "  make setup-hooks  - Setup git pre-commit hooks"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make lint         - Run linters (ruff, mypy)"
	@echo "  make format       - Format code (black, isort)"
	@echo ""
	@echo "API & Clients:"
	@echo "  make export-openapi    - Export OpenAPI schema"
	@echo "  make validate-openapi  - Validate OpenAPI schema"
	@echo "  make generate-clients  - Generate client libraries"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build      - Build Docker image"
	@echo "  make docker-run        - Run production container"
	@echo "  make docker-dev        - Run development container"
	@echo "  make docker-stop       - Stop all containers"
	@echo "  make docker-logs       - Show container logs"
	@echo "  make docker-clean      - Remove containers and images"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove build artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=md2cf --cov-report=html --cov-report=term

lint:
	ruff check md2cf tests
	mypy md2cf

format:
	black md2cf tests examples
	isort md2cf tests examples

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# REST API commands
server:
	uvicorn md2cf.rest_api:app --host 0.0.0.0 --port 8000 --reload

server-prod:
	gunicorn md2cf.rest_api:app \
		--workers 4 \
		--worker-class uvicorn.workers.UvicornWorker \
		--bind 0.0.0.0:8000

export-openapi:
	@echo "Exporting OpenAPI schema..."
	@python scripts/export-openapi.py openapi.json
	@echo "✅ Done"

watch-api:
	@python scripts/watch-and-export.py

validate-openapi: export-openapi
	@echo "Validating OpenAPI schema..."
	@python -c "import json; json.load(open('openapi.json'))" && echo "✅ Valid JSON"

generate-clients: export-openapi
	@./generate-clients.sh

# Git hooks
setup-hooks:
	@echo "Setting up git hooks..."
	@mkdir -p .git/hooks
	@echo '#!/bin/bash' > .git/hooks/pre-commit
	@echo 'make export-openapi' >> .git/hooks/pre-commit
	@echo 'git add openapi.json' >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook installed"

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t md2cf-rest:latest -f Dockerfile .
	@echo "✅ Image built: md2cf-rest:latest"

docker-build-dev:
	@echo "Building development Docker image..."
	docker build -t md2cf-rest:dev -f Dockerfile.dev .
	@echo "✅ Image built: md2cf-rest:dev"

docker-run:
	@echo "Starting production container..."
	docker run -d \
		--name md2cf-api \
		-p 8000:8000 \
		--restart unless-stopped \
		md2cf-rest:latest
	@echo "✅ Container started: md2cf-api"
	@echo "   API URL: http://localhost:8000"
	@echo "   Health: http://localhost:8000/health"
	@echo "   Docs: http://localhost:8000/docs"

docker-dev:
	@echo "Starting development container with docker-compose..."
	docker compose --profile dev up -d api-dev
	@echo "✅ Development container started"
	@echo "   API URL: http://localhost:8000"
	@echo "   Debug port: 5678"
	@echo "   Logs: make docker-logs"

docker-compose-up:
	@echo "Starting all services with docker-compose..."
	docker compose up -d
	@echo "✅ Services started"

docker-compose-dev:
	@echo "Starting development services..."
	docker compose --profile dev up -d
	@echo "✅ Development services started"
	@echo "   API: http://localhost:8000"
	@echo "   Watcher is monitoring for changes"

docker-stop:
	@echo "Stopping containers..."
	docker compose down
	-docker stop md2cf-api 2>/dev/null || true
	-docker rm md2cf-api 2>/dev/null || true
	@echo "✅ Containers stopped"

docker-logs:
	@docker compose logs -f api || docker logs -f md2cf-api

docker-logs-dev:
	@docker compose logs -f api-dev

docker-shell:
	@docker exec -it md2cf-api /bin/bash || \
		docker run --rm -it md2cf-rest:latest /bin/bash

docker-clean:
	@echo "Cleaning up Docker resources..."
	docker compose down -v
	-docker stop md2cf-api 2>/dev/null || true
	-docker rm md2cf-api 2>/dev/null || true
	-docker rmi md2cf-rest:latest md2cf-rest:dev 2>/dev/null || true
	@echo "✅ Docker resources cleaned"

docker-rebuild: docker-clean docker-build
	@echo "✅ Image rebuilt"

docker-test:
	@echo "Testing Docker image..."
	@docker build -t md2cf-rest:test -f Dockerfile .
	@docker run --rm -d --name md2cf-test -p 8001:8000 md2cf-rest:test
	@sleep 3
	@curl -f http://localhost:8001/health && echo "\n✅ Container is healthy" || echo "\n❌ Health check failed"
	@docker stop md2cf-test
	@docker rmi md2cf-rest:test
