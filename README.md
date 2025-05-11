# ML-сервис предсказаний цен криптовалют

Сервис позволяет пользователям регистрироваться, пополнять баланс и запускать асинхронные предсказания цен криптовалют с использованием различных моделей. Предсказания тарифицируются, сохраняются в истории и доступны для повторного анализа.

## Архитектура проекта

- Backend: FastAPI
- База данных: PostgreSQL + SQLAlchemy
- Очереди: Redis (RQ)
- Фронтенд: Streamlit
- Аутентификация: JWT

## Структура проекта

```
ml-service/
├── backend/            # Бэкенд на FastAPI
│   ├── src/
│   │   └── app/       # Исходный код приложения
│   │       ├── api/   # API-маршруты
│   │       ├── auth/  # Аутентификация
│   │       ├── core/  # Конфигурация
│   │       ├── database/ # Работа с БД
│   │       ├── models/   # Модели SQLAlchemy
│   │       ├── queue/    # Асинхронные задачи
│   │       └── schemas/  # Pydantic-схемы
│   ├── requirements.txt  # Зависимости бэкенда
│   └── pyproject.toml    # Конфигурация проекта
└── frontend/           # Фронтенд на Streamlit
    ├── app.py          # Главный файл приложения
    ├── pages/          # Страницы приложения
    ├── utils.py        # Утилиты для работы с API
    └── requirements.txt # Зависимости фронтенда
```

## Запуск проекта

### Предварительные требования

- Python 3.12+
- PostgreSQL
- Redis

### Настройка базы данных PostgreSQL

1. Установите и запустите PostgreSQL
2. Создайте базу данных для проекта:

```sql
CREATE DATABASE ml_service;  
CREATE USER postgres WITH PASSWORD 'postgres';  
GRANT ALL PRIVILEGES ON DATABASE ml_service TO postgres;
```

### Настройка и запуск бэкенда

1. Создайте виртуальное окружение и активируйте его:

```bash
python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
```

2. Установите зависимости:

```bash
cd backend
pip install -r requirements.txt
```

3. Запустите сервер API:

```bash
cd backend
python -m src.app.main
```

API будет доступно по адресу: http://localhost:8000

### Запуск воркера Redis Queue

1. Откройте новый терминал и активируйте виртуальное окружение
2. Запустите воркер RQ:

```bash
cd backend
python -c "from redis import Redis; from rq import Worker, Queue, Connection; with Connection(Redis.from_url('redis://localhost:6379/0')): worker = Worker(['predict_queue']); worker.work()"
```

### Настройка и запуск фронтенда

1. Создайте новое виртуальное окружение или используйте существующее
2. Установите зависимости:

```bash
cd frontend
pip install -r requirements.txt
```

3. Запустите Streamlit приложение:

```bash
cd frontend
streamlit run app.py
```

Фронтенд будет доступен по адресу: http://localhost:8501

## Использование API

Документация API доступна по адресу: http://localhost:8000/docs

Основные эндпоинты:

- POST `/api/v1/users` - Регистрация нового пользователя
- POST `/api/v1/auth/login` - Вход в систему
- GET `/api/v1/users/me` - Информация о текущем пользователе
- GET `/api/v1/models` - Получение списка моделей
- POST `/api/v1/predict` - Запуск предсказания
- GET `/api/v1/predict/history` - История предсказаний
- GET `/api/v1/predict/{id}` - Получение результатов предсказания
- GET `/api/v1/billing/balance` - Текущий баланс
- POST `/api/v1/billing/top-up` - Пополнение баланса
- GET `/api/v1/billing/transactions` - История транзакций

## Дополнительная информация

- Создание миграций базы данных происходит автоматически при первом запуске
- Для тестирования рекомендуется создать несколько тестовых моделей через API
- Предсказания выполняются асинхронно через Redis Queue

## Авторизация

Сервис использует JWT токены для авторизации. Токен необходимо передавать в заголовке `Authorization` в формате `Bearer TOKEN`.

Пример:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
