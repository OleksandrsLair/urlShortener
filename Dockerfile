# Simple Dockerfile for the Django URL shortener
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional, keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

EXPOSE 8000

# Run migrations then start the dev server (sufficient for the assignment)
CMD ["sh", "-c", "python url_shortener/manage.py migrate && python url_shortener/manage.py runserver 0.0.0.0:8000"]
