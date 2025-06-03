FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем alembic.ini и папку migrations
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations/

# Копируем requirements.txt
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Копируем приложение
COPY app /app/app

# Указываем порт
EXPOSE 8000

# Команда для запуска приложения (для production используем Gunicorn + Uvicorn)
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "app.main:app", "--bind", "0.0.0.0:8000"]
