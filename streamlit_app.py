import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA, STYLE I CSS ---
st.set_page_config(page_title="Manager Biura PRO", layout="wide")

st.markdown("""
    <style>
    /* Maksymalne wykorzystanie szerokości */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 98%; }
    
    /* Kompaktowe wiersze tabeli */
    .project-row {
        border-bottom: 1px solid #f0f2f6;
        padding: 5px 10px;
        margin-bottom: 0px;
        display: flex;
        align-items: center;
    }
    .project-row:hover { background-color: #f8f9fa; }
    
    /* Odchudzenie przycisków */
    .stButton>button {
        padding: 2px 5px !important;
        height: 26px !important;
        font-size: 14px !important;
        line-height: 1 !important;
    }

    /* Mniejsza czcionka dla danych pomocniczych */
    .small-text { font-size: 0.85rem; color: #555; }
    .mini-icons { font-size: 0.9rem; margin-left: 5px; }
    
    /* Styl badge dla etapu */
    .etap-badge {
        font-size: 0.75rem; 
        background: #e1f5fe; 
        color: #01579b; 
        padding: 2px 8px; 
        border-radius: 12px; 
        text-align: center;
        font-weight: bold;
    }
    
    /* Redukcja odstępów Streamlit */
    div[data-testid="stVerticalBlock"] > div { gap: 0.2rem !important; }
    hr { margin: 0.5rem 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE I CACHING ---
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

# --- 3. SYSTEM LOGOWANIA ---
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
        else:
            st.error("Błędne hasło")
    st.stop()

# --- 4. GŁÓWNA APLIKACJA ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# SIDEBAR (KOMPAKTOWY)
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user_name}**")
    if st.button("🏠 Lista Główna"):
        st.session_state.selected_project = None
        st.rerun()
    if st.button("🔄 Odśwież"):
        odswiez_baze()
        st.rerun()
    st.divider()
    with st.expander("➕ Nowy Projekt"):
        with st.form("nowy"):
            n_nazwa = st.text_input("Nazwa")
            n_inw = st.text_input("Inwestor")
            if st.form_submit_button("Dodaj"):
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
    st.header(f"📂 {row['Nazwa']}")

    c1, c2 = st.columns(2)
    link_d = row.get('Link_Drive', "")
    link_m = row.get('Link_Mapa', "")

    with c1:
        if pd.notnull(link_d) and str(link_d).startswith("http"):
            st.link_button("🚀 Pełny Google Drive", str(link_d), type="primary")
        else: st.info("Brak linku Drive")
    with c2:
        if pd.notnull(link_m) and str(link_m).startswith("http"):
            st.link_button("📍 Google Maps", str(link_m))
        else: st.info("Brak linku Mapy")

    # PODGLĄD DRIVE
    if pd.notnull(link_d) and "drive.google.com" in str(link_d):
        with st.expander("🔍 Podgląd dokumentacji", expanded=True):
            try:
                url_str = str(link_d)
                if "/folders/" in url_str:
                    f_id = url_str.split("/folders/")[1].split("?")[0]
                    embed_url = f"https://drive.google.com/embeddedfolderview?id={f_id}#list"
                    st.components.v1.iframe(embed_url, height=500, scrolling=True)
                elif "/file/d/" in url_str:
                    f_id = url_str.split("/file/d/")[1].split("/")[0]
                    st.components.v1.iframe(f"https://drive.google.com/file/d/{f_id}/preview", height=500)
            except: st.error("Błąd ładowania podglądu")

    with st.form("edycja_full"):
        col1, col2 = st.columns(2)
        with col1:
            e_nazwa = st.text_input("Nazwa", row['Nazwa'])
            e_inw = st.text_input("Inwestor", row['Inwestor'])
            e_drive = st.text_input("Link Drive", row.get('Link_Drive', ""))
        with col2:
            e_prac = st.text_input("Osoba", row.get('Pracownik', ""))
            e_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"], index=0)
            e_mapa = st.text_input("Link Mapa", row.get('Link_Mapa', ""))
        e_notatki = st.text_area("Notatki", str(row.get('Notatki', "")), height=150)
        
        if st.form_submit_button("💾 Zapisz"):
            for col in ['Nazwa', 'Inwestor', 'Link_Drive', 'Link_Mapa', 'Pracownik', 'Etap', 'Notatki']:
                if col not in df.columns: df[col] = ""
                df[col] = df[col].astype(str)
            df.at[idx, 'Nazwa'], df.at[idx, 'Inwestor'] = e_nazwa, e_inw
            df.at[idx, 'Link_Drive'], df.at[idx, 'Link_Mapa'] = e_drive, e_mapa
            df.at[idx, 'Pracownik'], df.at[idx, 'Etap'] = e_prac, e_etap
            df.at[idx, 'Notatki'] = e_notatki
            df.at[idx, 'Ostatnia_Zmiana'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.update(worksheet="Projekty", data=df)
            zapisz_log(st.session_state.user_name, e_nazwa, "Edycja")
            odswiez_baze()
            st.session_state.selected_project = None
            st.rerun()

# --- WIDOK LISTY (KOMPAKTOWY) ---
else:
    st.subheader("🏗️ Lista Projektów")
    
    # Toast z powiadomieniem
    logs_df = pobierz_dane("Logi")
    if not logs_df.empty:
        n_l = logs_df[(logs_df['Data'] > st.session_state.last_login) & (logs_df['Uzytkownik'] != st.session_state.user_name)]
        if not n_l.empty: st.toast(f"🔔 {len(n_l)} nowych zmian!", icon="🆕")

    # Nagłówki
    h = st.columns([0.5, 4, 3, 2, 1.5])
    h[0].caption("Otwórz")
    h[1].caption("Nazwa projektu")
    h[2].caption("Inwestor")
    h[3].caption("Prowadzący")
    h[4].caption("Etap")
    st.divider()

    if not df.empty:
        for i, row in df.iterrows():
            czy_nowe = str(row.get('Ostatnia_Zmiana', "")) > st.session_state.last_login
            bg_color = 'background-color: #f0fff4;' if czy_nowe else ''
            
            st.markdown(f'<div class="project-row" style="{bg_color}">', unsafe_allow_html=True)
            cols = st.columns([0.5, 4, 3, 2, 1.5])
            
            with cols[0]:
                if st.button("👁️", key=f"v_{i}"):
                    st.session_state.selected_project = i
                    st.rerun()
            
            with cols[1]:
                d_ico = "📁" if pd.notnull(row.get('Link_Drive')) and "http" in str(row.get('Link_Drive')) else ""
                m_ico = "📍" if pd.notnull(row.get('Link_Mapa')) and "http" in str(row.get('Link_Mapa')) else ""
                tag = "🟢 " if czy_nowe else ""
                st.markdown(f"{tag}**{row['Nazwa']}** <span class='mini-icons'>{d_ico}{m_ico}</span>", unsafe_allow_html=True)
            
            cols[2].markdown(f"<span class='small-text'>{row['Inwestor']}</span>", unsafe_allow_html=True)
            cols[3].markdown(f"<span class='small-text'>{row.get('Pracownik', '-')}</span>", unsafe_allow_html=True)
            
            with cols[4]:
                st.markdown(f'<div class="etap-badge">{row["Etap"]}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
