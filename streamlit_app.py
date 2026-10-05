"""
Hub for all my AI/ML cohort assignments.
The menu is built automatically from registry.py, so I never edit this file
when adding a new assignment.
"""
import streamlit as st
from registry import discover_assignments

st.set_page_config(page_title="AI/ML Cohort Assignments", page_icon="📚", layout="wide")

# Home page first, then every assignment found in app_pages/
pages = [st.Page("app_pages/home.py", title="Home", icon="🏠", default=True)]
for a in discover_assignments():
    pages.append(st.Page(a["file"], title=a["nav_title"], icon=a["icon"], url_path=a["url_path"]))

st.navigation(pages, position="top").run()
