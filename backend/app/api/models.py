from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.models import PredictionModel, User
from app.schemas.model import PredictionModelCreate, PredictionModel as PredictionModelSchema
from app.auth.jwt import get_current_active_user

router = APIRouter()

# Получение списка всех моделей
@router.get("/models", response_model=List[PredictionModelSchema])
def get_models(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    models = db.query(PredictionModel).all()
    return models

# Получение модели по ID
@router.get("/models/{model_id}", response_model=PredictionModelSchema)
def get_model(model_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    model = db.query(PredictionModel).filter(PredictionModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    return model

# Добавление модели (только для администраторов, ограничения не реализованы в MVP)
@router.post("/models", response_model=PredictionModelSchema, status_code=status.HTTP_201_CREATED)
def create_model(model: PredictionModelCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # В реальном приложении здесь была бы проверка на администратора
    new_model = PredictionModel(**model.dict())
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return new_model
