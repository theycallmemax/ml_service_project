FROM python:3.10-slim

WORKDIR /app

# Set locale for proper UTF-8 support
RUN apt-get update && apt-get install -y locales && \
    locale-gen ru_RU.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8
ENV PYTHONIOENCODING utf-8

# Установка Poetry
RUN pip install poetry==1.7.1

# Инсталлируем зависимости для библиотек визуализации
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файлы Poetry
COPY pyproject.toml .

# Настраиваем Poetry для установки в тот же контейнер
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Копируем файлы проекта
COPY . .

# Запуск Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
