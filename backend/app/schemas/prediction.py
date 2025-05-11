from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Статусы предсказаний
class PredictionStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"

# Базовая схема предсказания
class PredictionBase(BaseModel):
    model_id: int
    input_data: Dict[str, Any]  # Входные данные в формате JSON

# Схема для создания предсказания
class PredictionCreate(PredictionBase):
    pass

# Схема для отображения предсказания
class Prediction(PredictionBase):
    id: int
    user_id: int
    status: PredictionStatus
    result: Optional[Dict[str, Any]] = None  # Результат в формате JSON
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Заменил устаревший orm_mode на новый from_attributes
