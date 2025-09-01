# Минимален dev Dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системни зависимости за psycopg2 и Pillow
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# По подразбиране стартираме dev сървър
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
