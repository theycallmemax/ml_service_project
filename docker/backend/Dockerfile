FROM python:3.10-slim

WORKDIR /app

# Установка Poetry
RUN pip install poetry==1.7.1

# Копируем только файлы Poetry
COPY pyproject.toml ./

# Настраиваем Poetry для установки в тот же контейнер
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi \
    && poetry add rq redis psycopg2-binary bcrypt passlib[bcrypt] python-jose[cryptography] python-multipart requests

# Копирование файлов проекта
COPY . .

# Запуск по умолчанию - бэкенд сервис
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
