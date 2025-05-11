from ..database.database import SessionLocal
from .models import PredictionModel
from ..core.config import settings

# Модели ML-сервиса и их цены
ML_MODELS = {
    "random_forest": {
        "name": "Random Forest",
        "description": "Модель на основе случайного леса для прогнозирования цены Bitcoin. Высокая точность, средняя скорость.",
        "price": 10.0
    },
    "xgboost": {
        "name": "XGBoost",
        "description": "Модель на основе градиентного бустинга для прогнозирования цены Bitcoin. Высокая точность, быстрое обучение.",
        "price": 15.0
    },
    "lightgbm": {
        "name": "LightGBM",
        "description": "Легковесная модель градиентного бустинга для прогнозирования цены Bitcoin. Быстрая и эффективная.",
        "price": 12.0
    },
    "prophet": {
        "name": "Prophet",
        "description": "Модель временных рядов от Facebook для прогнозирования цены Bitcoin. Хорошо работает с сезонными данными.",
        "price": 20.0
    },
}

def update_models():
    """Обновление моделей в базе данных"""
    db = SessionLocal()
    try:
        # Ищем существующие модели в БД
        existing_models = {model.id: model for model in db.query(PredictionModel).all()}
        
        # Для каждой модели в маппинге
        for model_id, model_type in settings.ML_MODEL_MAPPING.items():
            if model_type in ML_MODELS:
                model_info = ML_MODELS[model_type]
                
                if model_id in existing_models:
                    # Обновляем существующую модель
                    model = existing_models[model_id]
                    model.name = model_info["name"]
                    model.description = model_info["description"]
                    model.price = model_info["price"]
                    print(f"Обновлена модель: {model.name} (ID: {model_id})")
                else:
                    # Создаем новую модель
                    new_model = PredictionModel(
                        id=model_id,
                        name=model_info["name"],
                        description=model_info["description"],
                        price=model_info["price"]
                    )
                    db.add(new_model)
                    print(f"Добавлена новая модель: {new_model.name} (ID: {model_id})")
        
        # Сохраняем изменения
        db.commit()
        print("Модели успешно обновлены!")
    except Exception as e:
        db.rollback()
        print(f"Ошибка при обновлении моделей: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_models()
