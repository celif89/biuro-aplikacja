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
    .date-col { color: #666; font-weight: bold; width: 100px; }
    .user-col { color: #01579b; width: 120px; }
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
    st.title("🔐 Logowanie")
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

# SIDEBAR
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user_name}**")
    if st.button("🏠 Lista Główna"):
        st.session_state.selected_project = None
        st.rerun()
    if st.button("🔄 Odśwież"):
        odswiez_baze()
        st.rerun()

# --- WIDOK SZCZEGÓŁÓW Z DZIENNIKIEM POSTĘPÓW ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    st.header(f"📂 {row['Nazwa']}")

    # Kolumny z linkami
    c1, c2 = st.columns(2)
    with c1: 
        if pd.notnull(row.get('Link_Drive')): st.link_button("🚀 Dokumentacja Drive", str(row['Link_Drive']), type="primary")
    with c2:
        if pd.notnull(row.get('Link_Mapa')): st.link_button("📍 Lokalizacja Maps", str(row['Link_Mapa']))

    st.divider()

    # --- SEKCJA DZIENNIKA POSTĘPÓW (MINI TABELKA) ---
    st.subheader("📝 Dziennik Postępów Robót")
    
    # Wyświetlanie historii z komórki 'Notatki'
    historia = str(row.get('Notatki', ""))
    if historia and historia != "nan":
        html_table = '<table class="progress-table"><tr><th>Data</th><th>Pracownik</th><th>Opis prac</th></tr>'
        wpisy = historia.split("||") # Używamy || jako separatora wpisów
        for wpis in reversed(wpisy): # Najnowsze na górze
            if "|" in wpis:
                czesci = wpis.split("|")
                if len(czesci) >= 3:
                    html_table += f'<tr><td class="date-col">{czesci[0]}</td><td class="user-col">{czesci[1]}</td><td>{czesci[2]}</td></tr>'
        html_table += '</table>'
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("Brak wpisów w dzienniku.")

    # Formularz dodawania nowego wpisu
    with st.expander("➕ Dodaj nowy postęp prac", expanded=True):
        with st.form("nowy_wpis"):
            nowy_opis = st.text_area("Co zostało dziś zrobione?", placeholder="Np. Wysłano projekt do uzgodnień...")
            col_save1, col_save2 = st.columns([1, 1])
            
            # Dodatkowe pola edycji parametrów projektu
            with col_save1:
                e_etap = st.selectbox("Zmień etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"], 
                                     index=["Koncepcja", "PNB", "Wykonawczy", "Nadzór"].index(row['Etap']) if row['Etap'] in ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"] else 0)
            with col_save2:
                e_pracownik = st.text_input("Osoba prowadząca", row.get('Pracownik', ""))

            if st.form_submit_button("✅ Zapisz postęp i aktualizuj projekt"):
                # Tworzenie nowego wpisu: DATA | UZYTKOWNIK | OPIS
                data_dzis = datetime.datetime.now().strftime("%d.%m.%Y")
                format_wpisu = f"{data_dzis}|{st.session_state.user_name}|{nowy_opis}"
                
                # Łączenie z historią
                stara_historia = str(row.get('Notatki', ""))
                if stara_historia == "nan" or stara_historia == "":
                    nowa_historia = format_wpisu
                else:
                    nowa_historia = stara_historia + "||" + format_wpisu
                
                # Aktualizacja DataFrame
                for col in ['Notatki', 'Etap', 'Pracownik', 'Ostatnia_Zmiana']:
                    df[col] = df[col].astype(str)
                
                df.at[idx, 'Notatki'] = nowa_historia
                df.at[idx, 'Etap'] = e_etap
                df.at[idx, 'Pracownik'] = e_pracownik
                df.at[idx, 'Ostatnia_Zmiana'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                conn.update(worksheet="Projekty", data=df)
                zapisz_log(st.session_state.user_name, row['Nazwa'], f"Dodano wpis: {nowy_opis[:30]}...")
                odswiez_baze()
                st.success("Postęp zapisany!")
                st.rerun()

# --- WIDOK LISTY ---
else:
    st.subheader("🏗️ Lista Projektów")
    h = st.columns([0.5, 4, 3, 2, 1.5])
    h[0].caption("Otwórz"); h[1].caption("Nazwa projektu"); h[2].caption("Inwestor"); h[3].caption("Prowadzący"); h[4].caption("Etap")
    st.divider()

    if not df.empty:
        for i, row in df.iterrows():
            st.markdown('<div class="project-row">', unsafe_allow_html=True)
            cols = st.columns([0.5, 4, 3, 2, 1.5])
            with cols[0]:
                if st.button("👁️", key=f"v_{i}"):
                    st.session_state.selected_project = i
                    st.rerun()
            cols[1].markdown(f"**{row['Nazwa']}**")
            cols[2].markdown(f"<span class='small-text'>{row['Inwestor']}</span>", unsafe_allow_html=True)
            cols[3].markdown(f"<span class='small-text'>{row.get('Pracownik', '-')}</span>", unsafe_allow_html=True)
            with cols[4]: st.markdown(f'<div class="etap-badge">{row["Etap"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
