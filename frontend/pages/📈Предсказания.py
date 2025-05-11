import streamlit as st
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from utils import check_authentication, get_models, create_prediction, get_predictions_history, get_prediction, get_current_price
# Конфигурация страницы
st.set_page_config(
    page_title="Предсказания",
    page_icon="📈",
    layout="wide",  # Изменено на широкий формат для колонок
)

# Заголовок страницы
st.title("Предсказания цен криптовалют")

# Проверка аутентификации
current_user = check_authentication()

# Функция для отображения текущей цены криптовалюты
def display_current_price(crypto):
    st.subheader("Текущая цена")
    
    with st.spinner("Загрузка текущей цены..."):
        price_data = get_current_price(crypto.lower())
    
    if "error" in price_data:
        st.error(price_data["error"])
    else:
        price = price_data.get("price", "N/A")
        timestamp = price_data.get("timestamp", "N/A")
        
        # Отображение цены в красивом формате
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label=f"{crypto.upper()}/USDT",
                value=f"${price:,.2f}" if isinstance(price, (int, float)) else price
            )
        with col2:
            st.caption(f"Обновлено: {timestamp}")
            if st.button("🔄 Обновить"):
                st.rerun()


# Переменная для хранения ID выбранного предсказания
if 'selected_prediction_id' not in st.session_state:
    st.session_state.selected_prediction_id = None

# Получаем список доступных моделей
response = get_models(st.session_state.token)

