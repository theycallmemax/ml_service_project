import requests
import json
import streamlit as st
import os

# URL нашего API - получаем из переменной окружения или используем значение по умолчанию
API_URL = os.environ.get("BACKEND_URL", "http://localhost:8001") + "/api/v1"

# Функция для выполнения запросов к API
def make_request(method, endpoint, token=None, data=None):
    url = f"{API_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        headers["Content-Type"] = "application/json"
        response = requests.post(url, headers=headers, data=json.dumps(data) if data else None)
    else:
        raise ValueError(f"Неподдерживаемый метод: {method}")
    
    return response

# Функция для аутентификации
def login(email, password):
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": email, "password": password},  # Используем формат форм-данных для совместимости с OAuth2
    )
    return response

# Функция для регистрации
def register(email, password):
    response = make_request(
        "POST",
        "/users",
        data={"email": email, "password": password}
    )
    return response

# Функция для получения информации о текущем пользователе
def get_current_user(token):
    response = make_request("GET", "/users/me", token=token)
    return response

# Функция для получения баланса
def get_balance(token):
    response = make_request("GET", "/billing/balance", token=token)
    return response

# Функция для пополнения баланса
def top_up_balance(token, amount):
    response = make_request(
        "POST",
        "/billing/top-up",
        token=token,
        data={"amount": amount}
    )
    return response

# Функция для получения списка моделей
def get_models(token):
    response = make_request("GET", "/models", token=token)
    return response

# Функция для создания предсказания
def create_prediction(token, model_id, input_data):
    response = make_request(
        "POST",
        "/predict",
        token=token,
        data={"model_id": model_id, "input_data": input_data}
    )
    return response

# Функция для получения истории предсказаний
def get_predictions_history(token):
    response = make_request("GET", "/predict/history", token=token)
    return response

# Функция для получения конкретного предсказания
def get_prediction(token, prediction_id):
    response = make_request("GET", f"/predict/{prediction_id}", token=token)
    return response

# Функция для получения истории транзакций
def get_transactions(token):
    response = make_request("GET", "/billing/transactions", token=token)
    return response

# Функция для проверки аутентификации
def check_authentication():
    if "token" not in st.session_state:
        st.warning("Вам необходимо войти в систему")
        st.stop()
    
    # Проверяем валидность токена
    response = get_current_user(st.session_state.token)
    if response.status_code != 200:
        st.warning("Сессия истекла. Пожалуйста, войдите снова")
        # Очищаем токен
        st.session_state.pop("token", None)
        st.stop()
    
    return response.json()

# u0424u0443u043du043au0446u0438u044f u0434u043bu044f u043fu043eu043bu0443u0447u0435u043du0438u044f u0442u0435u043au0443u0449u0435u0439 u0446u0435u043du044b u043au0440u0438u043fu0442u043eu0432u0430u043bu044eu0442u044b u0438u0437 ML-u0441u0435u0440u0432u0438u0441u0430
def get_current_price(crypto):
    # URL ML-u0441u0435u0440u0432u0438u0441u0430
    ML_SERVICE_URL = os.environ.get("ML_SERVICE_URL", "http://ml-service:8000")
    
    try:
        response = requests.get(f"{ML_SERVICE_URL}/current-price/{crypto}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"u041eu0448u0438u0431u043au0430 u043fu043eu043bu0443u0447u0435u043du0438u044f u0446u0435u043du044b: {response.status_code}"}
    except Exception as e:
        return {"error": f"u041eu0448u0438u0431u043au0430 u0441u0432u044fu0437u0438 u0441 ML-u0441u0435u0440u0432u0438u0441u043eu043c: {str(e)}"}
