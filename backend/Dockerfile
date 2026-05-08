FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for psycopg2 / xgboost / lightgbm
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc libgomp1 libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Train model on first build so the container is ready to predict.
# This runs offline using the synthetic generator and writes the model bundle.
RUN python -m app.ml.train || echo "[warn] training failed at build; will fall back to heuristic"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
