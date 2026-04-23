import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. KONFIGURACJA LOGOWANIA
def check_password():
    """Zwraca True, jeśli użytkownik wpisał poprawne hasło."""
    def password_entered():
        if st.session_state["password"] == "biuroaplus10!": # <--- TUTAJ WPISZ HASŁO
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Podaj hasło do systemu biura", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Błędne hasło, spróbuj ponownie", type="password", on_change=password_entered, key="password")
        st.error("😕 Hasło niepoprawne")
        return False
    else:
        return True

# 2. JEŚLI HASŁO JEST POPRAWNE, POKAŻ RESZTĘ APLIKACJI
if check_password():
    st.set_page_config(page_title="Manager Biura", layout="wide")
    
    # Dodaj przycisk wylogowania w panelu bocznym
    if st.sidebar.button("Wyloguj"):
        st.session_state["password_correct"] = False
        st.rerun()

    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)

    st.title("🏗️ System Zarządzania Projektami")

    # Wyświetlanie i edycja
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    if st.button("💾 Zapisz zmiany"):
        conn.update(data=edited_df)
        st.success("Zapisano pomyślnie!")
        st.rerun()
