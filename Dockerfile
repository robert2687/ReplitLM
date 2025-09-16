# Minimal production container for AI App Builder
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source
COPY app /app/app
COPY replit-code-v1-3b /app/replit-code-v1-3b

# Expose and run
EXPOSE 8000
ENV APP_MAX_CONCURRENCY=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]