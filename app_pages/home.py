"""
Home page: shows one card per assignment, built automatically from registry.py.
"""
import streamlit as st
from registry import discover_assignments, REPO_URL

st.title("📚 AI/ML Cohort Assignments")
st.write("By **Saavan**. Choose an assignment below or use the menu at the top.")
st.divider()

assignments = discover_assignments()
if not assignments:
    st.info("No assignments yet.")

for a in assignments:
    with st.container(border=True):                     # one card per assignment
        st.subheader(f"{a['icon']} {a['title']}")
        if a["description"]:
            st.write(a["description"])
        col1, col2 = st.columns([1, 4])
        col1.page_link(a["file"], label="Open app →")
        col2.markdown(f"[View source code]({REPO_URL}/blob/main/{a['source']})")
