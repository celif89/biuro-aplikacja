import datetime
import uuid

import streamlit as st

st.set_page_config(page_title="Biuro Projektowe", layout="wide")

if "projects" not in st.session_state:
    st.session_state.projects = []


def new_project(name: str, client: str, due_date, notes: str):
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "client": client,
        "status": "Planowanie",
        "priority": "Średni",
        "due_date": due_date,
        "notes": notes,
        "tasks": [],
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def add_task(project_id: str, task_name: str):
    for project in st.session_state.projects:
        if project["id"] == project_id:
            project["tasks"].append({"name": task_name, "done": False})
            return


def update_task(project_id: str, task_index: int, done: bool):
    for project in st.session_state.projects:
        if project["id"] == project_id and task_index < len(project["tasks"]):
            project["tasks"][task_index]["done"] = done
            return


st.title("📁 Panel zarządzania projektami")
st.caption("Wersja startowa: prosty podgląd projektów, statusów i zadań.")

col_form, col_dashboard = st.columns([2, 3])

with col_form:
    st.subheader("➕ Dodaj projekt")
    with st.form("project_form", clear_on_submit=True):
        p_name = st.text_input("Nazwa projektu")
        p_client = st.text_input("Inwestor / klient")
        p_due_date = st.date_input("Termin", value=datetime.date.today() + datetime.timedelta(days=14))
        p_notes = st.text_area("Opis / zakres", height=100)

        if st.form_submit_button("Zapisz projekt"):
            if not p_name.strip():
                st.warning("Podaj nazwę projektu.")
            else:
                st.session_state.projects.append(new_project(p_name.strip(), p_client.strip(), p_due_date, p_notes.strip()))
                st.success("Projekt został dodany.")
                st.rerun()

with col_dashboard:
    st.subheader("📊 Podsumowanie")
    total = len(st.session_state.projects)
    in_progress = len([p for p in st.session_state.projects if p["status"] == "W toku"])
    done = len([p for p in st.session_state.projects if p["status"] == "Zakończony"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Wszystkie", total)
    m2.metric("W toku", in_progress)
    m3.metric("Zakończone", done)

st.divider()
st.subheader("🏗️ Lista projektów")

if not st.session_state.projects:
    st.info("Brak projektów. Dodaj pierwszy projekt w formularzu powyżej.")
else:
    for project in st.session_state.projects:
        completed_tasks = len([t for t in project["tasks"] if t["done"]])
        total_tasks = len(project["tasks"])

        with st.expander(f"{project['name']} • {project['client'] or 'Brak klienta'}"):
            col_a, col_b, col_c = st.columns([2, 1, 1])

            with col_a:
                st.write(f"**Utworzono:** {project['created_at']}")
                st.write(f"**Termin:** {project['due_date']}")

            with col_b:
                project["status"] = st.selectbox(
                    "Status",
                    ["Planowanie", "W toku", "Wstrzymany", "Zakończony"],
                    index=["Planowanie", "W toku", "Wstrzymany", "Zakończony"].index(project["status"]),
                    key=f"status_{project['id']}",
                )

            with col_c:
                project["priority"] = st.selectbox(
                    "Priorytet",
                    ["Niski", "Średni", "Wysoki"],
                    index=["Niski", "Średni", "Wysoki"].index(project["priority"]),
                    key=f"priority_{project['id']}",
                )

            if project["notes"]:
                st.write(f"**Opis:** {project['notes']}")

            st.write(f"**Zadania:** {completed_tasks}/{total_tasks} ukończonych")

            for idx, task in enumerate(project["tasks"]):
                checked = st.checkbox(task["name"], value=task["done"], key=f"task_{project['id']}_{idx}")
                if checked != task["done"]:
                    update_task(project["id"], idx, checked)
                    st.rerun()

            with st.form(f"task_form_{project['id']}", clear_on_submit=True):
                task_name = st.text_input("Nowe zadanie", key=f"task_input_{project['id']}")
                if st.form_submit_button("Dodaj zadanie"):
                    if task_name.strip():
                        add_task(project["id"], task_name.strip())
                        st.rerun()

            if st.button("🗑️ Usuń projekt", key=f"delete_{project['id']}"):
                st.session_state.projects = [p for p in st.session_state.projects if p["id"] != project["id"]]
                st.rerun()
