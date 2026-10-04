.PHONY: install test dev dev-backend dev-frontend clean

install:
	python -m pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	PYTHONPATH=backend pytest backend/tests/ -v

dev-backend:
	python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend and frontend..."
	@echo "On Windows, run: .\\scripts\\dev.ps1"
