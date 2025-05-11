from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Базовая схема пользователя
class UserBase(BaseModel):
    email: EmailStr

# Схема для создания пользователя
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# Схема для авторизации
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Схема для отображения пользователя
class User(UserBase):
    id: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True  # Заменено с orm_mode

# Схема для токена доступа
class Token(BaseModel):
    access_token: str
    token_type: str

# Схема для данных токена
class TokenData(BaseModel):
    user_id: Optional[int] = None

# Схема для баланса пользователя
class UserBalance(BaseModel):
    user_id: int
    email: EmailStr
    balance: float

    class Config:
        from_attributes = True  # Заменено с orm_mode
