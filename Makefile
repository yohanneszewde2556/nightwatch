# Nightwatch - Autonomous AI On-Call Engineer
.PHONY: help install seed check test backend frontend dev build clean

help:
	@echo "Available commands:"
	@echo "  make install   - Install backend and frontend dependencies"
	@echo "  make seed      - Seed SQLite database with sample services and incidents"
	@echo "  make check     - Run setup & credentials integration check"
	@echo "  make test      - Run backend unit and integration test suite"
	@echo "  make backend   - Start FastAPI backend server on port 8000"
	@echo "  make frontend  - Start Vite React frontend server on port 5173"
	@echo "  make dev       - Start both backend and frontend development servers"
	@echo "  make build     - Build frontend production distribution"

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

seed:
	python backend/seed.py

check:
	python scripts/check_setup.py

test:
	python -m pytest backend/tests -v

backend:
	python -m uvicorn app.main:app --app-dir backend --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting Nightwatch Backend on :8000 and Frontend on :5173..."
	python -c "import subprocess, sys; b = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--app-dir', 'backend', '--reload', '--port', '8000']); f = subprocess.Popen(['npm', 'run', 'dev'], cwd='frontend', shell=True); [p.wait() for p in (b, f)]"

build:
	cd frontend && npm run build

clean:
	python -c "import shutil, glob, os; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + glob.glob('.pytest_cache') + glob.glob('frontend/dist')]"
