import streamlit as st
import pandas as pd
from utils import check_authentication, get_balance, top_up_balance, get_transactions

# Конфигурация страницы
st.set_page_config(
    page_title="Баланс",
    page_icon="💰",
    layout="centered",
)

# Заголовок страницы
st.title("Управление балансом")

# Проверка аутентификации
current_user = check_authentication()

# Получаем текущий баланс
response = get_balance(st.session_state.token)

if response.status_code == 200:
    data = response.json()
    balance = data.get("balance", 0)
    st.metric("Текущий баланс", f"{balance} кредитов")
    
    # Форма пополнения баланса
    with st.form("top_up_form"):
        st.subheader("Пополнить баланс")
        amount = st.number_input("Сумма пополнения", min_value=1, value=100)
        submit_button = st.form_submit_button("Пополнить")
        
        if submit_button:
            response = top_up_balance(st.session_state.token, amount)
            if response.status_code == 200:
                st.success(f"Баланс успешно пополнен на {amount} кредитов!")
                st.rerun()
            else:
                try:
                    error_msg = response.json().get("detail", "Ошибка пополнения баланса")
                except:
                    error_msg = "Ошибка пополнения баланса"
                st.error(f"Ошибка: {error_msg}")
    
    # История транзакций
    st.subheader("История транзакций")
    response = get_transactions(st.session_state.token)
    
    if response.status_code == 200:
        transactions = response.json()
        if transactions and len(transactions) > 0:
            # Преобразуем данные для отображения
            transactions_data = []
            for tx in transactions:
                transactions_data.append({
                    "ID": tx.get("id"),
                    "Дата": tx.get("created_at"),
                    "Тип": "Пополнение" if tx.get("amount", 0) > 0 else "Списание",
                    "Сумма": tx.get("amount"),
                    "Описание": tx.get("description", ""),
                })
            
            # Создаем DataFrame и отображаем его
            df = pd.DataFrame(transactions_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("У вас пока нет транзакций")
    else:
        st.error("Не удалось загрузить историю транзакций")
else:
    st.error("Не удалось получить информацию о балансе")
