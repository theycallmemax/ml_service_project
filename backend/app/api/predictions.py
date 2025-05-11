from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.database.database import get_db
from app.models.models import User, Prediction, PredictionModel, Transaction, TransactionType, PredictionStatus, get_user_balance
from app.schemas.prediction import PredictionCreate, Prediction as PredictionSchema
from app.auth.jwt import get_current_active_user
from app.queue.tasks import queue_prediction

router = APIRouter()

# Создание нового предсказания
@router.post("/predict", response_model=PredictionSchema, status_code=status.HTTP_201_CREATED)
def create_prediction(
    prediction: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Проверяем существование модели
    model = db.query(PredictionModel).filter(PredictionModel.id == prediction.model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    # Проверяем баланс пользователя
    balance_result = db.execute(get_user_balance(current_user.id)).first()
    if not balance_result or balance_result[2] < model.price:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Недостаточно средств на балансе. Требуется: {model.price}, Сейчас: {balance_result[2] if balance_result else 0}"
        )
    
    # Создаем запись о предсказании
    db_prediction = Prediction(
        user_id=current_user.id,
        model_id=prediction.model_id,
        status=PredictionStatus.QUEUED.value,
        input_data=prediction.input_data
    )
    
    # Создаем транзакцию списания средств
    transaction = Transaction(
        user_id=current_user.id,
        amount=model.price,
        transaction_type=TransactionType.DEBIT.value,
        description=f"Предсказание с использованием модели {model.name}"
    )
    
    # Сохраняем изменения в БД
    db.add(db_prediction)
    db.add(transaction)
    db.commit()
    db.refresh(db_prediction)
    
    # Добавляем задачу в очередь Redis
    queue_prediction(db_prediction.id)
    
    return db_prediction

# Получение истории предсказаний
@router.get("/predict/history", response_model=List[PredictionSchema])
def get_predictions_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    predictions = db.query(Prediction)\
        .filter(Prediction.user_id == current_user.id)\
        .order_by(Prediction.created_at.desc())\
        .all()
    return predictions

# Получение результата предсказания
@router.get("/predict/{prediction_id}", response_model=PredictionSchema)
def get_prediction(prediction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id
    ).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Предсказание не найдено")
    
    return prediction
