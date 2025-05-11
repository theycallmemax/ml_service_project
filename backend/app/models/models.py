import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Enum, func, text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.database.database import Base

# u0421u0442u0430u0442u0443u0441u044b u043fu0440u0435u0434u0441u043au0430u0437u0430u043du0438u0439
class PredictionStatus(str, PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"

# u0422u0438u043fu044b u0442u0440u0430u043du0437u0430u043au0446u0438u0439
class TransactionType(str, PyEnum):
    CREDIT = "credit"  # u043fu043eu043fu043eu043bu043du0435u043du0438u0435
    DEBIT = "debit"    # u0441u043fu0438u0441u0430u043du0438u0435

# u041cu043eu0434u0435u043bu044c u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # u0421u0432u044fu0437u0438 u0441 u0434u0440u0443u0433u0438u043cu0438 u0442u0430u0431u043bu0438u0446u0430u043cu0438
    predictions = relationship("Prediction", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

# u041cu043eu0434u0435u043bu044c u043fu0440u0435u0434u0441u043au0430u0437u0430u043du0438u044f (u0441u043fu0440u0430u0432u043eu0447u043du0438u043a u043cu043eu0434u0435u043bu0435u0439)
class PredictionModel(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)  # u0426u0435u043du0430 u0437u0430 u0438u0441u043fu043eu043bu044cu0437u043eu0432u0430u043du0438u0435 u043cu043eu0434u0435u043bu0438
    
    # u0421u0432u044fu0437u0438 u0441 u0434u0440u0443u0433u0438u043cu0438 u0442u0430u0431u043bu0438u0446u0430u043cu0438
    predictions = relationship("Prediction", back_populates="model")

# u041cu043eu0434u0435u043bu044c u043fu0440u0435u0434u0441u043au0430u0437u0430u043du0438u044f (u0437u0430u0434u0430u0447u0438)
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    status = Column(String, default=PredictionStatus.QUEUED.value, nullable=False)
    input_data = Column(JSON, nullable=False)  # u0412u0445u043eu0434u043du044bu0435 u0434u0430u043du043du044bu0435 u0434u043bu044f u043fu0440u0435u0434u0441u043au0430u0437u0430u043du0438u044f
    result = Column(JSON, nullable=True)  # u0420u0435u0437u0443u043bu044cu0442u0430u0442 u043fu0440u0435u0434u0441u043au0430u0437u0430u043du0438u044f
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # u0421u0432u044fu0437u0438 u0441 u0434u0440u0443u0433u0438u043cu0438 u0442u0430u0431u043bu0438u0446u0430u043cu0438
    user = relationship("User", back_populates="predictions")
    model = relationship("PredictionModel", back_populates="predictions")

# u041cu043eu0434u0435u043bu044c u0442u0440u0430u043du0437u0430u043au0446u0438u0439
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)  # u0421u0443u043cu043cu0430 u0442u0440u0430u043du0437u0430u043au0446u0438u0438 (u043fu043eu043bu043eu0436u0438u0442u0435u043bu044cu043du0430u044f u0434u043bu044f u043fu043eu043fu043eu043bu043du0435u043du0438u044f, u043eu0442u0440u0438u0446u0430u0442u0435u043bu044cu043du0430u044f u0434u043bu044f u0441u043fu0438u0441u0430u043du0438u044f)
    transaction_type = Column(String, nullable=False)  # credit (u043fu043eu043fu043eu043bu043du0435u043du0438u0435) u0438u043bu0438 debit (u0441u043fu0438u0441u0430u043du0438u0435)
    description = Column(String, nullable=True)  # u041eu043fu0438u0441u0430u043du0438u0435 u0442u0440u0430u043du0437u0430u043au0446u0438u0438
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # u0421u0432u044fu0437u0438 u0441 u0434u0440u0443u0433u0438u043cu0438 u0442u0430u0431u043bu0438u0446u0430u043cu0438
    user = relationship("User", back_populates="transactions")

# u041fu0440u0435u0434u0441u0442u0430u0432u043bu0435u043du0438u0435 u0434u043bu044f u0431u0430u043bu0430u043du0441u0430 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f
def get_user_balance(user_id):
    """SQL-u0437u0430u043fu0440u043eu0441 u0434u043bu044f u0440u0430u0441u0447u0435u0442u0430 u0431u0430u043bu0430u043du0441u0430 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f"""
    stmt = text("""
    SELECT u.id, u.email, COALESCE(SUM(CASE WHEN t.transaction_type = 'credit' THEN t.amount ELSE -t.amount END), 0) as balance
    FROM users u
    LEFT JOIN transactions t ON u.id = t.user_id
    WHERE u.id = :user_id
    GROUP BY u.id, u.email
    """)
    return stmt.bindparams(user_id=user_id)
