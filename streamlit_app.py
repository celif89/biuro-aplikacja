import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Manager Biura", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

st.title("🏗️ System Zarządzania Projektami")

# Wyświetlanie i edycja
edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

if st.button("💾 Zapisz zmiany"):
    conn.update(data=edited_df)
    st.success("Zapisano pomyślnie!")
    st.rerun()
