FROM node:22-bookworm-slim AS frontend
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ARG TORCH_INDEX=cu128
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    VOICESWAP_DATA=/data VOICESWAP_ENGINE=/app/engine/rvc \
    VOICESWAP_FRONTEND=/app/frontend/dist PYTHONPATH=/app/backend \
    OMP_NUM_THREADS=4
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/${TORCH_INDEX}
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
WORKDIR /app
COPY engine/ engine/
COPY backend/ backend/
COPY --from=frontend /web/dist frontend/dist
RUN groupadd -g 1000 voiceswap && useradd -u 1000 -g voiceswap -m voiceswap && mkdir /data && chown voiceswap:voiceswap /data
USER voiceswap
EXPOSE 8000
HEALTHCHECK --interval=30s --start-period=60s --timeout=5s CMD curl -fsS http://localhost:8000/api/health || exit 1
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

