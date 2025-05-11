import time
import random
import json
from datetime import datetime
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Prediction, PredictionStatus
from app.database.database import SessionLocal
from app.utils.ml_client import ml_service, MLServiceError

# Создаем подключение к Redis и очередь
def get_redis_connection():
    return Redis.from_url(settings.REDIS_URL)

def get_queue():
    # Используем Redis напрямую без Connection
    redis_conn = get_redis_connection()
    queue = Queue("predict_queue", connection=redis_conn)
    return queue

# Функция-заглушка для предсказания (оставляем для совместимости)
def mock_prediction(input_data):
    """Заглушка для предсказаний, возвращает случайные данные"""
    # Имитация длительной обработки
    time.sleep(5)
    
    # Генерируем случайные данные для предсказания
    symbol = input_data.get("symbol", "BTC/USD")
    current_price = input_data.get("current_price", 50000)
    periods = input_data.get("period", 7)
    
    # Генерируем случайные предсказания
    forecasts = []
    for i in range(periods):
        # Добавляем случайное отклонение от -5% до +10%
        change = random.uniform(-0.05, 0.10)
        price = current_price * (1 + change)
        forecasts.append({
            "day": i + 1,
            "price": round(price, 2),
            "change": f"{change * 100:.2f}%"
        })
        current_price = price
    
    return {
        "symbol": symbol,
        "forecast_date": datetime.utcnow().isoformat(),
        "forecasts": forecasts
    }

# Функция обработки задачи предсказания
def process_prediction(prediction_id: int):
    """Обработка задачи предсказания"""
    # Создаем новую сессию БД
    db = SessionLocal()
    try:
        # Получаем задачу из БД
        prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
        if not prediction:
            return {"error": f"Предсказание с ID {prediction_id} не найдено"}
        
        # Обновляем статус на "processing"
        prediction.status = PredictionStatus.PROCESSING.value
        db.commit()
        
        try:
            # Получаем тип модели из ML_MODEL_MAPPING
            model_id = prediction.model_id
            model_type = settings.ML_MODEL_MAPPING.get(model_id, "random_forest")
            
            # Выполняем предсказание через ML-сервис
            try:
                # Отправляем запрос к ML-сервису
                ml_result = ml_service.predict(model_type, prediction.input_data)
                
                # Преобразуем результат в формат, ожидаемый приложением
                # Передаем также входные данные для получения информации о периоде
                result = ml_service.convert_prediction_to_app_format(
                    ml_result, 
                    prediction.input_data
                )
                
                # Обновляем запись в БД
                prediction.status = PredictionStatus.DONE.value
                prediction.result = result
                prediction.completed_at = datetime.utcnow()
                db.commit()
                
                return result
            except MLServiceError as e:
                # В случае ошибки в ML-сервисе используем заглушку
                print(f"Ошибка ML-сервиса: {e}, используем заглушку")
                result = mock_prediction(prediction.input_data)
                
                prediction.status = PredictionStatus.DONE.value
                prediction.result = result
                prediction.completed_at = datetime.utcnow()
                db.commit()
                
                return result
        except Exception as e:
            # В случае ошибки обновляем статус
            prediction.status = PredictionStatus.ERROR.value
            prediction.result = {"error": str(e)}
            prediction.completed_at = datetime.utcnow()
            db.commit()
            return {"error": str(e)}
    finally:
        db.close()

# Функция для добавления задачи в очередь
def queue_prediction(prediction_id: int):
    """Добавление задачи предсказания в очередь"""
    queue = get_queue()
    job = queue.enqueue(process_prediction, prediction_id)
    return job.id
