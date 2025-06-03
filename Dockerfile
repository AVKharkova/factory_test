FROM python:3.9-slim

WORKDIR /app

# Копируем alembic.ini и папку migrations
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations/

# Копируем requirements.txt
COPY ./requirements.txt /app/requirements.txt

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Копируем всё приложение
COPY ./app /app/app

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
