import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Общие настройки
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ML-сервис предсказаний цен криптовалют"
    
    # База данных
    DATABASE_URL: str = "postgresql://postgres:postgres@127.0.0.1:5433/ml_service"
    
    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    
    # Настройки JWT
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Настройки моделей
    DEFAULT_MODEL_PRICE: float = 10.0
    
    # Настройки ML-сервиса
    ML_SERVICE_URL: str = "http://localhost:8000"
    ML_SERVICE_TIMEOUT: int = 30
    # Маппинг между внутренними ID моделей и типами моделей ML-сервиса
    ML_MODEL_MAPPING: dict = {
        1: "random_forest",
        2: "xgboost",
        3: "lightgbm",
        4: "prophet"
    }

settings = Settings()