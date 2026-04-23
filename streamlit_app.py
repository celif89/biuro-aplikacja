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
    if st.button("🔄 Odśwież dane"):
    odswiez_baze()
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

# --- WIDOK LISTY (POPRAWIONY) ---
else:
    st.title("🏗️ System Biura Projektowego")
    
    # Powiadomienia o nowościach
    logs_df = pobierz_dane("Logi")
    if not logs_df.empty:
        nowe = logs_df[(logs_df['Data'] > st.session_state.last_login) & (logs_df['Uzytkownik'] != st.session_state.user_name)]
        if not nowe.empty:
            st.success(f"🔔 Masz {len(nowe)} nowe zmiany od ostatniej wizyty! Sprawdź projekty oznaczone 🟢")

    st.divider()

    # Nagłówki tabeli (ukryte na małych ekranach automatycznie przez Streamlit)
    h_col1, h_col2, h_col3, h_col4 = st.columns([1, 4, 3, 2])
    h_col1.write("**Otwórz**")
    h_col2.write("**Nazwa Projektu**")
    h_col3.write("**Inwestor**")
    h_col4.write("**Etap**")
    st.divider()

    if not df.empty:
        for i, row in df.iterrows():
            # Sprawdzanie nowości
            czy_nowe = False
            if 'Ostatnia_Zmiana' in row and pd.notnull(row['Ostatnia_Zmiana']):
                if str(row['Ostatnia_Zmiana']) > st.session_state.last_login:
                    czy_nowe = True
            
            # Tworzymy wiersz
            cols = st.columns([1, 4, 3, 2])
            
            with cols[0]:
                if st.button("👁️", key=f"btn_{i}"):
                    st.session_state.selected_project = i
                    st.rerun()
            
            with cols[1]:
                # Dodajemy zieloną kropkę jeśli projekt jest nowy
                oznaczenie = "🟢 " if czy_nowe else ""
                st.markdown(f"{oznaczenie}**{row['Nazwa']}**")
            
            with cols[2]:
                st.write(row['Inwestor'])
                
            with cols[3]:
                # Kolorujemy tekst etapu dla lepszej widoczności
                st.info(row['Etap'])
            
            st.write("---") # Linia oddzielająca projekty
    else:
        st.info("Baza jest pusta.")