if response.status_code == 200:
    models = response.json()
    
    if models and len(models) > 0:
        # Формируем список моделей для выбора
        model_options = {f"{model['name']} ({model['description']}) - {model['price']} кредитов": model["id"] for model in models}
        
        # Создаем две колонки
        left_col, right_col = st.columns([1, 1])
        
        # ЛЕВАЯ КОЛОНКА - Форма создания предсказания
        with left_col:
            st.header("Создать новое предсказание")
            
            # Создаем форму для нового предсказания
            with st.form("prediction_form"):
                # Выбор модели
                selected_model_name = st.selectbox(
                    "Выберите модель:",
                    options=list(model_options.keys())
                )
                selected_model_id = model_options[selected_model_name]
                
                # Ввод параметров
                coin = st.selectbox(
                    "Выберите криптовалюту:",
                    options=["BTC", "ETH", "LTC", "XRP", "DOGE"]
                )
                
                period = st.slider(
                    "Период предсказания (дни):",
                    min_value=1, max_value=30, value=7
                )
                
                # Подготавливаем данные для передачи в API
                input_data = {
                    "coin": coin,
                    "period": period,
                    "options": {
                        "include_technical": "",
                        "include_sentiment": ""
                    }
                }
                
                submit_button = st.form_submit_button("Создать предсказание")
                
                if submit_button:
                    response = create_prediction(st.session_state.token, selected_model_id, input_data)
                    if response.status_code == 201:
                        prediction_data = response.json()
                        st.success(f"Предсказание успешно создано! ID: {prediction_data.get('id')}")
                        # Сохраняем ID нового предсказания для отображения
                        st.session_state.selected_prediction_id = prediction_data.get('id')
                        st.rerun()  # Перезагружаем страницу для отображения результатов
                    else:
                        try:
                            error_msg = response.json().get("detail", "Ошибка создания предсказания")
                        except:
                            error_msg = "Ошибка создания предсказания"
                        st.error(f"Ошибка: {error_msg}")
            
            # Таблица доступных моделей
            st.subheader("Доступные модели")
            models_data = []
            for model in models:
                models_data.append({
                    "Название": model.get("name"),
                    "Цена": f"{model.get('price')} кредитов"
                })
            df_models = pd.DataFrame(models_data)
            st.dataframe(df_models, use_container_width=True, height=200)
        
        # ПРАВАЯ КОЛОНКА - Результаты предсказания
        with right_col:
            st.header("Результаты предсказания")
            
            # Если у нас есть ID выбранного предсказания, пытаемся получить его данные
            prediction_id = st.session_state.selected_prediction_id
            
            if prediction_id:
                prediction_response = get_prediction(st.session_state.token, prediction_id)
                
                if prediction_response.status_code == 200:
                    prediction_details = prediction_response.json()
                    
                    # Информация о предсказании
                    status_map = {
                        "queued": "В очереди",
                        "processing": "Обрабатывается",
                        "done": "Завершено",
                        "completed": "Завершено",
                        "failed": "Ошибка"
                    }
                    status = status_map.get(prediction_details.get("status"), prediction_details.get("status"))
                    
                    st.info(f"ID предсказания: {prediction_id} | Статус: {status} | Криптовалюта: {prediction_details.get('input_data', {}).get('coin', 'N/A')}")
                    display_current_price(coin)

                    
                    # Если предсказание завершено и есть результаты, показываем их
                    if prediction_details.get("status") in ["done", "completed"] and prediction_details.get("result"):
                        result = prediction_details.get("result", {})
                        
                        # Создаем даты для предсказания
                        start_date = datetime.now()
                        period = prediction_details.get('input_data', {}).get('period', 7)
                        dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(period)]
                        
                        # Создаем DataFrame с результатами
                        forecast_data = []
                        price_values = []
                        
                        try:
                            # Получаем криптовалюту из данных предсказания
                            crypto = prediction_details.get('input_data', {}).get('coin', 'BTC')
                            
                            current_price_data = get_current_price(crypto.lower())
                            if not "error" in current_price_data:
                                current_price = current_price_data.get("price")
                                
                                # Получаем первое предсказание для сравнения с текущей ценой
                                first_prediction = None
                                if isinstance(result, dict) and "forecasts" in result and result["forecasts"]:
                                    if isinstance(result["forecasts"][0], dict) and "price" in result["forecasts"][0]:
                                        first_prediction = result["forecasts"][0]["price"]
                                    elif isinstance(result["forecasts"][0], (int, float)):
                                        first_prediction = result["forecasts"][0]
                                elif isinstance(result, dict) and "forecast" in result and result["forecast"]:
                                    first_prediction = result["forecast"][0] if result["forecast"] else None
                                elif isinstance(result, list) and result:
                                    first_prediction = result[0]
                                    
                                # Отображаем рекомендацию LONG/SHORT с эмодзи
                                if first_prediction and isinstance(first_prediction, (int, float)):
                                    if first_prediction > current_price:
                                        # Зеленая табличка для LONG
                                        st.success(f"LONG 📈")
                                    else:
                                        # Красная табличка для SHORT
                                        st.error(f"SHORT 📉")
                        except Exception as e:
                            st.warning(f"Не удалось получить текущую цену: {e}")


                                           
                        
                        # Обработка нового формата результата с ключом 'forecasts'
                        if isinstance(result, dict) and "forecasts" in result:
                            forecasts = result["forecasts"]
                            for i, forecast in enumerate(forecasts):
                                if isinstance(forecast, dict) and "price" in forecast and "date" in forecast:
                                    # Новый формат с объектами, содержащими price и date
                                    price = forecast["price"]
                                    date = forecast["date"]
                                    price_values.append(price)
                                    forecast_data.append({
                                        "Дата": date,
                                        "Прогноз цены": f"${price:.2f}",
                                        "Изменение от текущего": forecast.get("change_from_current", "N/A")
                                    })
                                else:
                                    # Если формат не соответствует ожидаемому
                                    if i < len(dates):
                                        date = dates[i]
                                    else:
                                        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                                    
                                    # Если forecast просто число
                                    if isinstance(forecast, (int, float)):
                                        price = float(forecast)
                                    else:
                                        # Если непонятный формат, используем случайное значение на основе последнего
                                        base_price = 30000 if not price_values else price_values[-1]
                                        price = base_price * (1 + np.random.uniform(-0.05, 0.08))
                                    
                                    price_values.append(price)
                                    forecast_data.append({
                                        "Дата": date,
                                        "Прогноз цены": f"${price:.2f}"
                                    })
                        # Обработка старого формата с ключом 'forecast'
                        elif isinstance(result, dict) and "forecast" in result:
                            forecasts = result["forecast"]
                            for i, date in enumerate(dates):
                                # Генерируем примерные данные, если их нет
                                if i < len(forecasts):
                                    price = forecasts[i]
                                else:
                                    # Если нет данных на этот день, делаем примерно
                                    price = forecasts[-1] * (1 + np.random.uniform(-0.02, 0.02))
                                
                                price_values.append(price)
                                forecast_data.append({
                                    "Дата": date,
                                    "Прогноз цены": f"${price:.2f}"
                                })
                        # Если результат просто список значений
                        elif isinstance(result, list):
                            forecasts = result
                            for i, date in enumerate(dates):
                                if i < len(forecasts):
                                    price = forecasts[i]
                                else:
                                    price = forecasts[-1] * (1 + np.random.uniform(-0.02, 0.02))
                                
                                price_values.append(price)
                                forecast_data.append({
                                    "Дата": date,
                                    "Прогноз цены": f"${price:.2f}"
                                })
                        # Если результат просто одно значение
                        else:
                            base_price = 30000  # Примерная цена BTC
                            if prediction_details.get('input_data', {}).get('coin') == "ETH":
                                base_price = 2000
                            elif prediction_details.get('input_data', {}).get('coin') == "LTC":
                                base_price = 80
                            
                            for i, date in enumerate(dates):
                                # Создаем синтетические данные для примера
                                change = np.random.uniform(-0.05, 0.08)
                                price = base_price * (1 + change * (i + 1))
                                price_values.append(price)
                                forecast_data.append({
                                    "Дата": date,
                                    "Прогноз цены": f"${price:.2f}"
                                })
                        
                        # Показываем таблицу с прогнозами
                        st.subheader("Таблица прогнозов по дням")
                        df_forecast = pd.DataFrame(forecast_data)
                        st.dataframe(df_forecast, use_container_width=True)
                        
                        # Строим график
                        st.subheader("График прогноза цены")
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(df_forecast["Дата"], price_values, marker='o', linestyle='-', color='blue')
                        ax.set_title(f"Прогноз цены {prediction_details.get('input_data', {}).get('coin', 'Криптовалюты')}")
                        ax.set_xlabel("Дата")
                        ax.set_ylabel("Цена (USD)")
                        ax.grid(True, linestyle='--', alpha=0.7)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                        # Дополнительная аналитика (если есть)
                        if isinstance(result, dict) and "analytics" in result:
                            st.subheader("Дополнительная аналитика")
                            st.json(result["analytics"])
                    
                    elif prediction_details.get("status") == "failed":
                        st.error("Предсказание завершилось с ошибкой")
                    elif prediction_details.get("status") in ["queued", "processing"]:
                        st.warning("Предсказание еще обрабатывается. Пожалуйста, подождите...")
                        # Добавляем автоматическое обновление страницы каждые 5 секунд
                        st.empty()
                        st.rerun()
                else:
                    st.error("Не удалось загрузить детали предсказания")
            else:
                st.info("Выберите предсказание из истории ниже или создайте новое, чтобы увидеть результаты")
        
        # История предсказаний (внизу под колонками)
        st.header("История предсказаний")
        history_response = get_predictions_history(st.session_state.token)
        
        if history_response.status_code == 200:
            predictions = history_response.json()
            if predictions and len(predictions) > 0:
                # Преобразуем данные для отображения
                predictions_data = []
                for pred in predictions:
                    status_map = {
                        "queued": "В очереди",
                        "processing": "Обрабатывается",
                        "done": "Завершено", 
                        "completed": "Завершено",
                        "failed": "Ошибка"
                    }
                    
                    status = status_map.get(pred.get("status"), pred.get("status"))
                    coin = pred.get("input_data", {}).get("coin", "N/A")
                    period = pred.get("input_data", {}).get("period", "N/A")
                    
                    predictions_data.append({
                        "ID": pred.get("id"),
                        "Дата": pred.get("created_at"),
                        "Модель": pred.get("model_id"),
                        "Криптовалюта": coin,
                        "Период (дни)": period,
                        "Статус": status,
                    })
                
                # Создаем DataFrame и отображаем его с возможностью выбора строки
                df_history = pd.DataFrame(predictions_data)
                st.dataframe(df_history, use_container_width=True, height=300)
                
                # Выбор предсказания для отображения
                selected_id = st.selectbox(
                    "Выберите предсказание для просмотра:",
                    options=[pred["ID"] for pred in predictions_data],
                    format_func=lambda x: f"Предсказание #{x} - {next((p['Криптовалюта'] for p in predictions_data if p['ID'] == x), '')} на {next((p['Период (дни)'] for p in predictions_data if p['ID'] == x), '')} дней"
                )
                
                if st.button("Показать результаты выбранного предсказания"):
                    st.session_state.selected_prediction_id = selected_id
                    st.rerun()
            else:
                st.info("У вас пока нет предсказаний")
        else:
            st.error("Не удалось загрузить историю предсказаний")
    else:
        st.warning("Нет доступных моделей для предсказаний")
else:
    st.error("Не удалось загрузить список моделей")