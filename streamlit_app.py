import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. KONFIGURACJA I STYLE (NOWY DESIGN) ---
st.set_page_config(page_title="ProManager 2.0", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    /* Import czcionki */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc; /* Bardzo jasny błękit/szary */
    }

    /* Ograniczenie szerokości kontenera */
    .main > div {
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Stylizacja Karty Projektu */
    .project-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 15px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border-left: 5px solid #e2e8f0;
    }
    
    .project-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #3b82f6; /* Niebieski przy hoverze */
    }

    .project-card-new {
        border-left: 5px solid #10b981 !important; /* Zielony dla nowych */
        background-color: #f0fdf4;
    }

    /* Stylizacja Tekstów */
    .proj-title {
        color: #1e293b;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 5px;
    }
    
    .proj-subtitle {
        color: #64748b;
        font-size: 0.85rem;
    }

    /* Badge Etapu */
    .badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-koncepcja { background-color: #dbeafe; color: #1e40af; }
    .badge-pnb { background-color: #fef3c7; color: #92400e; }
    .badge-wykonawczy { background-color: #dcfce7; color: #166534; }
    .badge-nadzor { background-color: #f3e8ff; color: #6b21a8; }

    /* Ukrycie domyślnych ramek przycisków w liście */
    div[data-testid="column"] button {
        border: none !important;
        background-color: #f1f5f9 !important;
        color: #475569 !important;
        border-radius: 8px !important;
        transition: 0.3s;
    }
    div[data-testid="column"] button:hover {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNKCJE POMOCNICZE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl=0)
    except: return pd.DataFrame()

def odswiez(): st.cache_data.clear()

def get_badge_class(etap):
    etap = str(etap).lower()
    if 'koncepcja' in etap: return 'badge-koncepcja'
    if 'pnb' in etap: return 'badge-pnb'
    if 'wykonawczy' in etap: return 'badge-wykonawczy'
    if 'nadzor' in etap: return 'badge-nadzor'
    return ''

# --- 3. LOGOWANIE ---
if "password_correct" not in st.session_state:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🏗️ ProManager Login")
        u = st.selectbox("Użytkownik", ["Adam", "Ewa", "Marek", "Pracownik1"])
        p = st.text_input("Hasło", type="password")
        if st.button("Zaloguj się"):
            if p == "TwojeTajneHaslo123":
                st.session_state.update({"user_name": u, "password_correct": True, "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                st.rerun()
    st.stop()

# --- 4. GŁÓWNA APLIKACJA ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_name}")
    st.divider()
    if st.button("🏠 Lista Główna", use_container_width=True):
        st.session_state.selected_project = None
        st.rerun()
    if st.button("🔄 Odśwież dane", use_container_width=True):
        odswiez(); st.rerun()
    
    st.divider()
    with st.expander("➕ Nowy Projekt"):
        with st.form("new_p"):
            n_nazwa = st.text_input("Nazwa")
            n_inw = st.text_input("Inwestor")
            if st.form_submit_button("Dodaj do bazy"):
                if n_nazwa:
                    new = pd.DataFrame([{"Nazwa": n_nazwa, "Inwestor": n_inw, "Etap": "Koncepcja", "Ostatnia_Zmiana": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                    conn.update(worksheet="Projekty", data=pd.concat([df, new], ignore_index=True))
                    odswiez(); st.rerun()
    
    if st.button("🚪 Wyloguj", use_container_width=True):
        del st.session_state["password_correct"]
        st.rerun()

# --- WIDOK SZCZEGÓŁÓW ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    
    st.button("← Wróć do listy", on_click=lambda: st.session_state.update({"selected_project": None}))
    st.title(f"📂 {row['Nazwa']}")
    
    tab1, tab2, tab3 = st.tabs(["📋 Metryka i To-Do", "📝 Dziennik Robót", "⚙️ Pliki i Ustawienia"])
    
    # (Tutaj logika Tabów pozostaje bez zmian funkcjonalnych, jedynie UI Streamlit automatycznie je ostyluje)
    with tab1:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.subheader("📌 Metryka")
            m_text = st.text_area("Informacje stałe:", value=str(row.get('Metryka', "")), height=200)
            if st.button("Zapisz Metrykę"):
                df.at[idx, 'Metryka'] = m_text
                conn.update(worksheet="Projekty", data=df); odswiez(); st.success("Zapisano!")
        
        with col_m2:
            st.subheader("✅ Zadania")
            # Logika checkboxów (jak w poprzedniej wersji)
            # ...
            st.info("Zarządzaj listą zadań poniżej.")

# --- WIDOK LISTY ---
else:
    st.title("🏗️ Aktywne Projekty")
    st.write("Zarządzaj swoimi projektami i śledź postępy prac.")
    
    # Nagłówki tabeli (opcjonalne przy kartach, ale dodajmy dla porządku)
    st.markdown("""
        <div style="display: flex; padding: 0px 20px; color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 10px;">
            <div style="flex: 0.5;">Otwórz</div>
            <div style="flex: 3.5;">Projekt i Inwestor</div>
            <div style="flex: 2;">Prowadzący</div>
            <div style="flex: 1.5; text-align: right;">Etap</div>
        </div>
    """, unsafe_allow_html=True)

    for i, row in df.iterrows():
        czy_nowy = str(row.get('Ostatnia_Zmiana', "")) > st.session_state.last_login
        card_class = "project-card project-card-new" if czy_nowy else "project-card"
        badge_class = get_badge_class(row['Etap'])
        
        # Ikony dokumentacji
        d_i = "📁" if pd.notnull(row.get('Link_Drive')) and "http" in str(row.get('Link_Drive')) else ""
        m_i = "📍" if pd.notnull(row.get('Link_Mapa')) and "http" in str(row.get('Link_Mapa')) else ""

        st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; align-items: center;">
                    <div style="flex: 0.5;" id="btn_space_{i}"></div>
                    <div style="flex: 3.5;">
                        <div class="proj-title">{row['Nazwa']} {d_i}{m_i}</div>
                        <div class="proj-subtitle">Inwestor: {row['Inwestor']}</div>
                    </div>
                    <div style="flex: 2;">
                        <div class="proj-subtitle">Prowadzący:</div>
                        <div style="color: #1e293b; font-weight: 600;">{row.get('Pracownik', '-')}</div>
                    </div>
                    <div style="flex: 1.5; text-align: right;">
                        <span class="badge {badge_class}">{row['Etap']}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Streamlitowy przycisk "wstrzyknięty" w pusty kontener nad kartą (hack dla pozycjonowania)
        # Przycisk umieszczamy w kolumnach poniżej karty dla funkcjonalności
        with st.container():
            cols = st.columns([0.5, 7, 1])
            with cols[0]:
                if st.button("👁️", key=f"btn_{i}"):
                    st.session_state.selected_project = i
                    st.rerun()
