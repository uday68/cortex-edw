.PHONY: install test lint run-api run-ui run-all docker-build docker-up

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

run-api:
	uvicorn cortex.api.server:app --reload --port 8000

run-ui:
	streamlit run cortex/ui/dashboard.py --server.port 8501

run-all:
	powershell -Command "Start-Process python -ArgumentList '-m uvicorn cortex.api.server:app --port 8000'; Start-Process python -ArgumentList '-m streamlit run cortex/ui/dashboard.py --server.port 8501'"

docker-build:
	docker build -t cortex-edw:latest .

docker-up:
	docker compose up --build -d
