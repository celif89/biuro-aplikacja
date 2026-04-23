import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA LOGOWANIA
def check_password():
    def password_entered():
        if st.session_state["password"] == "biuroaplus10!": # <--- TWOJE HASŁO
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Podaj hasło", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    st.set_page_config(page_title="Manager Biura", layout="wide")
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)

    # Inicjalizacja pamięci wybranego projektu
    if "selected_project" not in st.session_state:
        st.session_state.selected_project = None

    # --- WIDOK 1: SZCZEGÓŁY PROJEKTU ---
    if st.session_state.selected_project is not None:
        idx = st.session_state.selected_project
        project_data = df.iloc[idx]

        if st.button("⬅️ Powrót do listy"):
            st.session_state.selected_project = None
            st.rerun()

        st.header(f"Projekt: {project_data['Nazwa']}")
        st.subheader("Szczegółowe informacje")

        # Formularz edycji szczegółów
        with st.form("edycja_szczegolowa"):
            col1, col2 = st.columns(2)
            with col1:
                n_nazwa = st.text_input("Nazwa", project_data['Nazwa'])
                n_inwestor = st.text_input("Inwestor", project_data['Inwestor'])
            with col2:
                n_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"], 
                                     index=["Koncepcja", "PNB", "Wykonawczy", "Nadzór"].index(project_data['Etap']))
                n_pracownik = st.text_input("Osoba", project_data['Pracownik'])
            
            # Tutaj możesz dodać nowe pola, których nie ma w głównej tabeli, 
            # ale na razie edytujemy te podstawowe
            n_opis = st.text_area("Dodatkowe notatki (widoczne w Arkuszu)")

            if st.form_submit_button("💾 Zapisz i wróć"):
                df.at[idx, 'Nazwa'] = n_nazwa
                df.at[idx, 'Inwestor'] = n_inwestor
                df.at[idx, 'Etap'] = n_etap
                df.at[idx, 'Pracownik'] = n_pracownik
                # Jeśli dodasz kolumnę 'Notatki' w Arkuszu Google, odkomentuj linię niżej:
                # df.at[idx, 'Notatki'] = n_opis
                
                conn.update(data=df)
                st.success("Zapisano!")
                st.session_state.selected_project = None
                st.rerun()

    # --- WIDOK 2: GŁÓWNA LISTA ---
    else:
        st.title("🏗️ System Zarządzania Projektami")
        
        if not df.empty:
            # Tworzymy kolumny: przycisk + dane
            for i, row in df.iterrows():
                col_btn, col_txt = st.columns([1, 10])
                with col_btn:
                    if st.button("👁️", key=f"btn_{i}"):
                        st.session_state.selected_project = i
                        st.rerun()
                with col_txt:
                    st.write(f"**{row['Nazwa']}** | {row['Inwestor']} | Etap: {row['Etap']} | Termin: {row['Termin']}")
                st.divider()
        else:
            st.info("Baza jest pusta.")

        # Dodawanie w sidebarze (zostaje bez zmian)
        with st.sidebar.form("nowy"):
            st.write("Dodaj nowy projekt")
            # ... (tutaj kod dodawania z poprzedniej wersji)
