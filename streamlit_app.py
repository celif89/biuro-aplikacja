import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA I STYLE ---
st.set_page_config(page_title="Manager Biura PRO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; max-width: 98%; }
    .project-row { border-bottom: 1px solid #f0f2f6; padding: 5px 10px; display: flex; align-items: center; }
    .stButton>button { padding: 2px 5px !important; height: 26px !important; font-size: 14px !important; }
    .small-text { font-size: 0.85rem; color: #555; }
    .etap-badge { font-size: 0.75rem; background: #e1f5fe; color: #01579b; padding: 2px 8px; border-radius: 12px; font-weight: bold; }
    
    /* Styl dla tabeli postępów */
    .progress-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-bottom: 10px; }
    .progress-table th { background: #f8f9fa; text-align: left; padding: 8px; border-bottom: 2px solid #dee2e6; }
    .progress-table td { padding: 8px; border-bottom: 1px solid #eee; vertical-align: top; }
    
    /* Styl dla metryki */
    .metric-box { background-color: #fcfcfc; border: 1px solid #eee; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNKCJE BAZODANOWE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl=0)
    except: return pd.DataFrame()

def odswiez_baze(): st.cache_data.clear()

def zapisz_log(uzytkownik, projekt, akcja):
    try:
        logs_df = pobierz_dane("Logi")
        nowy_log = pd.DataFrame([{"Data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Uzytkownik": uzytkownik, "Projekt": projekt, "Akcja": akcja}])
        conn.update(worksheet="Logi", data=pd.concat([logs_df, nowy_log], ignore_index=True))
    except: pass

# --- 3. LOGOWANIE ---
if "password_correct" not in st.session_state:
    st.title("🔐 Logowanie do systemu")
    user_name = st.selectbox("Użytkownik", ["Adam", "Ewa"])
    password = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if password == "biuro":
            st.session_state.update({"user_name": user_name, "password_correct": True, "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            st.rerun()
    st.stop()

# --- 4. GŁÓWNA APLIKACJA ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# --- SIDEBAR (MENU LEWE) ---
with st.sidebar:
    st.title("📁 Menu Biura")
    st.write(f"Zalogowany: **{st.session_state.user_name}**")
    
    if st.button("🏠 Lista Główna Projektów", use_container_width=True):
        st.session_state.selected_project = None
        st.rerun()
    
    if st.button("🔄 Odśwież Dane", use_container_width=True):
        odswiez_baze()
        st.rerun()
    
    st.divider()
    
    with st.expander("➕ Dodaj Nowy Projekt"):
        with st.form("nowy_p"):
            n_nazwa = st.text_input("Nazwa")
            n_inw = st.text_input("Inwestor")
            if st.form_submit_button("Dodaj do bazy"):
                if n_nazwa:
                    new = pd.DataFrame([{"Nazwa": n_nazwa, "Inwestor": n_inw, "Etap": "Koncepcja", "Ostatnia_Zmiana": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                    conn.update(worksheet="Projekty", data=pd.concat([df, new], ignore_index=True))
                    zapisz_log(st.session_state.user_name, n_nazwa, "Dodano projekt")
                    odswiez_baze()
                    st.rerun()

    st.divider()
    if st.button("🚪 Wyloguj"):
        del st.session_state["password_correct"]
        st.rerun()

# --- WIDOK SZCZEGÓŁÓW PROJEKTU ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    
    st.title(f"📂 {row['Nazwa']}")

    # LINKI AKCJI
    c_l1, c_l2 = st.columns(2)
    with c_l1: 
        if pd.notnull(row.get('Link_Drive')): st.link_button("🚀 Dokumentacja Drive", str(row['Link_Drive']), use_container_width=True)
    with c_l2:
        if pd.notnull(row.get('Link_Mapa')): st.link_button("📍 Mapa / Lokalizacja", str(row['Link_Mapa']), use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["📋 Metryka i Zadania", "📝 Dziennik Postępów", "⚙️ Ustawienia Linków"])

    # --- TAB 1: METRYKA I ZADANIA ---
    with tab1:
        col_m1, col_m2 = st.columns([1, 1])
        
        with col_m1:
            st.subheader("📌 Informacje podstawowe (Umowa)")
            with st.form("form_metryka"):
                metryka_text = st.text_area("Dane umowy, zakres, budżet, nr kontaktowy:", value=str(row.get('Metryka', "")) if pd.notnull(row.get('Metryka')) else "", height=200)
                if st.form_submit_button("Zapisz Metrykę"):
                    df.at[idx, 'Metryka'] = metryka_text
                    conn.update(worksheet="Projekty", data=df)
                    odswiez_baze()
                    st.success("Metryka zaktualizowana")

        with col_m2:
            st.subheader("✅ Co należy zrobić (To-Do)")
            lista_zadan = st.text_area("Wpisz zadania (jedno pod drugim):", value=str(row.get('Lista_Zadań', "")) if pd.notnull(row.get('Lista_Zadań')) else "", height=200)
            if st.button("Zapisz Listę Zadań"):
                df.at[idx, 'Lista_Zadań'] = lista_zadan
                conn.update(worksheet="Projekty", data=df)
                odswiez_baze()
                st.toast("Lista zadań zapisana!")

    # --- TAB 2: DZIENNIK POSTĘPÓW ---
    with tab2:
        st.subheader("Dziennik Postępów Robót")
        historia = str(row.get('Notatki', ""))
        if historia and historia != "nan":
            html_table = '<table class="progress-table"><tr><th>Data</th><th>Pracownik</th><th>Opis prac</th></tr>'
            for wpis in reversed(historia.split("||")):
                if "|" in wpis:
                    cz = wpis.split("|")
                    if len(cz) >= 3: html_table += f'<tr><td>{cz[0]}</td><td style="color:#01579b">{cz[1]}</td><td>{cz[2]}</td></tr>'
            html_table += '</table>'
            st.markdown(html_table, unsafe_allow_html=True)
        
        with st.form("nowy_wpis_dziennik"):
            nowy_postep = st.text_area("Co dziś zrobiono?")
            if st.form_submit_button("Dodaj wpis do dziennika"):
                data_dzis = datetime.datetime.now().strftime("%d.%m.%Y")
                wpis_f = f"{data_dzis}|{st.session_state.user_name}|{nowy_postep}"
                df.at[idx, 'Notatki'] = wpis_f if not historia or historia=="nan" else historia + "||" + wpis_f
                conn.update(worksheet="Projekty", data=df)
                zapisz_log(st.session_state.user_name, row['Nazwa'], "Wpis w dzienniku")
                odswiez_baze()
                st.rerun()

    # --- TAB 3: USTAWIENIA LINKÓW ---
    with tab3:
        with st.form("linki_edit"):
            e_inw = st.text_input("Inwestor", row['Inwestor'])
            e_prac = st.text_input("Prowadzący", row.get('Pracownik', ""))
            e_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"], index=0)
            e_drive = st.text_input("Link Drive", row.get('Link_Drive', ""))
            e_mapa = st.text_input("Link Mapa", row.get('Link_Mapa', ""))
            if st.form_submit_button("Zapisz parametry"):
                df.at[idx, 'Inwestor'], df.at[idx, 'Pracownik'], df.at[idx, 'Etap'] = e_inw, e_prac, e_etap
                df.at[idx, 'Link_Drive'], df.at[idx, 'Link_Mapa'] = e_drive, e_mapa
                conn.update(worksheet="Projekty", data=df)
                odswiez_baze()
                st.rerun()

# --- WIDOK LISTY GŁÓWNEJ ---
else:
    st.subheader("🏗️ Aktywne Projekty")
    # ... Nagłówki ...
    cols_h = st.columns([0.5, 4, 3, 2, 1.5])
    cols_h[0].caption("Otwórz"); cols_h[1].caption("Nazwa projektu"); cols_h[2].caption("Inwestor"); cols_h[3].caption("Prowadzący"); cols_h[4].caption("Etap")
    st.divider()

    for i, row in df.iterrows():
        st.markdown('<div class="project-row">', unsafe_allow_html=True)
        c = st.columns([0.5, 4, 3, 2, 1.5])
        with c[0]:
            if st.button("👁️", key=f"v_{i}"):
                st.session_state.selected_project = i
                st.rerun()
        c[1].markdown(f"**{row['Nazwa']}**")
        c[2].markdown(f"<span class='small-text'>{row['Inwestor']}</span>", unsafe_allow_html=True)
        c[3].markdown(f"<span class='small-text'>{row.get('Pracownik', '-')}</span>", unsafe_allow_html=True)
        with c[4]: st.markdown(f'<div class="etap-badge">{row["Etap"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
