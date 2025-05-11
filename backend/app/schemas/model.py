from pydantic import BaseModel, Field
from typing import Optional

# Базовая схема модели предсказания
class PredictionModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)  # Цена должна быть положительной

# Схема для создания модели
class PredictionModelCreate(PredictionModelBase):
    pass

# Схема для обновления модели
class PredictionModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)

# Схема для отображения модели
class PredictionModel(PredictionModelBase):
    id: int

    class Config:
        from_attributes = True  # Заменено с orm_mode
