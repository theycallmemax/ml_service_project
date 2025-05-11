from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# Типы транзакций
class TransactionType(str, Enum):
    CREDIT = "credit"  # пополнение
    DEBIT = "debit"    # списание

# Базовая схема транзакции
class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)  # Сумма всегда положительная
    transaction_type: TransactionType
    description: Optional[str] = None

# Схема для создания транзакции
class TransactionCreate(TransactionBase):
    pass

# Схема для пополнения баланса
class TopUpBalance(BaseModel):
    amount: float = Field(..., gt=0)  # Сумма должна быть положительной

# Схема для отображения транзакции
class Transaction(TransactionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Заменено с orm_mode