FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FORGE_SERVE_FRONTEND=0 \
    FORGE_DB_PATH=/tmp/forge/fitness_app.sqlite \
    FORGE_DB_SEED_PATH=/app/fitness_app_initial_database.sqlite \
    PORT=8080

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /tmp/forge

EXPOSE 8080

CMD ["sh","-c","exec uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
