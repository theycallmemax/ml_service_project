import streamlit as st
import json
from utils import login, register

# Конфигурация страницы
st.set_page_config(
    page_title="ML-сервис предсказаний цен криптовалют",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Инициализация сессии
if "token" not in st.session_state:
    st.session_state.token = None

# Заголовок страницы
st.title("ML-сервис предсказаний цен криптовалют")

# Если пользователь уже вошел, перенаправляем на страницу предсказаний
if st.session_state.token:
    st.info("Вы уже вошли в систему!")
    st.page_link("pages/📈Предсказания.py", label="📈 Предсказания")
    st.page_link("pages/📃История.py", label="📃 История")
    st.page_link("pages/💰Баланс.py", label="💰 Баланс")
    
    if st.button("Выйти"):
        st.session_state.token = None
        st.rerun()
else:
    # Создаем вкладки для входа и регистрации
    tab1, tab2 = st.tabs(["Вход", "Регистрация"])
    
    with tab1:
        st.header("Вход в систему")
        with st.form("login_form"):
            email = st.text_input("Электронная почта")
            password = st.text_input("Пароль", type="password")
            submit_button = st.form_submit_button("Войти")
            
            if submit_button:
                if not email or not password:
                    st.error("Введите электронную почту и пароль")
                else:
                    response = login(email, password)
                    if response.status_code == 200:
                        st.success("Успешный вход!")
                        # Сохраняем токен в сессии
                        data = response.json()
                        st.session_state.token = data["access_token"]
                        st.rerun()
                    else:
                        try:
                            error_msg = response.json().get("detail", "Ошибка входа")
                        except:
                            error_msg = "Неверный логин или пароль"
                        st.error(f"Ошибка: {error_msg}")
    
    with tab2:
        st.header("Регистрация")
        with st.form("register_form"):
            email = st.text_input("Электронная почта")
            password = st.text_input("Пароль", type="password")
            password_confirm = st.text_input("Подтвердите пароль", type="password")
            submit_button = st.form_submit_button("Зарегистрироваться")
            
            if submit_button:
                if not email or not password or not password_confirm:
                    st.error("Заполните все поля")
                elif password != password_confirm:
                    st.error("Пароли не совпадают")
                elif len(password) < 6:
                    st.error("Пароль должен быть не менее 6 символов")
                else:
                    response = register(email, password)
                    if response.status_code == 201:
                        st.success("Регистрация успешна! Теперь вы можете войти в систему.")
                    else:
                        try:
                            error_msg = response.json().get("detail", "Ошибка регистрации")
                        except:
                            error_msg = "Ошибка регистрации"
                        st.error(f"Ошибка: {error_msg}")

    st.markdown("---")
    st.markdown("Зарегистрируйтесь или войдите, чтобы начать работу.")
