.PHONY: help install test health demo reset fixtures build-info docker-build docker-up clean

PYTHON ?= python

help:
	@echo "SIH26237 — Cryptographic Attribution Platform"
	@echo "Available commands:"
	@echo "  make demo         - Start full offline demo (backend + frontend)"
	@echo "  make test         - Run all test suites (integration, deployment, API)"
	@echo "  make health       - Run deployment readiness health check"
	@echo "  make reset        - Reset environment and restore baseline demo fixtures"
	@echo "  make fixtures     - Regenerate deterministic demo fixtures"
	@echo "  make build-info   - Collect system build and dependency metadata"
	@echo "  make docker-build - Build offline Docker image"
	@echo "  make docker-up    - Run containerized demo via Docker Compose"

install:
	$(PYTHON) -m pip install -r deployment/requirements.txt

test:
	$(PYTHON) -m pytest tests/test_api.py tests/test_attribution.py tests/integration tests/deployment -v

health:
	$(PYTHON) scripts/deployment/health_check.py

demo:
	$(PYTHON) scripts/deployment/start_demo.py

reset:
	$(PYTHON) scripts/deployment/reset_demo.py

fixtures:
	$(PYTHON) scripts/deployment/generate_demo_fixtures.py

build-info:
	$(PYTHON) scripts/deployment/build_info.py

docker-build:
	docker build -t sih26237:latest .

docker-up:
	docker-compose up -d

clean: reset
