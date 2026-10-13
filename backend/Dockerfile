FROM python:3.12-slim
WORKDIR /opt/project
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt backend/requirements-lock.txt /tmp/backend/
COPY ml/requirements.txt /tmp/ml/requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend/requirements.txt -r /tmp/ml/requirements.txt
COPY backend ./backend
COPY ml/*.py ml/protocol.json ml/requirements.txt ./ml/
COPY ml/artifacts/uci-retail-v1-0cc2a83c3e40 ./ml/artifacts/uci-retail-v1-0cc2a83c3e40
COPY docs/research/results/*.json ./docs/research/results/
COPY data/processed/phase4/development.csv ./data/processed/phase4/development.csv
ENV PYTHONPATH=/opt/project:/opt/project/backend
WORKDIR /opt/project/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
