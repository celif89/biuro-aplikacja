import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA I STYLE ---
st.set_page_config(page_title="Manager Biura PRO", layout="wide")

st.markdown("""
    <style>
    /* Ograniczenie szerokości głównego kontenera do 1300px i wyśrodkowanie go */
    .main > div {
        max-width: 1000px;
        margin-left: auto;
        margin-right: auto;
    }
    
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    /* Stylizacja wierszy projektów */
    .project-row { 
        border-bottom: 1px solid #f0f2f6; 
        padding: 8px 10px; 
        display: flex; 
        align-items: center; 
    }
    .project-row:hover { background-color: #f9f9f9; }
    
    /* Przyciski i odznaki */
    .stButton>button { padding: 2px 10px !important; height: 30px !important; font-size: 14px !important; }
    .small-text { font-size: 0.85rem; color: #555; }
    .etap-badge { 
        font-size: 0.75rem; 
        background: #e1f5fe; 
        color: #01579b; 
        padding: 2px 10px; 
        border-radius: 12px; 
        font-weight: bold; 
        display: inline-block;
    }
    
    /* Styl dla checkboxów zadań */
    div[data-testid="stCheckbox"] {
        padding: 5px;
        background: #fcfcfc;
        border-radius: 5px;
        margin-bottom: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE I FUNKCJE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl=0)
    except: return pd.DataFrame()

def odswiez_baze():
    st.cache_data.clear()

def zapisz_log(uzytkownik, projekt, akcja):
    try:
        logs_df = pobierz_dane("Logi")
        nowy_log = pd.DataFrame([{"Data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                  "Uzytkownik": uzytkownik, "Projekt": projekt, "Akcja": akcja}])
        conn.update(worksheet="Logi", data=pd.concat([logs_df, nowy_log], ignore_index=True))
    except: pass

# --- 3. SYSTEM LOGOWANIA ---
if "password_correct" not in st.session_state:
    st.title("🔐 Logowanie do Systemu")
    uzytkownik = st.selectbox("Wybierz użytkownika", ["Adam"])
    haslo = st.text_input("Wprowadź hasło", type="password")
    if st.button("Zaloguj"):
        if haslo == "biuro":
            st.session_state.update({
                "user_name": uzytkownik, 
                "password_correct": True, 
                "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()
    st.stop()

# --- 4. GŁÓWNA APLIKACJA ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"👤 {st.session_state.user_name}")
    if st.button("🏠 Lista Główna Projektów", use_container_width=True):
        st.session_state.selected_project = None
        st.rerun()
    if st.button("🔄 Odśwież Bazę", use_container_width=True):
        odswiez_baze()
        st.rerun()
    st.divider()
    with st.expander("➕ Nowy Projekt"):
        with st.form("new_p", clear_on_submit=True):
            n_nazwa = st.text_input("Nazwa projektu")
            n_inw = st.text_input("Inwestor")
            if st.form_submit_button("Dodaj Projekt"):
                if n_nazwa:
                    new = pd.DataFrame([{"Nazwa": n_nazwa, "Inwestor": n_inw, "Etap": "Koncepcja", 
                                         "Ostatnia_Zmiana": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                    conn.update(worksheet="Projekty", data=pd.concat([df, new], ignore_index=True))
                    zapisz_log(st.session_state.user_name, n_nazwa, "Nowy projekt")
                    odswiez_baze(); st.rerun()
    st.divider()
    if st.button("🚪 Wyloguj"):
        del st.session_state["password_correct"]
        st.rerun()

# --- WIDOK SZCZEGÓŁÓW ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    st.title(f"📂 Projekt: {row['Nazwa']}")

    tab1, tab2, tab3 = st.tabs(["📋 Dane i Zadania", "📝 Dziennik Postępów", "⚙️ Ustawienia i Pliki"])

    with tab1:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.subheader("📌 Metryka Projektu")
            m_text = st.text_area("Informacje o umowie i zakresie prac:", 
                                  value=str(row.get('Metryka', "")) if pd.notnull(row.get('Metryka')) else "", height=300)
            if st.button("Zapisz Metrykę"):
                df.at[idx, 'Metryka'] = m_text
                conn.update(worksheet="Projekty", data=df); odswiez_baze(); st.success("Zapisano dane umowy")

        with col_m2:
            st.subheader("✅ Lista Zadań (To-Do)")
            zadania_raw = str(row.get('Lista_Zadań', ""))
            lista_z = [z.split("|") for z in zadania_raw.split("||") if "|" in z]
            
            zmiana = False
            nowa_lista = []
            for i, z in enumerate(lista_z):
                checked = st.checkbox(z[0], value=(z[1] == "1"), key=f"task_{i}")
                nowy_s = "1" if checked else "0"
                if nowy_s != z[1]: zmiana = True
                nowa_lista.append(f"{z[0]}|{nowy_s}")
            
            if zmiana:
                df.at[idx, 'Lista_Zadań'] = "||".join(nowa_lista)
                conn.update(worksheet="Projekty", data=df); odswiez_baze(); st.rerun()

            with st.form("add_t", clear_on_submit=True):
                nt = st.text_input("Nowe zadanie:")
                if st.form_submit_button("➕ Dodaj do listy"):
                    if nt:
                        entry = f"{nt}|0"
                        df.at[idx, 'Lista_Zadań'] = entry if not zadania_raw or zadania_raw=="nan" else zadania_raw + "||" + entry
                        conn.update(worksheet="Projekty", data=df); odswiez_baze(); st.rerun()

    with tab2:
        st.subheader("📝 Dziennik Robót")
        hist = str(row.get('Notatki', ""))
        if hist and hist != "nan":
            for wpis in reversed(hist.split("||")):
                if "|" in wpis:
                    cz = wpis.split("|")
                    st.info(f"📅 **{cz[0]}** | 👤 **{cz[1]}** | {cz[2]}")
        with st.form("d_wpis"):
            wpis_t = st.text_input("Dodaj nowy opis postępu prac:")
            if st.form_submit_button("Zapisz w Dzienniku"):
                dt = datetime.datetime.now().strftime("%d.%m.%Y")
                nw = f"{dt}|{st.session_state.user_name}|{wpis_t}"
                df.at[idx, 'Notatki'] = nw if not hist or hist=="nan" else hist + "||" + nw
                conn.update(worksheet="Projekty", data=df); odswiez_baze(); st.rerun()

    with tab3:
        st.subheader("⚙️ Linki i Podgląd Drive")
        with st.form("set_f"):
            c_s1, c_s2 = st.columns(2)
            e_inw = c_s1.text_input("Inwestor", row['Inwestor'])
            e_etap = c_s1.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"])
            e_prac = c_s1.text_input("Prowadzący", row.get('Pracownik', ""))
            e_drive = c_s2.text_input("Link Google Drive", row.get('Link_Drive', ""))
            e_mapa = c_s2.text_input("Link Google Maps", row.get('Link_Mapa', ""))
            if st.form_submit_button("💾 Zapisz Ustawienia"):
                # Konwersja na str, aby uniknąć TypeError
                for c in ['Link_Drive', 'Link_Mapa', 'Inwestor', 'Etap', 'Pracownik']: df[c] = df[c].astype(str)
                df.at[idx, 'Inwestor'], df.at[idx, 'Etap'], df.at[idx, 'Pracownik'] = e_inw, e_etap, e_prac
                df.at[idx, 'Link_Drive'], df.at[idx, 'Link_Mapa'] = e_drive, e_mapa
                conn.update(worksheet="Projekty", data=df); odswiez_baze(); st.rerun()
        
        st.divider()
        link_d = row.get('Link_Drive', "")
        if pd.notnull(link_d) and "drive.google.com" in str(link_d):
            st.subheader("📂 Podgląd Dokumentacji")
            if "/folders/" in str(link_d):
                fid = str(link_d).split("/folders/")[1].split("?")[0]
                st.components.v1.iframe(f"https://drive.google.com/embeddedfolderview?id={fid}#list", height=500)

# --- WIDOK LISTY GŁÓWNEJ ---
else:
    st.subheader("🏗️ Aktywne Projekty")
    h = st.columns([0.5, 4, 3, 2, 1.5])
    h[0].caption("Otwórz"); h[1].caption("Nazwa projektu"); h[2].caption("Inwestor"); h[3].caption("Prowadzący"); h[4].caption("Etap")
    st.divider()

    for i, row in df.iterrows():
        czy_n = str(row.get('Ostatnia_Zmiana', "")) > st.session_state.last_login
        st.markdown(f'<div class="project-row" style="{"background:#fafffa; border-left: 5px solid #28a745;" if czy_n else ""}">', unsafe_allow_html=True)
        c = st.columns([0.5, 4, 3, 2, 1.5])
        with c[0]:
            if st.button("👁️", key=f"L_{i}"):
                st.session_state.selected_project = i; st.rerun()
        
        d_i = "📁" if pd.notnull(row.get('Link_Drive')) and "http" in str(row.get('Link_Drive')) else ""
        m_i = "📍" if pd.notnull(row.get('Link_Mapa')) and "http" in str(row.get('Link_Mapa')) else ""
        
        c[1].markdown(f"{'🟢 ' if czy_n else ''}**{row['Nazwa']}** <span class='mini-icons'>{d_i}{m_i}</span>", unsafe_allow_html=True)
        c[2].markdown(f"<span class='small-text'>{row['Inwestor']}</span>", unsafe_allow_html=True)
        c[3].markdown(f"<span class='small-text'>{row.get('Pracownik', '-')}</span>", unsafe_allow_html=True)
        with c[4]: st.markdown(f'<div class="etap-badge">{row["Etap"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
