import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA LOGOWANIA
def check_password():
    def password_entered():
        if st.session_state["password"] == "biuro": # <--- TWOJE HASŁO
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Podaj hasło", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if check_password():
    st.set_page_config(page_title="Manager Biura", layout="wide")
    
    # Połączenie i dane
    url = "https://docs.google.com/spreadsheets/d/1G9RAEbTst4RoD1_Pq1Nm1Q5n1qG6_woDcQv2cnh3100/edit?usp=sharing"
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)

    # Inicjalizacja pamięci wybranego projektu
    if "selected_project" not in st.session_state:
        st.session_state.selected_project = None

    # --- PANEL BOCZNY (Zawsze widoczny) ---
    with st.sidebar:
        st.header("⚙️ Opcje")
        if st.button("🏠 Powrót do listy głównej"):
            st.session_state.selected_project = None
            st.rerun()
            
        st.divider()
        
        # FORMULARZ DODAWANIA - Tutaj był błąd (brakowało przycisku submit)
        with st.form("form_nowy_projekt"):
            st.subheader("➕ Nowy Projekt")
            n_nazwa = st.text_input("Nazwa projektu")
            n_inwestor = st.text_input("Inwestor")
            n_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"])
            n_termin = st.date_input("Termin")
            n_pracownik = st.text_input("Osoba")
            
            # TO JEST KLUCZOWY PRZYCISK:
            btn_dodaj = st.form_submit_button("Dodaj projekt")
            
            if btn_dodaj:
                if n_nazwa:
                    new_row = pd.DataFrame([{
                        "Nazwa": n_nazwa,
                        "Inwestor": n_inwestor,
                        "Etap": n_etap,
                        "Termin": str(n_termin),
                        "Status": "W toku",
                        "Pracownik": n_pracownik
                    }])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=url, data=updated_df)
                    st.success("Dodano!")
                    st.rerun()
                else:
                    st.error("Podaj nazwę!")

        st.divider()
        if st.button("🚪 Wyloguj"):
            st.session_state["password_correct"] = False
            st.rerun()

    # --- WIDOK 1: SZCZEGÓŁY PROJEKTU ---
    if st.session_state.selected_project is not None:
        idx = st.session_state.selected_project
        project_data = df.iloc[idx]

        st.header(f"📂 Projekt: {project_data['Nazwa']}")
        
        with st.form("edycja_szczegolowa"):
            col1, col2 = st.columns(2)
            with col1:
                e_nazwa = st.text_input("Nazwa", project_data['Nazwa'])
                e_inwestor = st.text_input("Inwestor", project_data['Inwestor'])
            with col2:
                etapy = ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"]
                idx_etap = etapy.index(project_data['Etap']) if project_data['Etap'] in etapy else 0
                e_etap = st.selectbox("Etap", etapy, index=idx_etap)
                e_pracownik = st.text_input("Osoba", project_data['Pracownik'])
            
            st.subheader("📝 Szczegółowe notatki")
            
            # POBIERANIE NOTATEK Z BAZY DO POLA TEKSTOWEGO
            obecne_notatki = ""
            if 'Notatki' in project_data:
                obecne_notatki = str(project_data['Notatki']) if pd.notnull(project_data['Notatki']) else ""
            
            e_notatki = st.text_area("Wpisz ustalenia, numery działek, telefony itp.", value=obecne_notatki, height=200)

            if st.form_submit_button("💾 Zapisz zmiany i wróć"):
                # Aktualizacja danych w lokalnym DataFrame
                df.at[idx, 'Nazwa'] = e_nazwa
                df.at[idx, 'Inwestor'] = e_inwestor
                df.at[idx, 'Etap'] = e_etap
                df.at[idx, 'Pracownik'] = e_pracownik
                
                if 'Notatki' in df.columns:
                    df['Notatki'] = df['Notatki'].astype(str)
                    df.at[idx, 'Notatki'] = e_notatki
                
                # Wysłanie do Google Sheets
                conn.update(spreadsheet=url, data=df)
                st.success("Zapisano!")
                st.session_state.selected_project = None
                st.rerun()

    # --- WIDOK 2: GŁÓWNA LISTA ---
    else:
        st.title("🏗️ System Zarządzania Projektami")
        
        if not df.empty:
            # Nagłówki "tabeli"
            h1, h2, h3, h4 = st.columns([1, 4, 3, 3])
            h1.write("**Akcja**")
            h2.write("**Nazwa Projektu**")
            h3.write("**Inwestor**")
            h4.write("**Termin**")
            st.divider()

            for i, row in df.iterrows():
                c1, c2, c3, c4 = st.columns([1, 4, 3, 3])
                with c1:
                    if st.button("👁️", key=f"view_{i}"):
                        st.session_state.selected_project = i
                        st.rerun()
                c2.write(row['Nazwa'])
                c3.write(row['Inwestor'])
                c4.write(str(row['Termin']))
                st.divider()
        else:
            st.info("Baza projektów jest pusta.")
