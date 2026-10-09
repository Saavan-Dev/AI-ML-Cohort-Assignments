"""
============================================================
AI LOAN ELIGIBILITY SYSTEM  (Wrench Wise - Task 2)
============================================================
Author : Saavan
Module : Python Decision Making and Iteration Constructs

No real AI / LLM is used. "AI" here means a rule-based system
built with if, if-else, if-elif-else and for loops.
============================================================
"""

# ---- Page info (read by registry.py to build the menu & README) ----
TITLE = "AI Loan Eligibility System"
NAV_TITLE = "Loan Eligibility"
URL_PATH = "loan-eligibility"
ICON = "🏦"
DESCRIPTION = "Screens loan applications using credit score, salary and existing loans."
ORDER = 3

import streamlit as st

st.title("🏦 AI Loan Eligibility System")
st.caption("Wrench Wise · Task 2 · Python Decision Making and Iteration Constructs")
st.write("Enter customer details to check loan eligibility.")

# -----------------------------------------------------------------
# STEP 1 : Collect user inputs
# -----------------------------------------------------------------
customer_name = st.text_input("Customer Name", placeholder="e.g. Rahul Sharma")

# Salary -> Integer. min_value=0 so I can test the "salary > 0" rule
monthly_salary = st.number_input("Monthly Salary (₹)", min_value=0, value=85000, step=1000)

# Credit Score -> Integer. The box allows 0 to 1000 on purpose,
# so my own validation (300 to 900) can actually be tested.
credit_score = st.number_input("Credit Score", min_value=0, max_value=1000, value=780, step=1)

# Existing Loans -> Integer
existing_loans = st.number_input("Existing Loans", min_value=0, value=1, step=1)

# Documents Submitted -> List
documents = st.multiselect(
    "Documents Submitted",
    ["Aadhaar", "PAN", "Salary Slip", "Bank Statement", "Address Proof"],
)

if st.button("Check Eligibility"):

    # -------------------------------------------------------------
    # STEP 2 : Input validation
    # -------------------------------------------------------------
    is_valid = True

    if customer_name.strip() == "":
        st.warning("⚠️ Customer Name should not be empty.")
        is_valid = False

    if monthly_salary <= 0:
        st.warning("⚠️ Salary should be greater than zero.")
        is_valid = False

    if credit_score < 300 or credit_score > 900:
        st.warning("⚠️ Credit Score should be between 300 and 900.")
        is_valid = False

    if is_valid:

        # ---------------------------------------------------------
        # STEP 3 : Loan status by credit score (if-elif-else)
        # ---------------------------------------------------------
        # < 600 -> Reject | 600-750 -> Review | > 750 -> Approve
        if credit_score < 600:
            loan_status = "Rejected"
        elif credit_score <= 750:
            loan_status = "Under Review"
        else:
            loan_status = "Approved"

        # ---------------------------------------------------------
        # STEP 4 : Salary based risk assessment (if-elif-else)
        # ---------------------------------------------------------
        # < 30,000 -> High | 30,000-70,000 -> Medium | > 70,000 -> Low
        if monthly_salary < 30000:
            risk_level = "High Risk"
        elif monthly_salary <= 70000:
            risk_level = "Medium Risk"
        else:
            risk_level = "Low Risk"

        # ---------------------------------------------------------
        # STEP 6 : Final decision (combine credit, salary, loans)
        # ---------------------------------------------------------
        # My business rules:
        # 1. Credit score below 600                   -> REJECTED
        # 2. More than 3 existing loans               -> REJECTED
        # 3. Good credit + not high risk + max 2 loans -> APPROVED
        # 4. Anything else                            -> MANUAL REVIEW
        if loan_status == "Rejected":
            final_decision = "LOAN REJECTED"
        elif existing_loans > 3:
            final_decision = "LOAN REJECTED"
        elif loan_status == "Approved" and risk_level != "High Risk" and existing_loans <= 2:
            final_decision = "LOAN APPROVED"
        else:
            final_decision = "MANUAL REVIEW REQUIRED"

        # ---------------------------------------------------------
        # Display summary
        # ---------------------------------------------------------
        st.subheader("📋 Customer Loan Assessment")

        st.write(f"**Customer Name :** {customer_name.strip()}")
        st.write(f"**Credit Score :** {credit_score}")
        st.write(f"**Loan Status :** {loan_status}")
        st.write(f"**Risk Category :** {risk_level}")
        st.write(f"**Existing Loans :** {existing_loans}")

        # ---------------------------------------------------------
        # STEP 5 : Display documents using a for loop
        # ---------------------------------------------------------
        # if-else: first check whether the list is empty
        st.write("**Documents Submitted:**")
        if len(documents) == 0:
            st.info("No documents submitted.")
        else:
            for doc in documents:
                st.write(f"📄 {doc}")

        # Colour of the final decision depends on the result
        st.write("**Final Decision:**")
        if final_decision == "LOAN APPROVED":
            st.success(f"✅ {final_decision}")
        elif final_decision == "LOAN REJECTED":
            st.error(f"❌ {final_decision}")
        else:
            st.warning(f"🔍 {final_decision}")
