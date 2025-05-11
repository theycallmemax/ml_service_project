import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # u041eu0431u0449u0438u0435 u043du0430u0441u0442u0440u043eu0439u043au0438
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ML-u0441u0435u0440u0432u0438u0441 u043fu0440u0435u0434u0441u043au0430u0437u0430u043du0438u0439 u0446u0435u043d u043au0440u0438u043fu0442u043eu0432u0430u043bu044eu0442"
    
    # u0411u0430u0437u0430 u0434u0430u043du043du044bu0445
    DATABASE_URL: str = "postgresql://postgres:postgres@127.0.0.1:5433/ml_service"
    
    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    
    # u041du0430u0441u0442u0440u043eu0439u043au0438 JWT
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # u041du0430u0441u0442u0440u043eu0439u043au0438 u043cu043eu0434u0435u043bu0435u0439
    DEFAULT_MODEL_PRICE: float = 10.0
    
    # u041du0430u0441u0442u0440u043eu0439u043au0438 ML-u0441u0435u0440u0432u0438u0441u0430
    ML_SERVICE_URL: str = "http://localhost:8000"
    ML_SERVICE_TIMEOUT: int = 30
    # u041cu0430u043fu043fu0438u043du0433 u043cu0435u0436u0434u0443 u0432u043du0443u0442u0440u0435u043du043du0438u043cu0438 ID u043cu043eu0434u0435u043bu0435u0439 u0438 u0442u0438u043fu0430u043cu0438 u043cu043eu0434u0435u043bu0435u0439 ML-u0441u0435u0440u0432u0438u0441u0430
    ML_MODEL_MAPPING: dict = {
        1: "random_forest",
        2: "xgboost",
        3: "lightgbm",
        4: "prophet"
    }

settings = Settings()
