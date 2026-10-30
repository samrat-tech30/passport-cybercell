# Backend image. Build from the backend/ folder:  docker build -t passport-backend .
# Works on Render / Railway / Fly / any container host. Set "root directory" = backend.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=prod \
    DATA_DIR=/data

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run as a non-root user; the only writable place is the data folder (SQLite).
RUN useradd --create-home --uid 10001 passport && mkdir -p /data && chown passport /data
USER passport

EXPOSE 8000
# --proxy-headers so rate limiting sees the real client IP behind the host's load balancer.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
