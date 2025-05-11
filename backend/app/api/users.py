from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from app.database.database import get_db
from app.models.models import User, get_user_balance, Transaction, TransactionType
from app.schemas.user import UserCreate, User as UserSchema, Token, UserBalance
from app.schemas.transaction import TransactionCreate, Transaction as TransactionSchema, TopUpBalance
from app.auth.jwt import authenticate_user, create_access_token, get_password_hash, get_current_active_user
from app.core.config import settings

router = APIRouter()

# Регистрация пользователя
@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Проверяем, что пользователь с таким email уже не существует
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )
    
    # Создаем нового пользователя
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# Авторизация и получение JWT токена
@router.post("/auth/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем JWT токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Получение текущего пользователя
@router.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Получение баланса пользователя
@router.get("/billing/balance", response_model=UserBalance)
async def get_balance(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Выполняем SQL-запрос для получения баланса
    result = db.execute(get_user_balance(current_user.id), {"user_id": current_user.id}).first()
    if not result:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return {"user_id": result[0], "email": result[1], "balance": result[2]}

# Пополнение баланса
@router.post("/billing/top-up", response_model=TransactionSchema)
async def top_up_balance(
    top_up: TopUpBalance,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Создаем новую транзакцию пополнения
    transaction = Transaction(
        user_id=current_user.id,
        amount=top_up.amount,
        transaction_type=TransactionType.CREDIT.value,
        description="Пополнение баланса"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction

# Получение истории транзакций
@router.get("/billing/transactions", response_model=List[TransactionSchema])
async def get_transactions(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.created_at.desc()).all()
    return transactions
