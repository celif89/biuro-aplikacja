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
    .progress-table td { padding: 8px; border-bottom: 1px solid #eee; }
    
    /* Styl dla listy zadań */
    .task-done { text-decoration: line-through; color: #999; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def pobierz_dane(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl=0)
    except: return pd.DataFrame()

def odswiez_baze(): st.cache_data.clear()

# --- 3. LOGOWANIE ---
if "password_correct" not in st.session_state:
    st.title("🔐 Logowanie")
    user_name = st.selectbox("Użytkownik", ["Adam", "Ewa"])
    if st.button("Zaloguj"):
        st.session_state.update({"user_name": user_name, "password_correct": True, "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        st.rerun()
    st.stop()

# --- 4. GŁÓWNA APLIKACJA ---
df = pobierz_dane("Projekty")
if "selected_project" not in st.session_state: st.session_state.selected_project = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("📁 Menu")
    if st.button("🏠 Lista Główna", use_container_width=True):
        st.session_state.selected_project = None
        st.rerun()
    if st.button("🔄 Odśwież", use_container_width=True):
        odswiez_baze()
        st.rerun()
    st.divider()
    with st.expander("➕ Nowy Projekt"):
        with st.form("nowy_p"):
            n_nazwa = st.text_input("Nazwa")
            n_inw = st.text_input("Inwestor")
            if st.form_submit_button("Dodaj"):
                if n_nazwa:
                    new = pd.DataFrame([{"Nazwa": n_nazwa, "Inwestor": n_inw, "Etap": "Koncepcja", "Ostatnia_Zmiana": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                    conn.update(worksheet="Projekty", data=pd.concat([df, new], ignore_index=True))
                    odswiez_baze()
                    st.rerun()

# --- WIDOK SZCZEGÓŁÓW ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    st.title(f"📂 {row['Nazwa']}")

    tab1, tab2, tab3 = st.tabs(["📋 Metryka i Zadania", "📝 Dziennik", "⚙️ Ustawienia"])

    with tab1:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📌 Metryka Projektu")
            with st.form("metryka_form"):
                m_text = st.text_area("Szczegóły umowy/zakresu:", value=str(row.get('Metryka', "")) if pd.notnull(row.get('Metryka')) else "", height=300)
                if st.form_submit_button("Zapisz Metrykę"):
                    df.at[idx, 'Metryka'] = m_text
                    conn.update(worksheet="Projekty", data=df)
                    odswiez_baze()
                    st.success("Zapisano!")

        with col_right:
            st.subheader("✅ Lista Zadań (To-Do)")
            
            # Pobieranie i parsowanie zadań z bazy
            zadania_raw = str(row.get('Lista_Zadań', ""))
            lista_zadan = []
            if zadania_raw and zadania_raw != "nan" and zadania_raw != "":
                # Format w bazie: Zadanie1|0||Zadanie2|1 (0=do zrobienia, 1=zrobione)
                lista_zadan = [z.split("|") for z in zadania_raw.split("||") if "|" in z]

            # Wyświetlanie checkboxów
            zmiana_statusu = False
            nowa_lista_str = []
            
            for i, z in enumerate(lista_zadan):
                text, status = z[0], z[1]
                # Checkbox
                checked = st.checkbox(text, value=(status == "1"), key=f"task_{i}")
                
                # Jeśli użytkownik kliknął (zmiana statusu)
                nowy_status = "1" if checked else "0"
                if nowy_status != status:
                    zmiana_statusu = True
                nowa_lista_str.append(f"{text}|{nowy_status}")

            # Zapisywanie zmian statusu (automatyczne po kliknięciu)
            if zmiana_statusu:
                df.at[idx, 'Lista_Zadań'] = "||".join(nowa_lista_str)
                conn.update(worksheet="Projekty", data=df)
                odswiez_baze()
                st.rerun()

            st.divider()
            # Dodawanie nowego zadania
            with st.form("new_task_form", clear_on_submit=True):
                new_t = st.text_input("Dodaj nowe zadanie:")
                if st.form_submit_button("➕ Dodaj"):
                    if new_t:
                        entry = f"{new_t}|0"
                        df.at[idx, 'Lista_Zadań'] = entry if not zadania_raw or zadania_raw=="nan" else zadania_raw + "||" + entry
                        conn.update(worksheet="Projekty", data=df)
                        odswiez_baze()
                        st.rerun()
            
            if st.button("🗑️ Wyczyść ukończone"):
                lista_zadan = [f"{z[0]}|{z[1]}" for z in lista_zadan if z[1] == "0"]
                df.at[idx, 'Lista_Zadań'] = "||".join(lista_zadan)
                conn.update(worksheet="Projekty", data=df)
                odswiez_baze()
                st.rerun()

    # --- TAB 2: DZIENNIK (SKRÓCONY) ---
    with tab2:
        st.subheader("Historia działań")
        historia = str(row.get('Notatki', ""))
        if historia and historia != "nan":
            for wpis in reversed(historia.split("||")):
                if "|" in wpis:
                    cz = wpis.split("|")
                    st.info(f"**{cz[0]}** - {cz[1]}: {cz[2]}")
        
        with st.form("dziennik_form"):
            n_wpis = st.text_input("Co zrobiono?")
            if st.form_submit_button("Dodaj wpis"):
                d = datetime.datetime.now().strftime("%d.%m.%Y")
                w = f"{d}|{st.session_state.user_name}|{n_wpis}"
                df.at[idx, 'Notatki'] = w if not historia or historia=="nan" else historia + "||" + w
                conn.update(worksheet="Projekty", data=df)
                odswiez_baze()
                st.rerun()

    # --- TAB 3: USTAWIENIA ---
    with tab3:
        with st.form("settings"):
            e_inw = st.text_input("Inwestor", row['Inwestor'])
            e_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"])
            e_drive = st.text_input("Link Drive", row.get('Link_Drive', ""))
            if st.form_submit_button("Zapisz"):
                df.at[idx, 'Inwestor'], df.at[idx, 'Etap'], df.at[idx, 'Link_Drive'] = e_inw, e_etap, e_drive
                conn.update(worksheet="Projekty", data=df)
                odswiez_baze()
                st.rerun()

# --- WIDOK LISTY ---
else:
    st.subheader("🏗️ Lista Projektów")
    for i, row in df.iterrows():
        st.markdown('<div class="project-row">', unsafe_allow_html=True)
        c = st.columns([0.5, 5, 3, 2])
        with c[0]:
            if st.button("👁️", key=f"list_{i}"):
                st.session_state.selected_project = i
                st.rerun()
        c[1].markdown(f"**{row['Nazwa']}**")
        c[2].write(row['Inwestor'])
        with c[3]: st.markdown(f'<div class="etap-badge">{row["Etap"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
