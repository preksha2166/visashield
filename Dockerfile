# Single-container deploy: builds the React frontend, then serves it from FastAPI.
# Works on Hugging Face Spaces (Docker SDK, port 7860) or any container host.
# Requires trained artifacts in backend/models/ (classifier/, baseline.joblib, fusion.joblib, rag/).

FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/tmp/hf
WORKDIR /app/backend
COPY backend/requirements.txt .
# CPU-only torch keeps the image small.
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1 \
 && grep -v "^torch==" requirements.txt | grep -v "^datasets==" > req.txt \
 && pip install -r req.txt
COPY backend/ ./
COPY --from=web /web/dist /app/frontend/dist
# Pre-download the embedding and OCR models at build time so startup is fast.
RUN python -c "from app.rag.index import embed; embed(['warm up'])" \
 && python -c "import easyocr; easyocr.Reader(['en'], gpu=False, verbose=False)"
EXPOSE 7860
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
