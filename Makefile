.DEFAULT_GOAL := help
.PHONY: help install run test lint format check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Sync dependencies (incl. dev group)
	uv sync

run: ## Start the web app on http://127.0.0.1:8011
	uv run python -m speech_to_text.web

test: ## Run the test suite
	uv run pytest

lint: ## Lint with ruff
	uv run ruff check .

format: ## Format with ruff
	uv run ruff format .

check: lint test ## Lint then run tests

clean: ## Remove caches
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
