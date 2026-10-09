"""
============================================================
AI TRAVEL PLANNER APPLICATION  (Wrench Wise - Task 1)
============================================================
Author : Saavan
Module : Python Decision Making and Iteration Constructs

No real AI / LLM is used. "AI" here means rule-based decisions
made with if, if-else, if-elif-else and for loops.
============================================================
"""

# ---- Page info (read by registry.py to build the menu & README) ----
TITLE = "AI Travel Planner Application"
NAV_TITLE = "Travel Planner"
URL_PATH = "travel-planner"
ICON = "✈️"
DESCRIPTION = "Plans a trip using budget, travel type and interests with if-elif-else and for loops."
ORDER = 2

import streamlit as st

st.title("✈️ AI Travel Planner")
st.caption("Wrench Wise · Task 1 · Python Decision Making and Iteration Constructs")
st.write("Enter your trip details to get a personalised travel plan.")

# -----------------------------------------------------------------
# STEP 1 : Collect user inputs
# -----------------------------------------------------------------
# Destination -> String
destination = st.text_input("Destination", placeholder="e.g. Goa")

# Travel Date -> String (PDF says String, so I used text_input instead
# of a date picker. This also lets me test the "not empty" validation.)
travel_date = st.text_input("Travel Date", placeholder="e.g. 25-Dec-2026")

# Budget -> Integer (min_value=0 stops negative numbers)
budget = st.number_input("Budget (₹)", min_value=0, value=45000, step=1000)

# Travel Type -> String (only 4 options allowed, so a dropdown)
travel_type = st.selectbox("Travel Type", ["Solo", "Family", "Couple", "Business"])

# Interests -> List (multiselect gives back a Python list)
interests = st.multiselect(
    "Interests",
    ["Beach", "Nature", "Adventure", "Culture", "Food", "Shopping"],
)

# Everything below runs only when the button is clicked
if st.button("Plan My Trip"):

    # -------------------------------------------------------------
    # STEP 2 : Input validation (simple if statements)
    # -------------------------------------------------------------
    # I assume inputs are valid first. If any check fails,
    # I show a warning and set is_valid to False.
    is_valid = True

    # .strip() removes spaces, so "   " also counts as empty
    if destination.strip() == "":
        st.warning("⚠️ Destination should not be empty.")
        is_valid = False

    if travel_date.strip() == "":
        st.warning("⚠️ Travel Date should not be empty.")
        is_valid = False

    if len(interests) == 0:
        st.warning("⚠️ Please select at least one interest.")
        is_valid = False

    # Process flow: Validate Inputs? -> Yes = continue, No = show error
    if is_valid:

        # ---------------------------------------------------------
        # STEP 3 : Budget classification (if-elif-else)
        # ---------------------------------------------------------
        # Python checks top to bottom and stops at the first True one.
        if budget < 10000:
            budget_category = "Low Budget"
        elif budget <= 30000:
            budget_category = "Medium Budget"
        elif budget <= 60000:
            budget_category = "Premium Budget"
        else:
            budget_category = "Luxury Budget"

        # ---------------------------------------------------------
        # STEP 4 : Travel type recommendation (if-elif-else)
        # ---------------------------------------------------------
        if travel_type == "Solo":
            recommendation = "Backpacking & Exploration"
        elif travel_type == "Family":
            recommendation = "Family-Friendly Resort Package"
        elif travel_type == "Couple":
            recommendation = "Romantic Getaway Packages"
        else:
            # Only "Business" is left at this point
            recommendation = "Corporate Hotels & Meeting Facilities"

        # ---------------------------------------------------------
        # STEP 7 : Travel readiness score
        # ---------------------------------------------------------
        # Budget > 30,000 -> +25 | Family/Couple -> +25
        # Each interest -> +15   | Maximum = 100
        score = 0

        if budget > 30000:
            score = score + 25

        if travel_type == "Family" or travel_type == "Couple":
            score = score + 25

        # for loop: add 15 points for every selected interest
        for interest in interests:
            score = score + 15

        # Never go above 100
        if score > 100:
            score = 100

        # ---------------------------------------------------------
        # Display results (Travel Summary)
        # ---------------------------------------------------------
        st.success("✅ Your travel plan is ready!")
        st.subheader("📋 Travel Summary")

        st.write(f"**Destination :** {destination.strip()}")
        st.write(f"**Travel Date :** {travel_date.strip()}")
        st.write(f"**Budget Category :** {budget_category}")
        st.write(f"**Recommendation :** {recommendation}")

        # ---------------------------------------------------------
        # STEP 5 : Display interests using a for loop
        # ---------------------------------------------------------
        st.write("**Selected Interests:**")
        for interest in interests:
            st.write(f"• {interest}")

        # ---------------------------------------------------------
        # STEP 6 : Travel checklist using a for loop
        # ---------------------------------------------------------
        checklist = [
            "Passport / ID",
            "Flight Tickets",
            "Hotel Booking Confirmation",
            "Mobile Charger",
            "Medicines",
        ]

        st.write("**Travel Checklist:**")
        for item in checklist:
            st.write(f"☑️ {item}")

        # Score as text + a progress bar (0 to 100)
        st.subheader(f"🎯 Travel Readiness Score : {score}/100")
        st.progress(score)
