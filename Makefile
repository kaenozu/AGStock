# AGStockプロジェクトのためのMakefile

.PHONY: help install test test-cov lint format check mypy pre-commit-setup pre-commit-run clean clean-pyc clean-build docs

# デルプを表示
help:
	@echo "Makefile for AGStock project"
	@echo ""
	@echo "Targets:"
	@echo "  install          - Install dependencies and pre-commit hooks"
	@echo "  test             - Run tests"
	@echo "  test-cov         - Run tests with coverage"
	@echo "  lint             - Run linters (flake8, black check)"
	@echo "  format           - Format code with black"
	@echo "  check            - Run all checks (lint, type check, tests)"
	@echo "  mypy             - Run type checker"
	@echo "  pre-commit-setup - Setup pre-commit hooks"
	@echo "  pre-commit-run   - Run pre-commit hooks manually"
	@echo "  clean            - Remove all temporary files"
	@echo "  docs             - Build documentation"

# 依存関係をインストール
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

# テストを実行
test:
	python -m pytest tests/

# テストをカバレッジ付きで実行
test-cov:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

# リントを実行
lint:
	flake8 src/
	flake8 tests/
	black --check src/
	black --check tests/

# コードをフォーマット
format:
	black src/
	black tests/

# すべてのチェックを実行
check: lint mypy test

# 型チェックを実行
mypy:
	mypy --package src
	mypy --package tests

# pre-commitをセットアップ
pre-commit-setup:
	pre-commit install

# pre-commitを手動で実行
pre-commit-run:
	pre-commit run --all-files

# 一時ファイルを削除
clean: clean-pyc clean-build
	rm -rf .pytest_cache/
	rm -rf .benchmarks/
	rm -rf .cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.log
	rm -rf logs/*

# Pythonのキャッシュファイルを削除
clean-pyc:
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '*~' -delete
	find . -name '__pycache__' -delete

# ビルドファイルを削除
clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# ドキュメントをビルド
docs:
	pdoc src/ -o docs/gen/

# Docker関連のタスク
docker-build:
	docker build -t agstock .

docker-run:
	docker run -it --rm -p 8501:8501 agstock

docker-dev:
	docker-compose up --build

# デプロイ関連のタスク
setup-venv:
	python -m venv venv
	venv\Scripts\activate
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# マートシステム起動
start-system:
	python run_all.py

# バックテスト実行
run-backtest:
	python -c "from src.backtester import Backtester; bt = Backtester(); print('Backtester initialized successfully')"

# モーフンステスト実行
benchmark:
	python benchmark_accuracy.py