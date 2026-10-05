"""
Hub for all my AI/ML cohort assignments.
This is the ONLY file Streamlit Cloud runs. Each assignment is one page.
"""
import streamlit as st

# Page settings for the whole app (set once here, not in the page files)
st.set_page_config(page_title="AI/ML Cohort Assignments", page_icon="📚", layout="wide")

# Each assignment is one page. url_path gives it its own direct link.
pages = [
    st.Page("app_pages/home.py", title="Home", icon="🏠", default=True),
    st.Page("app_pages/food_waste.py", title="Food-Waste Manager", icon="🥗", url_path="food-waste"),
]

# Show the menu at the top so it doesn't clash with each app's own sidebar
st.navigation(pages, position="top").run()
