"""
Home page of my AI/ML cohort assignments app.
Shows one card per assignment with a link to open it.
"""
import streamlit as st

st.title("📚 AI/ML Cohort Assignments")
st.write("By **Saavan**. Choose an assignment below or use the menu at the top.")
st.divider()

# One entry per assignment: (page file, title, short description)
# To add a new assignment, just add one more line here.
ASSIGNMENTS = [
    ("app_pages/food_waste.py",
     "🥗 Smart Food-Waste Management System",
     "Python Fundamentals: inventory tracking, expiry monitoring, input validation and exception handling."),
]

for page_file, title, description in ASSIGNMENTS:
    with st.container(border=True):          # draws a card around each assignment
        st.subheader(title)
        st.write(description)
        st.page_link(page_file, label="Open app →")
