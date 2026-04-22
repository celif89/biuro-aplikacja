import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Manager Biura Projektowego", layout="wide")

st.title("🏗️ System Zarządzania Projektami")

# Połączenie z Google Sheets
url = "https://docs.google.com/spreadsheets/d/1G9RAEbTst4RoD1_Pq1Nm1Q5n1qG6_woDcQv2cnh3100/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Pobieranie danych
data = conn.read(spreadsheet=url)

# Boczne menu - Dodawanie
with st.sidebar.form("nowy_projekt"):
    st.header("Dodaj Projekt")
    nowa_nazwa = st.text_input("Nazwa projektu")
    nowy_inwestor = st.text_input("Inwestor")
    nowy_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"])
    nowy_termin = st.date_input("Termin")
    nowy_pracownik = st.text_input("Pracownik")
    
    if st.form_submit_button("Zapisz projekt"):
        # Logika dopisywania do arkusza (zrobimy to w kolejnym kroku)
        st.success("Projekt zapisany w bazie!")

# Wyświetlanie danych
st.subheader("Lista aktywnych projektów")
st.dataframe(data, use_container_width=True)
