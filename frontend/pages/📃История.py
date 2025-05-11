import streamlit as st
import pandas as pd
import json
from utils import check_authentication, get_predictions_history, get_prediction, get_transactions

# Конфигурация страницы
st.set_page_config(
    page_title="История",
    page_icon="📃",
    layout="centered",
)

# Заголовок страницы
st.title("История операций")

# Проверка аутентификации
current_user = check_authentication()

# Добавляем переключатель между историей транзакций и историей пополнений
tab1, tab2 = st.tabs(["История транзакций", "История пополнений"])

# Таб 1 - История транзакций (предсказаний)
with tab1:
    st.header("История предсказаний")

    # Получаем историю предсказаний
    response = get_predictions_history(st.session_state.token)

    if response.status_code == 200:
        predictions = response.json()
        if predictions and len(predictions) > 0:
            # Преобразуем данные для отображения
            predictions_data = []
            for pred in predictions:
                status_map = {
                    "queued": "В очереди",
                    "processing": "Обрабатывается",
                    "completed": "Завершено",
                    "failed": "Ошибка"
                }

                status = status_map.get(pred.get("status"), pred.get("status"))

                predictions_data.append({
                    "ID": pred.get("id"),
                    "Дата": pred.get("created_at"),
                    "Модель": pred.get("model_id"),
                    "Статус": status,
                })

            # Создаем DataFrame и отображаем его
            df = pd.DataFrame(predictions_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("У вас пока нет предсказаний")
    else:
        st.error("Не удалось загрузить историю предсказаний")

# Таб 2 - История пополнений
with tab2:
    st.header("История пополнений баланса")

    # Получаем реальную историю транзакций из API
    transactions_response = get_transactions(st.session_state.token)

    if transactions_response.status_code == 200:
        transactions = transactions_response.json()

        # Фильтруем только транзакции с описанием "Пополнение баланса"
        deposit_transactions = [
            t for t in transactions
            if t.get("description") == "Пополнение баланса" or
               (t.get("amount", 0) > 0 and "пополнение" in t.get("description", "").lower())
        ]

        if deposit_transactions and len(deposit_transactions) > 0:
            # Преобразуем данные для отображения
            transactions_data = []
            for transaction in deposit_transactions:
                # Форматируем сумму
                amount = transaction.get("amount", 0)

                transactions_data.append({
                    "ID": transaction.get("id"),
                    "Дата": transaction.get("created_at"),
                    "Сумма": f"{amount} кредитов",
                    "Статус": transaction.get("status", "Выполнено")
                })

            # Создаем DataFrame и отображаем его
            transactions_df = pd.DataFrame(transactions_data)
            st.dataframe(transactions_df, use_container_width=True)

        else:
            st.info("У вас пока нет операций пополнения баланса")
    else:
        st.error("Не удалось загрузить историю транзакций")
