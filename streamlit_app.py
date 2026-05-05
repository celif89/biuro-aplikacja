import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA I DESIGN ---
st.set_page_config(page_title="Biuro PRO", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; }
    .main > div { max-width: 1100px; margin-left: auto; margin-right: auto; padding-top: 1.5rem; }

    /* STYL KARTY */
    .project-wrapper {
        position: relative; /* Pozwala na pozycjonowanie przycisku wewnątrz */
        margin-bottom: 12px;
    }

    .project-card {
        background: white;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        padding: 16px 24px;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .project-wrapper:hover .project-card {
        border-color: #3b82f6;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        background: #f9fbff;
    }

    .is-new { border-left: 5px solid #10b981 !important; background: #f0fdf4 !important; }

    /* TYPOGRAFIA */
    .p-title { font-size: 1.05rem; font-weight: 600; color: #0f172a; margin: 0; }
    .p-sub { font-size: 0.85rem; color: #64748b; margin-top: 2px; }
    .p-label { font-size: 0.7rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
    .p-val { font-size: 0.9rem; color: #334155; font-weight: 500; }

    /* STATUSY */
    .badge { font-size: 0.7rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; }
    .b-blue { background: #eff6ff; color: #2563eb; }
    .b-green { background: #f0fdf4; color: #16a34a; }
    .b-orange { background: #fffbeb; color: #d97706; }

    /* MAGICZNY TRIK: PRZEZROCZYSTY PRZYCISK NA CAŁEJ KARCIE */
    .stButton > button {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 10; /* Przycisk jest na wierzchu */
        cursor: pointer;
    }
    .stButton > button:hover, .stButton > button:active, .stButton > button:focus {
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    /* Ukrycie dodatkowego odstępu generowanego przez Streamlit dla przycisków */
    div[data-testid="stVerticalBlock"] > div:has(button) { margin: 0 !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl=0)
    except: return pd.DataFrame()

def odswiez(): st.cache_data.clear()

# --- 3. GŁÓWNA LOGIKA ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# SIDEBAR (dla porządku)
with st.sidebar:
    if st.button("🏠 Lista Główna", use_container_width=True):
        st.session_state.selected_project = None; st.rerun()
    if st.button("🔄 Odśwież Dane", use_container_width=True):
        odswiez(); st.rerun()

# --- WIDOK PROJEKTU ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    st.title(f"📂 {row['Nazwa']}")
    st.write(f"Inwestor: {row['Inwestor']}")
    if st.button("← Powrót"): st.session_state.selected_project = None; st.rerun()
    
# --- LISTA PROJEKTÓW ---
else:
    st.markdown("<h1>🏗️ Aktywne Projekty</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-bottom:25px;'>Wybierz projekt z listy, aby zarządzać zadaniami.</p>", unsafe_allow_html=True)

    for i, row in df.iterrows():
        # Logika nowości i statusów
        czy_nowy = str(row.get('Ostatnia_Zmiana', "")) > st.session_state.get('last_login', "")
        card_style = "project-card is-new" if czy_nowy else "project-card"
        
        # Dobór koloru badge'a
        etap = str(row['Etap']).lower()
        b_style = "b-blue" if "koncepcja" in etap else "b-green" if "wykonawczy" in etap else "b-orange"

        # HTML KARTY
        st.markdown(f"""
            <div class="project-wrapper">
                <div class="{card_style}">
                    <div style="flex: 3;">
                        <div class="p-title">{row['Nazwa']}</div>
                        <div class="p-sub">Inwestor: {row['Inwestor']}</div>
                    </div>
                    <div style="flex: 2;">
                        <div class="p-label">Prowadzący</div>
                        <div class="p-val">{row.get('Pracownik', '-')}</div>
                    </div>
                    <div style="flex: 1; text-align: right;">
                        <span class="badge {b_style}">{row['Etap']}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # PRZYCISK (Niewidzialny, nałożony na div powyżej)
        # Dzięki CSS powyżej, ten button wypełni całe project-wrapper
        if st.button("Open", key=f"p_{i}"):
            st.session_state.selected_project = i
            st.rerun()
