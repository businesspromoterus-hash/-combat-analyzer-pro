FROM python:3.11-slim

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar deps primero (cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Crear directorios runtime
RUN mkdir -p uploads reports

# Railway inyecta $PORT dinámicamente
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Usa $PORT si está disponible (Railway), 8000 si no (local)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
