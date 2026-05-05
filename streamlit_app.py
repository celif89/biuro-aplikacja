import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA I NOWOCZESNY DESIGN ---
st.set_page_config(page_title="Biuro PRO", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; }

    .main > div { max-width: 1200px; margin-left: auto; margin-right: auto; padding-top: 1rem; }

    /* Nagłówek główny */
    h1 { font-size: 1.6rem !important; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem !important; }
    p { font-size: 0.9rem; color: #64748b; }

    /* STYL KARTY PROJEKTU */
    .project-container {
        position: relative;
        background: white;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
        padding: 12px 20px;
        transition: all 0.2s ease;
    }
    
    .project-container:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        background: #f8faff;
    }

    .new-project { border-left: 4px solid #10b981 !important; background: #f0fdf4 !important; }

    /* TYPOGRAFIA W KARCIE */
    .proj-name { font-size: 1rem; font-weight: 600; color: #0f172a; margin-bottom: 2px; }
    .proj-info { font-size: 0.8rem; color: #64748b; }
    .proj-label { font-size: 0.75rem; font-weight: 500; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px; }
    .proj-value { font-size: 0.85rem; color: #334155; font-weight: 500; }

    /* ETYKIETA ETAPU */
    .badge {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    .b-koncepcja { background: #eff6ff; color: #2563eb; }
    .b-pnb { background: #fffbeb; color: #d97706; }
    .b-wykonawczy { background: #f0fdf4; color: #16a34a; }
    .b-nadzor { background: #faf5ff; color: #9333ea; }

    /* HACK: UKRYCIE PRZYCISKU STREAMLIT I ROZCIĄGNIĘCIE GO NA CAŁĄ KARTĘ */
    div[data-testid="stVerticalBlock"] > div:has(button[key^="pbtn_"]) {
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: 10;
        opacity: 0;
    }
    button[key^="pbtn_"] { width: 100%; height: 60px; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA DANYCH ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl=0)
    except: return pd.DataFrame()

def odswiez(): st.cache_data.clear()

def get_badge(etap):
    e = str(etap).lower()
    if 'koncepcja' in e: return 'b-koncepcja'
    if 'pnb' in e: return 'b-pnb'
    if 'wykonawczy' in e: return 'b-wykonawczy'
    return 'b-nadzor'

# --- 3. LOGOWANIE (SKRÓCONE) ---
if "password_correct" not in st.session_state:
    st.title("🏗️ Logowanie")
    u = st.selectbox("Użytkownik", ["Adam", "Ewa", "Marek", "Pracownik1"])
    p = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if p == "Haslo123":
            st.session_state.update({"user_name": u, "password_correct": True, "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            st.rerun()
    st.stop()

# --- 4. GŁÓWNA APLIKACJA ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# SIDEBAR
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user_name}**")
    if st.button("🏠 Powrót do listy", use_container_width=True):
        st.session_state.selected_project = None; st.rerun()
    if st.button("🔄 Odśwież dane", use_container_width=True):
        odswiez(); st.rerun()
    st.divider()
    if st.button("🚪 Wyloguj"):
        del st.session_state["password_correct"]; st.rerun()

# --- WIDOK SZCZEGÓŁÓW ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    
    st.title(f"Projekt: {row['Nazwa']}")
    st.markdown(f"Inwestor: **{row['Inwestor']}** | Etap: **{row['Etap']}**")
    
    tab1, tab2, tab3 = st.tabs(["📋 Metryka i Zadania", "📝 Dziennik Robót", "⚙️ Ustawienia"])
    # (Tutaj funkcjonalność pozostaje taka jak wcześniej ustalona)
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📌 Metryka")
            new_m = st.text_area("Dane umowy:", value=str(row.get('Metryka', "")), height=250)
            if st.button("Zapisz Metrykę"):
                df.at[idx, 'Metryka'] = new_m; conn.update(worksheet="Projekty", data=df); st.success("Zapisano")
        with c2:
            st.subheader("✅ Zadania")
            # Logika checkboxów...
            st.write("Tu pojawią się Twoje checkboxy zadań.")

# --- WIDOK LISTY GŁÓWNEJ ---
else:
    st.title("🏗️ Aktywne Projekty")
    st.write("Kliknij w kartę projektu, aby zobaczyć szczegóły.")
    
    st.divider()

    for i, row in df.iterrows():
        czy_nowy = str(row.get('Ostatnia_Zmiana', "")) > st.session_state.last_login
        c_class = "project-container new-project" if czy_nowy else "project-container"
        b_class = get_badge(row['Etap'])
        
        d_i = "📁" if pd.notnull(row.get('Link_Drive')) and "http" in str(row.get('Link_Drive')) else ""
        m_i = "📍" if pd.notnull(row.get('Link_Mapa')) and "http" in str(row.get('Link_Mapa')) else ""

        # Główny kontener karty (HTML)
        st.markdown(f"""
            <div class="{c_class}">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="flex: 4;">
                        <div class="proj-name">{row['Nazwa']} {d_i}{m_i}</div>
                        <div class="proj-info">Inwestor: {row['Inwestor']}</div>
                    </div>
                    <div style="flex: 2;">
                        <div class="proj-label">Prowadzący</div>
                        <div class="proj-value">{row.get('Pracownik', '-')}</div>
                    </div>
                    <div style="flex: 1.5; text-align: right;">
                        <span class="badge {b_class}">{row['Etap']}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Przezroczysty przycisk nałożony na całą kartę
        if st.button("Otwórz", key=f"pbtn_{i}"):
            st.session_state.selected_project = i
            st.rerun()
