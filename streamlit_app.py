import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Manager Biura", layout="wide")

st.title("🏗️ System Zarządzania Projektami")

# Połączenie z Google Sheets
url = "https://docs.google.com/spreadsheets/d/1G9RAEbTst4RoD1_Pq1Nm1Q5n1qG6_woDcQv2cnh3100/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Pobieranie aktualnych danych
df = conn.read(spreadsheet=url, ttl=0) # ttl=0 wymusza odświeżenie danych za każdym razem

# --- PANEL BOCZNY: DODAWANIE ---
st.sidebar.header("➕ Nowy Projekt")
with st.sidebar.form("form_dodawania"):
    n_nazwa = st.text_input("Nazwa projektu")
    n_inwestor = st.text_input("Inwestor")
    n_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"])
    n_termin = st.date_input("Termin")
    n_pracownik = st.text_input("Osoba")
    
    submit = st.form_submit_button("Dodaj do bazy")
    
    if submit:
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
            st.sidebar.success("Dodano! Odśwież stronę.")
            st.rerun()
        else:
            st.sidebar.error("Podaj nazwę projektu!")

# --- GŁÓWNY PANEL: EDYCJA I PODGLĄD ---
if not df.empty:
    st.subheader("Aktualna lista")
    
    # Edytowalna tabela (nowoczesna funkcja Streamlit)
    edited_df = st.data_editor(
        df, 
        use_container_width=True,
        num_rows="dynamic" # Pozwala usuwać wiersze (zaznacz i Delete)
    )
    
    if st.button("💾 Zapisz zmiany w tabeli"):
        conn.update(spreadsheet=url, data=edited_df)
        st.success("Zmiany zapisane w Google Sheets!")
        st.rerun()
else:
    st.info("Baza jest pusta.")
