import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA STRONY I STYLE ---
st.set_page_config(page_title="Manager Biura PRO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; }
    .project-card {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #e6e9ef;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE I CACHING (PRZYŚPIESZENIE) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)  # Dane są pamiętane przez 10 minut
def pobierz_dane(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl=0)
    except Exception:
        return pd.DataFrame()

def odswiez_baze():
    st.cache_data.clear()

def zapisz_log(uzytkownik, projekt, akcja):
    try:
        logs_df = pobierz_dane("Logi")
        nowy_log = pd.DataFrame([{
            "Data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Uzytkownik": uzytkownik,
            "Projekt": projekt,
            "Akcja": akcja
        }])
        updated_logs = pd.concat([logs_df, nowy_log], ignore_index=True)
        conn.update(worksheet="Logi", data=updated_logs)
    except:
        pass

def aktualizuj_czas_logowania(uzytkownik):
    users_df = pobierz_dane("Uzytkownicy")
    teraz = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not users_df.empty and uzytkownik in users_df['Uzytkownik'].values:
        users_df.loc[users_df['Uzytkownik'] == uzytkownik, 'OstatnieLogowanie'] = teraz
    else:
        new_user = pd.DataFrame([{"Uzytkownik": uzytkownik, "OstatnieLogowanie": teraz}])
        users_df = pd.concat([users_df, new_user], ignore_index=True)
    conn.update(worksheet="Uzytkownicy", data=users_df)
    odswiez_baze()

# --- 3. SYSTEM LOGOWANIA ---
if "password_correct" not in st.session_state:
    st.title("🔐 Logowanie")
    uzytkownicy = ["Adam", "Ewa"]
    user_name = st.selectbox("Wybierz użytkownika", uzytkownicy)
    password = st.text_input("Hasło", type="password")
    
    if st.button("Zaloguj"):
        if password == "biuro":
            users_df = pobierz_dane("Uzytkownicy")
            last_time = "2000-01-01 00:00:00"
            if not users_df.empty and user_name in users_df['Uzytkownik'].values:
                last_time = users_df.loc[users_df['Uzytkownik'] == user_name, 'OstatnieLogowanie'].values[0]
            
            st.session_state["last_login"] = last_time
            st.session_state["user_name"] = user_name
            st.session_state["password_correct"] = True
            aktualizuj_czas_logowania(user_name)
            st.rerun()
        else:
            st.error("Błędne hasło")
    st.stop()

# --- 4. GŁÓWNA LOGIKA APLIKACJI ---
# Zmień "Projekty" na nazwę swojej zakładki, jeśli jest inna!
df = pobierz_dane("Projekty")

if "selected_project" not in st.session_state:
    st.session_state.selected_project = None

# PANEL BOCZNY
with st.sidebar:
    st.header(f"👤 {st.session_state.user_name}")
    if st.button("🏠 Powrót do listy"):
        st.session_state.selected_project = None
        st.rerun()
    
    st.divider()
    with st.form("nowy_proj"):
        st.subheader("➕ Nowy Projekt")
        n_nazwa = st.text_input("Nazwa projektu")
        n_inw = st.text_input("Inwestor")
        n_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"])
        if st.form_submit_button("Dodaj"):
            if n_nazwa:
                new_row = pd.DataFrame([{
                    "Nazwa": n_nazwa, "Inwestor": n_inw, "Etap": n_etap, 
                    "Termin": str(datetime.date.today()), "Pracownik": "", 
                    "Notatki": "", "Ostatnia_Zmiana": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                df_up = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Projekty", data=df_up)
                zapisz_log(st.session_state.user_name, n_nazwa, "Dodano projekt")
                odswiez_baze()
                st.success("Dodano!")
                st.rerun()

    if st.button("🚪 Wyloguj"):
        del st.session_state["password_correct"]
        st.rerun()

# --- WIDOK SZCZEGÓŁÓW ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    
    st.title(f"📂 {row['Nazwa']}")
    
    with st.form("edycja"):
        c1, c2 = st.columns(2)
        with c1:
            e_inw = st.text_input("Inwestor", row['Inwestor'])
            e_prac = st.text_input("Pracownik", row['Pracownik'])
        with c2:
            e_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"], 
                                 index=["Koncepcja", "PNB", "Wykonawczy", "Nadzór"].index(row['Etap']) if row['Etap'] in ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"] else 0)
        
        e_notatki = st.text_area("Szczegóły / Notatki", str(row['Notatki']) if pd.notnull(row['Notatki']) else "", height=250)
        
        if st.form_submit_button("💾 Zapisz i wróć"):
            teraz = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.at[idx, 'Inwestor'] = e_inw
            df.at[idx, 'Pracownik'] = e_prac
            df.at[idx, 'Etap'] = e_etap
            df.at[idx, 'Notatki'] = e_notatki
            df.at[idx, 'Ostatnia_Zmiana'] = teraz
            
            conn.update(worksheet="Projekty", data=df)
            zapisz_log(st.session_state.user_name, row['Nazwa'], "Edycja danych")
            odswiez_baze()
            st.session_state.selected_project = None
            st.rerun()

# --- WIDOK LISTY ---
else:
    st.title("🏗️ System Biura Projektowego")
    
    # Powiadomienia
    logs_df = pobierz_dane("Logi")
    if not logs_df.empty:
        nowe = logs_df[(logs_df['Data'] > st.session_state.last_login) & (logs_df['Uzytkownik'] != st.session_state.user_name)]
        if not nowe.empty:
            with st.expander(f"🔔 Nowe zmiany ({len(nowe)})", expanded=True):
                for _, log in nowe.sort_values(by="Data", ascending=False).iterrows():
                    st.info(f"**{log['Uzytkownik']}** edytował **{log['Projekt']}** ({log['Data']})")

    # Lista projektów
    if not df.empty:
        for i, row in df.iterrows():
            # Logika kolorowania (zielony jeśli nowe)
            czy_nowe = False
            if 'Ostatnia_Zmiana' in row and pd.notnull(row['Ostatnia_Zmiana']):
                if str(row['Ostatnia_Zmiana']) > st.session_state.last_login and row.get('Uzytkownik_Zmiany') != st.session_state.user_name:
                    czy_nowe = True
            
            bg_color = "#d4edda" if czy_nowe else "white"
            border_color = "#28a745" if czy_nowe else "#e6e9ef"
            
            st.markdown(f'<div style="background-color:{bg_color}; border: 2px solid {border_color}; padding:15px; border-radius:10px; margin-bottom:10px;">', unsafe_allow_html=True)
            cols = st.columns([1, 4, 3, 2])
            with cols[0]:
                if st.button("👁️", key=f"btn_{i}"):
                    st.session_state.selected_project = i
                    st.rerun()
            cols[1].markdown(f"**{row['Nazwa']}**")
            cols[2].write(row['Inwestor'])
            cols[3].write(f"Etap: {row['Etap']}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Brak projektów. Dodaj pierwszy w panelu bocznym!")
