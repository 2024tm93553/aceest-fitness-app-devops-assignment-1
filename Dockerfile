FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/build/deps -r requirements.txt

FROM python:3.11-slim AS production

LABEL org.opencontainers.image.title="ACEest Fitness App" \
      org.opencontainers.image.description="Fitness & Gym Management API" \
      org.opencontainers.image.version="2.0.1" \
      org.opencontainers.image.vendor="BITS Pilani" \
      org.opencontainers.image.authors="2024tm93553"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/deps \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    # Security: Disable Python's hash randomization for reproducibility
    PYTHONHASHSEED=random

WORKDIR /app

COPY --from=builder /build/deps /app/deps

COPY app.py .
COPY templates/ templates/
COPY static/ static/

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false --create-home appuser && \
    chown -R appuser:appgroup /app && \
    chmod 755 /app


USER appuser


EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9000/health', timeout=5)" || exit 1

CMD ["python", "app.py"]

