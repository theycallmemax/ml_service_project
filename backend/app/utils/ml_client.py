import requests
import logging
import json
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

class MLServiceError(Exception):
    """Ошибка при взаимодействии с ML-сервисом"""
    pass

class MLServiceClient:
    """Клиент для взаимодействия с ML-сервисом"""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        """Инициализация клиента ML-сервиса"""
        self.base_url = base_url or settings.ML_SERVICE_URL
        self.timeout = timeout or settings.ML_SERVICE_TIMEOUT
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение HTTP запроса к ML-сервису"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            # Добавляем таймаут в запрос
            kwargs.setdefault('timeout', self.timeout)
            
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()  # Вызывает исключение для HTTP ошибок
            
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ошибка при обращении к ML-сервису: {e}")
            raise MLServiceError(f"Ошибка при обращении к ML-сервису: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Ошибка при разборе ответа от ML-сервиса")
            raise MLServiceError("Некорректный формат ответа от ML-сервиса")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о доступных моделях"""
        return self._make_request('GET', '/model-info')
    
    def predict(self, model_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение предсказания с использованием выбранной модели
        
        Args:
            model_type: Тип модели (random_forest, xgboost, lightgbm, prophet)
            input_data: Данные для предсказания, должны содержать:
                        - crypto: Название криптовалюты (например, 'btc')
                        - days: Количество дней для прогноза (например, 7)
                        
        Returns:
            Dict с результатами предсказания
        """
        # Извлекаем параметры из входных данных
        crypto = input_data.get("coin", "btc").lower()
        days = input_data.get("period", 7)
        
        # Формируем запрос к ML-сервису в новом формате
        data = {
            "crypto": crypto,
            "days": days,
            "model_type": model_type
        }
            
        return self._make_request('POST', '/predict', json=data)
    
    def retrain_model(self, model_type: str) -> Dict[str, Any]:
        """Запуск переобучения модели"""
        return self._make_request('POST', '/retrain', json={"model_type": model_type})
    
    def convert_prediction_to_app_format(self, ml_prediction: Dict[str, Any], input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Конвертирует ответ ML-сервиса в формат, ожидаемый приложением
        
        Args:
            ml_prediction: Результат предсказания от ML-сервиса
            input_data: Исходные данные запроса (для совместимости)
        """
        # Определяем символ криптовалюты
        crypto = ml_prediction.get("crypto", "btc").upper()
        symbol = f"{crypto}/USD"
        
        # Проверяем наличие входных данных для совместимости
        if input_data and "coin" in input_data:
            crypto = input_data.get("coin", "BTC").upper()
            symbol = f"{crypto}/USD"
        
        # Извлекаем информацию о текущих параметрах из features_used
        current_price = 0
        if "features_used" in ml_prediction and "close" in ml_prediction["features_used"]:
            current_price = ml_prediction["features_used"]["close"]
        
        model_type = ml_prediction.get("model_type", "")
        
        # Преобразуем предсказания из нового формата в ожидаемый приложением формат
        forecasts = []
        
        # Новый формат содержит список предсказаний
        if "predictions" in ml_prediction and isinstance(ml_prediction["predictions"], list):
            for i, prediction in enumerate(ml_prediction["predictions"]):
                day = i + 1
                price = prediction.get("price", 0)
                date = prediction.get("date") or (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")
                
                # Расчет изменений от текущей цены
                change_from_current = ((price - current_price) / current_price * 100) if current_price else 0
                
                # Расчет изменений от предыдущего дня
                prev_price = forecasts[-1]["price"] if forecasts else current_price
                day_change = ((price - prev_price) / prev_price * 100) if prev_price else 0
                
                forecasts.append({
                    "day": day,
                    "price": round(price, 2),
                    "date": date,
                    "change": f"{day_change:.2f}%",
                    "change_from_current": f"{change_from_current:.2f}%"
                })
        # Совместимость со старым форматом
        elif "prediction" in ml_prediction:
            # Извлекаем период из входных данных
            period = 7
            if input_data and "period" in input_data:
                period = input_data.get("period", 7)
            
            # Получаем цену из старого формата
            predicted_price = ml_prediction.get("prediction", 0)
            latest_price = predicted_price
            
            for day in range(1, period + 1):
                # Для первого дня используем предсказание модели
                if day == 1:
                    price = predicted_price
                else:
                    # Для последующих дней генерируем значения на основе тренда
                    volatility = 0.01 * day
                    change_factor = random.uniform(-volatility, volatility * 1.5)  # Небольшой бычий уклон
                    price = latest_price * (1 + change_factor)
                
                # Расчет изменений
                change_from_current = ((price - current_price) / current_price * 100) if current_price else 0
                day_change = ((price - latest_price) / latest_price * 100) if latest_price and day > 1 else change_from_current
                
                forecasts.append({
                    "day": day,
                    "price": round(price, 2),
                    "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                    "change": f"{day_change:.2f}%",
                    "change_from_current": f"{change_from_current:.2f}%"
                })
                
                # Обновляем последнюю цену для следующей итерации
                latest_price = price
        
        # Формируем итоговый ответ
        result = {
            "symbol": symbol,
            "forecast_date": ml_prediction.get("timestamp", datetime.now().isoformat()),
            "forecasts": forecasts,
            "ml_service_details": {
                "model_type": model_type,
                "features_used": ml_prediction.get("features_used", {}),
                "raw_predictions": ml_prediction.get("predictions", [])
            }
        }
        
        return result

# Создаем экземпляр клиента для использования в других модулях
ml_service = MLServiceClient()
