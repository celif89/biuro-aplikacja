import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Biuro PRO", layout="wide")

# CSS - naprawiony i bezpieczny
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main > div { max-width: 1000px; margin: 0 auto; }
    
    /* Ukrywamy standardowy wygląd przycisku, robimy z niego kartę */
    div.stButton > button {
        width: 100%;
        background-color: white !important;
        border: 1px solid #e2e8f0 !important;
        padding: 20px !important;
        border-radius: 12px !important;
        text-align: left !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    
    div.stButton > button:hover {
        border-color: #3b82f6 !important;
        background-color: #f8faff !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }

    /* Styl dla tekstu wewnątrz przycisku */
    .btn-content { color: #1e293b; pointer-events: none; }
    .btn-title { font-size: 1.1rem; font-weight: 600; display: block; margin-bottom: 4px; }
    .btn-desc { font-size: 0.85rem; color: #64748b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DANE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane():
    return conn.read(worksheet="Projekty", ttl=0)

# --- 3. LOGIKA ---
if "selected_project" not in st.session_state:
    st.session_state.selected_project = None

df = pobierz_dane()

# --- WIDOK SZCZEGÓŁÓW ---
if st.session_state.selected_project is not None:
    row = df.iloc[st.session_state.selected_project]
    st.header(f"📂 {row['Nazwa']}")
    if st.button("← Powrót do listy"):
        st.session_state.selected_project = None
        st.rerun()
    
    st.divider()
    st.subheader("Szczegóły projektu")
    st.write(f"**Inwestor:** {row['Inwestor']}")
    st.write(f"**Etap:** {row['Etap']}")
    # Tutaj dodaj swoje zakładki i resztę funkcji...

# --- WIDOK LISTY ---
else:
    st.title("🏗️ Aktywne Projekty")
    st.write("Wybierz projekt, aby zobaczyć szczegóły.")
    
    for i, row in df.iterrows():
        # Przygotowanie tekstu do przycisku
        # Używamy prostego tekstu, bo Streamlit w przyciskach słabo znosi HTML
        tytul = f"{row['Nazwa']}"
        opis = f"Inwestor: {row['Inwestor']}  |  Prowadzący: {row.get('Pracownik', '-')}  |  Etap: {row['Etap']}"
        
        # Cała karta to ten przycisk
        if st.button(f"{tytul}\n{opis}", key=f"p_{i}"):
            st.session_state.selected_project = i
            st.rerun()    /* Styl dla "Nowych" projektów (zielony pasek) */
    /* Streamlit nie pozwala łatwo nadawać klas konkretnym buttonom, 
       więc użyjemy triku z emotką lub po prostu czystego designu */

    /* WEWNĘTRZNA STRUKTURA KARTY (HTML wewnątrz buttona) */
    .c-box {
        padding: 16px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
    }
    .c-title { font-size: 1rem; font-weight: 600; color: #0f172a; }
    .c-sub { font-size: 0.85rem; color: #64748b; font-weight: 400; }
    .c-label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; }
    .c-val { font-size: 0.85rem; color: #334155; font-weight: 500; }
    
    .c-badge {
        font-size: 0.7rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        background: #f1f5f9;
        color: #475569;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE I DANE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl=0)
    except: return pd.DataFrame()

# --- 3. LOGIKA APLIKACJI ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# --- WIDOK SZCZEGÓŁÓW ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    
    st.title(f"📂 {row['Nazwa']}")
    if st.button("← Wróć do listy"):
        st.session_state.selected_project = None
        st.rerun()
    st.divider()
    # Tu reszta Twoich zakładek (Metryka, Zadania itd.)
    st.info("Tutaj zarządzasz szczegółami projektu.")

# --- WIDOK LISTY (KLIKALNE KARTY) ---
else:
    st.markdown("<h1>🏗️ Aktywne Projekty</h1>", unsafe_allow_html=True)
    st.markdown("<p>Kliknij bezpośrednio w kartę projektu, aby go otworzyć.</p>", unsafe_allow_html=True)
    
    for i, row in df.iterrows():
        # Przygotowujemy ikony i status
        d_i = "📁" if pd.notnull(row.get('Link_Drive')) and "http" in str(row.get('Link_Drive')) else ""
        m_i = "📍" if pd.notnull(row.get('Link_Mapa')) and "http" in str(row.get('Link_Mapa')) else ""
        
        # Tworzymy treść karty jako jeden wielki ciąg HTML
        # Button w Streamlit może przyjąć tekst, ale my "oszukamy" system, 
        # wstrzykując tam sformatowany tekst, który ostylowaliśmy w CSS.
        
        button_content = f"""
            {row['Nazwa']} {d_i} {m_i}
            Inwestor: {row['Inwestor']} | Prowadzący: {row.get('Pracownik', '-')} | Status: {row['Etap']}
        """
        
        # Aby uzyskać bogaty wygląd wewnątrz buttona bez błędów Streamlita, 
        # użyjemy standardowego buttona, a CSS zajmie się resztą.
        # UWAGA: Streamlit nie renderuje HTML wewnątrz labela buttona, 
        # dlatego stylizujemy SAM button, by wyglądał jak karta.
        
        label = f"PROJEKT: {row['Nazwa']} \n Inwestor: {row['Inwestor']} | Etap: {row['Etap']}"
        
        if st.button(label, key=f"card_{i}"):
            st.session_state.selected_project = i
            st.rerun()
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
