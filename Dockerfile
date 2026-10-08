# Single-container deploy (lite runtime): builds the React frontend, then serves it from
# FastAPI with int8 ONNX models, no PyTorch, about 300 MB RAM. Fits Render's free 512 MB
# instance. Model artifacts are committed under backend/models/ (onnx/, fusion.joblib, rag/).

FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 VISASHIELD_RUNTIME=onnx ONNX_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr && rm -rf /var/lib/apt/lists/*
WORKDIR /app/backend
COPY backend/requirements-lite.txt .
RUN pip install -r requirements-lite.txt
COPY backend/ ./
COPY --from=web /web/dist /app/frontend/dist
# Render injects $PORT; default 10000 elsewhere.
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
