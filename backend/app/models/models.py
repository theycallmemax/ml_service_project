import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Enum, func, text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.database.database import Base

# Статусы предсказаний
class PredictionStatus(str, PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"

# Типы транзакций
class TransactionType(str, PyEnum):
    CREDIT = "credit"  # пополнение
    DEBIT = "debit"    # списание

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Связи с другими таблицами
    predictions = relationship("Prediction", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

# Модель предсказания (справочник моделей)
class PredictionModel(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)  # Цена за использование модели
    
    # Связи с другими таблицами
    predictions = relationship("Prediction", back_populates="model")

# Модель предсказания (задачи)
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    status = Column(String, default=PredictionStatus.QUEUED.value, nullable=False)
    input_data = Column(JSON, nullable=False)  # Входные данные для предсказания
    result = Column(JSON, nullable=True)  # Результат предсказания
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Связи с другими таблицами
    user = relationship("User", back_populates="predictions")
    model = relationship("PredictionModel", back_populates="predictions")

# Модель транзакций
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Сумма транзакции (положительная для пополнения, отрицательная для списания)
    transaction_type = Column(String, nullable=False)  # credit (пополнение) или debit (списание)
    description = Column(String, nullable=True)  # Описание транзакции
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Связи с другими таблицами
    user = relationship("User", back_populates="transactions")

# Представление для баланса пользователя
def get_user_balance(user_id):
    """SQL-запрос для расчета баланса пользователя"""
    stmt = text("""
    SELECT u.id, u.email, COALESCE(SUM(CASE WHEN t.transaction_type = 'credit' THEN t.amount ELSE -t.amount END), 0) as balance
    FROM users u
    LEFT JOIN transactions t ON u.id = t.user_id
    WHERE u.id = :user_id
    GROUP BY u.id, u.email
    """)
    return stmt.bindparams(user_id=user_id)