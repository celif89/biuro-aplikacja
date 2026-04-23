import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Manager Biura PRO", layout="wide")

# --- POŁĄCZENIE Z BAZĄ ---
# Upewnij się, że w Secrets masz poprawny link i klucze!
conn = st.connection("gsheets", type=GSheetsConnection)

def pobierz_dane(sheet_name):
    return conn.read(worksheet=sheet_name, ttl=0)

# --- FUNKCJE SYSTEMOWE ---
def zapisz_log(uzytkownik, projekt, akcja, url):
    try:
        logs_df = pobierz_dane("Logi")
        nowy_log = pd.DataFrame([{
            "Data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Uzytkownik": uzytkownik,
            "Projekt": projekt,
            "Akcja": akcja
        }])
        updated_logs = pd.concat([logs_df, nowy_log], ignore_index=True)
        conn.update(worksheet="Logi", data=updated_logs)
    except Exception as e:
        st.error(f"Błąd logowania zmian: {e}")

def aktualizuj_czas_logowania(uzytkownik):
    users_df = pobierz_dane("Uzytkownicy")
    teraz = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if uzytkownik in users_df['Uzytkownik'].values:
        users_df.loc[users_df['Uzytkownik'] == uzytkownik, 'OstatnieLogowanie'] = teraz
    else:
        new_user = pd.DataFrame([{"Uzytkownik": uzytkownik, "OstatnieLogowanie": teraz}])
        users_df = pd.concat([users_df, new_user], ignore_index=True)
    conn.update(worksheet="Uzytkownicy", data=users_df)

# --- SYSTEM LOGOWANIA ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Logowanie do Systemu Biura")
        user_list = ["Wybierz...", "Adam", "Ewa", "Marek", "Pracownik1"] # Dodaj swoich pracowników
        user_name = st.selectbox("Wybierz użytkownika", user_list)
        password = st.text_input("Hasło", type="password")
        
        if st.button("Zaloguj"):
            if password == "biuro" and user_name != "Wybierz...":
                # Pobieramy datę poprzedniego wejścia ZANIM zaktualizujemy na nową
                users_df = pobierz_dane("Uzytkownicy")
                last_time = users_df.loc[users_df['Uzytkownik'] == user_name, 'OstatnieLogowanie'].values
                st.session_state["last_login"] = last_time[0] if len(last_time) > 0 else "2000-01-01 00:00:00"
                
                st.session_state["password_correct"] = True
                st.session_state["user_name"] = user_name
                aktualizuj_czas_logowania(user_name)
                st.rerun()
            else:
                st.error("Niepoprawne hasło lub nie wybrano użytkownika")
        return False
    return True

# --- GŁÓWNA CZĘŚĆ APLIKACJI ---
if check_password():
    df = pobierz_dane("Sheet1") # Twoja główna zakładka z projektami
    
    if "selected_project" not in st.session_state:
        st.session_state.selected_project = None

    # --- PANEL POWIADOMIEŃ O NOWOŚCIACH ---
    if st.session_state.selected_project is None:
        st.title(f"Witaj, {st.session_state.user_name}! 👋")
        
        try:
            logs_df = pobierz_dane("Logi")
            # Filtrujemy zmiany zrobione przez INNYCH po naszym ostatnim logowaniu
            nowe_zmiany = logs_df[
                (logs_df['Data'] > st.session_state.last_login) & 
                (logs_df['Uzytkownik'] != st.session_state.user_name)
            ]
            
            if not nowe_zmiany.empty:
                with st.expander(f"🔔 Masz {len(nowe_zmiany)} nowych powiadomień!", expanded=True):
                    for _, log in nowe_zmiany.sort_values(by="Data", ascending=False).iterrows():
                        st.info(f"O godzinie **{log['Data']}**, użytkownik **{log['Uzytkownik']}** wykonał: **{log['Akcja']}** w projekcie **{log['Projekt']}**")
        except:
            st.warning("Dodaj arkusz 'Logi', aby widzieć powiadomienia.")

    # --- WIDOK 1: SZCZEGÓŁY PROJEKTU ---
    if st.session_state.selected_project is not None:
        idx = st.session_state.selected_project
        project_data = df.iloc[idx]
        
        if st.button("⬅️ Powrót"):
            st.session_state.selected_project = None
            st.rerun()

        with st.form("edycja_szczegolowa"):
            st.header(f"Edycja: {project_data['Nazwa']}")
            e_pracownik = st.text_input("Osoba odpowiedzialna", project_data['Pracownik'])
            e_notatki = st.text_area("Notatki", str(project_data['Notatki']) if 'Notatki' in project_data else "")

            if st.form_submit_button("💾 Zapisz zmiany"):
                df.at[idx, 'Pracownik'] = e_pracownik
                if 'Notatki' in df.columns:
                    df['Notatki'] = df['Notatki'].astype(str)
                    df.at[idx, 'Notatki'] = e_notatki
                
                conn.update(data=df)
                # ZAPIS LOGU ZMIAN
                zapisz_log(st.session_state.user_name, project_data['Nazwa'], "Zmiana notatek/pracownika", "")
                st.success("Zapisano!")
                st.session_state.selected_project = None
                st.rerun()

    # --- WIDOK 2: LISTA PROJEKTÓW ---
    else:
        st.subheader("Lista projektów")
        for i, row in df.iterrows():
            col1, col2 = st.columns([1, 10])
            with col1:
                if st.button("👁️", key=f"v_{i}"):
                    st.session_state.selected_project = i
                    st.rerun()
            with col2:
                st.write(f"**{row['Nazwa']}** - {row['Inwestor']} (Osoba: {row['Pracownik']})")
            st.divider()

    # Wylogowanie
    if st.sidebar.button("Wyloguj"):
        st.session_state["password_correct"] = False
        st.rerun()
