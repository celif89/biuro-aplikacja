import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA I STYLE ---
st.set_page_config(page_title="Manager Biura PRO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    /* Stylizacja kart projektów */
    .project-card {
        border: 1px solid #e6e9ef;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE I FUNKCJE POMOCNICZE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl=0)
    except:
        return pd.DataFrame()

def odswiez_baze():
    st.cache_data.clear()

def zapisz_log(uzytkownik, projekt, akcja):
    try:
        logs_df = pobierz_dane("Logi")
        nowy_log = pd.DataFrame([{
            "Data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Uzytkownik": uzytkownik, "Projekt": projekt, "Akcja": akcja
        }])
        conn.update(worksheet="Logi", data=pd.concat([logs_df, nowy_log], ignore_index=True))
    except: pass

def aktualizuj_czas_logowania(uzytkownik):
    users_df = pobierz_dane("Uzytkownicy")
    teraz = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not users_df.empty and uzytkownik in users_df['Uzytkownik'].values:
        users_df.loc[users_df['Uzytkownik'] == uzytkownik, 'OstatnieLogowanie'] = teraz
    else:
        users_df = pd.concat([users_df, pd.DataFrame([{"Uzytkownik": uzytkownik, "OstatnieLogowanie": teraz}])], ignore_index=True)
    conn.update(worksheet="Uzytkownicy", data=users_df)
    odswiez_baze()

# --- 3. LOGOWANIE ---
if "password_correct" not in st.session_state:
    st.title("🔐 System Zarządzania Biurem")
    user_name = st.selectbox("Wybierz użytkownika", ["Adam", "Ewa"])
    password = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if password == "biuro":
            u_df = pobierz_dane("Uzytkownicy")
            last = u_df.loc[u_df['Uzytkownik'] == user_name, 'OstatnieLogowanie'].values[0] if not u_df.empty and user_name in u_df['Uzytkownik'].values else "2000-01-01 00:00:00"
            st.session_state.update({"last_login": last, "user_name": user_name, "password_correct": True})
            aktualizuj_czas_logowania(user_name)
            st.rerun()
    st.stop()

# --- 4. GŁÓWNA APLIKACJA ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# SIDEBAR
with st.sidebar:
    st.header(f"👤 {st.session_state.user_name}")
    if st.button("🏠 Powrót do listy głównej"):
        st.session_state.selected_project = None
        st.rerun()
    if st.button("🔄 Odśwież dane"):
        odswiez_baze()
        st.rerun()
    st.divider()
    with st.form("nowy"):
        st.subheader("➕ Szybkie dodawanie")
        n_nazwa = st.text_input("Nazwa projektu")
        n_inw = st.text_input("Inwestor")
        if st.form_submit_button("Dodaj projekt"):
            if n_nazwa:
                new = pd.DataFrame([{"Nazwa": n_nazwa, "Inwestor": n_inw, "Etap": "Koncepcja", "Ostatnia_Zmiana": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                conn.update(worksheet="Projekty", data=pd.concat([df, new], ignore_index=True))
                zapisz_log(st.session_state.user_name, n_nazwa, "Nowy projekt")
                odswiez_baze()
                st.rerun()
    if st.button("🚪 Wyloguj"):
        del st.session_state["password_correct"]
        st.rerun()

# --- WIDOK SZCZEGÓŁÓW ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    st.title(f"📂 Projekt: {row['Nazwa']}")

    # SZYBKIE LINKI (Zawsze na górze szczegółów)
    c1, c2 = st.columns(2)
    with c1:
        link_d = row.get('Link_Drive', "")
        if pd.notnull(link_d) and str(link_d).startswith("http"):
            st.link_button("📂 Otwórz Dokumentację (Drive)", str(link_d), type="primary")
        else:
            st.info("Brak podpiętego folderu Drive.")
    with c2:
        link_m = row.get('Link_Mapa', "")
        if pd.notnull(link_m) and str(link_m).startswith("http"):
            st.link_button("📍 Zobacz lokalizację (Maps)", str(link_m))
        else:
            st.info("Brak podpiętej mapy.")

    st.divider()

    with st.form("edycja_full"):
        col1, col2 = st.columns(2)
        with col1:
            e_nazwa = st.text_input("Nazwa", row['Nazwa'])
            e_inw = st.text_input("Inwestor", row['Inwestor'])
            e_drive = st.text_input("Link Google Drive (Folder)", row.get('Link_Drive', ""))
        with col2:
            e_prac = st.text_input("Pracownik", row.get('Pracownik', ""))
            e_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"], index=0)
            e_mapa = st.text_input("Link Google Maps (Lokalizacja)", row.get('Link_Mapa', ""))
        
        e_notatki = st.text_area("Szczegółowe notatki projektowe", str(row.get('Notatki', "")), height=200)
        
        if st.form_submit_button("💾 Zapisz wszystkie zmiany"):
            df.at[idx, 'Nazwa'], df.at[idx, 'Inwestor'] = e_nazwa, e_inw
            df.at[idx, 'Link_Drive'], df.at[idx, 'Link_Mapa'] = e_drive, e_mapa
            df.at[idx, 'Pracownik'], df.at[idx, 'Etap'] = e_prac, e_etap
            df.at[idx, 'Notatki'] = e_notatki
            df.at[idx, 'Ostatnia_Zmiana'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn.update(worksheet="Projekty", data=df)
            zapisz_log(st.session_state.user_name, e_nazwa, "Aktualizacja danych i linków")
            odswiez_baze()
            st.session_state.selected_project = None
            st.rerun()

# --- WIDOK LISTY ---
else:
    st.title("🏗️ Zarządzanie Projektami")
    
    # Powiadomienia
    logs_df = pobierz_dane("Logi")
    if not logs_df.empty:
        n_l = logs_df[(logs_df['Data'] > st.session_state.last_login) & (logs_df['Uzytkownik'] != st.session_state.user_name)]
        if not n_l.empty:
            st.success(f"🔔 Masz {len(n_l)} nowych zmian od współpracowników!")

    st.divider()
    if not df.empty:
        for i, row in df.iterrows():
            czy_nowe = str(row.get('Ostatnia_Zmiana', "")) > st.session_state.last_login
            bg = "#f0fff4" if czy_nowe else "white"
            brdr = "#c6f6d5" if czy_nowe else "#e2e8f0"
            
            st.markdown(f'<div style="background-color:{bg}; border: 1px solid {brdr}; padding:15px; border-radius:10px; margin-bottom:10px;">', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns([1, 4, 3, 2])
            with c1:
                if st.button("👁️", key=f"v_{i}"):
                    st.session_state.selected_project = i
                    st.rerun()
            
            # Ikony informacyjne obok nazwy
            drive_icon = "📁 " if pd.notnull(row.get('Link_Drive')) and str(row.get('Link_Drive')).startswith("http") else ""
            map_icon = "📍 " if pd.notnull(row.get('Link_Mapa')) and str(row.get('Link_Mapa')).startswith("http") else ""
            
            c2.markdown(f"{'🟢 ' if czy_nowe else ''}**{row['Nazwa']}** <br> <small>{drive_icon}{map_icon}</small>", unsafe_allow_html=True)
            c3.write(row['Inwestor'])
            c4.info(row['Etap'])
            st.markdown('</div>', unsafe_allow_html=True)
