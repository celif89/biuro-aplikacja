import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Manager Biura PRO", layout="wide")

st.markdown("""
    <style>
    /* Zmniejszenie odstępów między elementami */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stButton>button { width: 100%; border-radius: 5px; }
    /* Optymalizacja tabeli na mobile */
    [data-testid="column"] { min-width: 100px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600) # Dane zostają w pamięci serwera na 10 minut
def pobierz_dane_cached(sheet_name):
    try:
        # Używamy cache, żeby nie pytać Google przy każdym kliknięciu
        return conn.read(worksheet=sheet_name, ttl=0) 
    except:
        return pd.DataFrame()

# Funkcja do czyszczenia cache po zapisie (żeby od razu widzieć zmiany)
def wyczysc_cache():
    st.cache_data.clear()

def zapisz_log(uzytkownik, projekt, akcja):
    logs_df = pobierz_dane("Logi")
    nowy_log = pd.DataFrame([{
        "Data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Uzytkownik": uzytkownik,
        "Projekt": projekt,
        "Akcja": akcja
    }])
    updated_logs = pd.concat([logs_df, nowy_log], ignore_index=True)
    conn.update(worksheet="Logi", data=updated_logs)

def aktualizuj_czas_logowania(uzytkownik):
    users_df = pobierz_dane("Uzytkownicy")
    teraz = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not users_df.empty and uzytkownik in users_df['Uzytkownik'].values:
        users_df.loc[users_df['Uzytkownik'] == uzytkownik, 'OstatnieLogowanie'] = teraz
    else:
        new_user = pd.DataFrame([{"Uzytkownik": uzytkownik, "OstatnieLogowanie": teraz}])
        users_df = pd.concat([users_df, new_user], ignore_index=True)
    conn.update(worksheet="Uzytkownicy", data=users_df)

# --- LOGOWANIE ---
if "password_correct" not in st.session_state:
    st.title("🔐 Logowanie do Systemu Biura")
    uzytkownicy = ["Sebastian", "Olek"] # Dodaj swoich
    user_name = st.selectbox("Wybierz siebie", uzytkownicy)
    password = st.text_input("Hasło", type="password")
    
    if st.button("Zaloguj"):
        if password == "biuro":
            users_df = pobierz_dane("Uzytkownicy")
            last_time = "2000-01-01 00:00:00"
            if not users_df.empty and user_name in users_df['Uzytkownik'].values:
                last_time = users_df.loc[users_df['Uzytkownik'] == user_name, 'OstatnieLogowanie'].values[0]
            
            st.session_state["last_login"] = last_time
            st.session_state["user_name"] = user_name
            st.session_state["password_correct"] = True
            aktualizuj_czas_logowania(user_name)
            st.rerun()
        else:
            st.error("Błędne hasło")
    st.stop()

# --- JEŚLI ZALOGOWANO ---
df = pobierz_dane("Projekty") # <--- UPEWNIJ SIĘ ŻE TAK SIĘ NAZYWA ZAKŁADKA

if "selected_project" not in st.session_state:
    st.session_state.selected_project = None

# --- PANEL BOCZNY (Sidebar) ---
with st.sidebar:
    st.title(f"👤 {st.session_state.user_name}")
    if st.button("🏠 Lista Główna"):
        st.session_state.selected_project = None
        st.rerun()
    
    st.divider()
    
    # FORMULARZ DODAWANIA
    with st.form("dodaj_projekt"):
        st.subheader("➕ Nowy Projekt")
        n_nazwa = st.text_input("Nazwa")
        n_inwestor = st.text_input("Inwestor")
        n_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"])
        n_termin = st.date_input("Termin")
        n_pracownik = st.text_input("Pracownik")
        
        if st.form_submit_button("Dodaj do bazy"):
            if n_nazwa:
                new_row = pd.DataFrame([{
                    "Nazwa": n_nazwa, "Inwestor": n_inwestor, "Etap": n_etap, 
                    "Termin": str(n_termin), "Pracownik": n_pracownik, "Notatki": ""
                }])
                df_updated = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Projekty", data=df_updated)
                zapisz_log(st.session_state.user_name, n_nazwa, "Dodanie nowego projektu")
                st.success("Dodano!")
                st.rerun()

    st.divider()
    if st.button("🚪 Wyloguj"):
        del st.session_state["password_correct"]
        st.rerun()

# --- WIDOK 1: SZCZEGÓŁY ---
if st.session_state.selected_project is not None:
    idx = st.session_state.selected_project
    row = df.iloc[idx]
    
    st.header(f"📂 Projekt: {row['Nazwa']}")
    
    with st.form("edycja_szczegoly"):
        col1, col2 = st.columns(2)
        with col1:
            e_inwestor = st.text_input("Inwestor", row['Inwestor'])
            e_pracownik = st.text_input("Pracownik", row['Pracownik'])
        with col2:
            e_etap = st.selectbox("Etap", ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"], 
                                 index=["Koncepcja", "PNB", "Wykonawczy", "Nadzór"].index(row['Etap']) if row['Etap'] in ["Koncepcja", "PNB", "Wykonawczy", "Nadzór"] else 0)
        
        e_notatki = st.text_area("Szczegółowe ustalenia", str(row['Notatki']) if 'Notatki' in row else "")
        
        if st.form_submit_button("💾 Zapisz zmiany"):
            teraz = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.at[idx, 'Inwestor'] = e_inwestor
            df.at[idx, 'Pracownik'] = e_pracownik
            df.at[idx, 'Etap'] = e_etap
            df.at[idx, 'Notatki'] = e_notatki
            df.at[idx, 'Ostatnia_Zmiana'] = teraz # <--- TO ZAPISUJE CZAS ZMIANY
            
            conn.update(worksheet="Projekty", data=df)
            zapisz_log(st.session_state.user_name, row['Nazwa'], "Edycja szczegółów")
            st.success("Zapisano!")
            st.session_state.selected_project = None
            wyczysc_cache() # <--- TO JEST KLUCZOWE
            st.rerun()

# --- WIDOK 2: LISTA GŁÓWNA ---
else:
    st.title("🏗️ System Zarządzania Projektami")
    
    # POWIADOMIENIA
    logs_df = pobierz_dane("Logi")
    if not logs_df.empty:
        nowe = logs_df[(logs_df['Data'] > st.session_state.last_login) & (logs_df['Uzytkownik'] != st.session_state.user_name)]
        if not nowe.empty:
            with st.expander(f"🔔 Masz {len(nowe)} nowe zmiany od ostatniej wizyty!", expanded=True):
                for _, log in nowe.sort_values(by="Data", ascending=False).iterrows():
                    st.info(f"**{log['Uzytkownik']}** -> {log['Projekt']} ({log['Akcja']} - {log['Data']})")

    if not df.empty:
            st.write("---")
            for i, row in df.iterrows():
                # Sprawdzamy czy zmiana jest nowa i nie zrobiona przez nas
                czy_nowe = False
                if 'Ostatnia_Zmiana' in row and pd.notnull(row['Ostatnia_Zmiana']):
                    if str(row['Ostatnia_Zmiana']) > st.session_state.last_login:
                        # Opcjonalnie: nie koloruj, jeśli to TY sam dokonałeś tej zmiany przed chwilą
                        czy_nowe = True

                # Kontener z kolorem tła
                # Jeśli zmiana jest nowa, używamy jasnej zieleni
                bg_color = "#d4edda" if czy_nowe else "transparent"
                border_color = "#28a745" if czy_nowe else "#eeeeee"
                
                # Renderowanie wiersza wewnątrz ramki z kolorem
                with st.container():
                    st.markdown(f"""
                        <div style="background-color:{bg_color}; border: 1px solid {border_color}; border-radius: 5px; padding: 10px; margin-bottom: 5px;">
                        """, unsafe_allow_html=True)
                    
                    c1, c2, c3, c4 = st.columns([1, 4, 3, 2])
                    with c1:
                        if st.button("👁️", key=f"v_{i}"):
                            st.session_state.selected_project = i
                            st.rerun()
                    with c2:
                        # Jeśli nowe, dodajemy ikonkę gwiazdki
                        prefix = "🟢 " if czy_nowe else ""
                        st.write(f"{prefix}**{row['Nazwa']}**")
                    c3.write(row['Inwestor'])
                    c4.write(row['Etap'])
                    
                    st.markdown("</div>", unsafe_allow_html=True)
