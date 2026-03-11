# ---- Build stage ----
FROM python:3.12-slim AS base

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/      app/
COPY run.py    .

# Data directory for SQLite persistence
RUN mkdir -p /data

ENV DATABASE_PATH=/data/bookmarks.db
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "run:app"]
