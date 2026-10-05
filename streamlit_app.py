"""
============================================================
 SMART FOOD-WASTE MANAGEMENT SYSTEM - Streamlit Web Version
============================================================
 Author : Saavan
 File   : streamlit_app.py

 This is the web dashboard for my console app (food_waste_manager.py).
 Instead of rewriting the logic, I IMPORT the validation and status
 functions from the console file, so both versions follow the exact
 same business rules.

 Run locally:  streamlit run streamlit_app.py
============================================================
"""

from datetime import datetime
from zoneinfo import ZoneInfo           # built-in module for time zones

import streamlit as st
import food_waste_manager as fwm        # my console app, imported as a module
# (importing is safe because main_menu() only runs under `if __name__ == "__main__"`)


# ------------------------------------------------------------
# PAGE SETUP
# ------------------------------------------------------------
st.set_page_config(page_title="Smart Food-Waste Manager", page_icon="🥗", layout="wide")

# The server can stay running for days, so I refresh the operating date on every
# page load. I use Indian time because the cloud server runs in UTC.
fwm.OPERATING_DATE = datetime.now(ZoneInfo("Asia/Kolkata")).date()

# Coloured dots make statuses easy to spot in tables
STATUS_ICON = {
    fwm.STATUS_EXPIRED: "🔴",
    fwm.STATUS_EXPIRING: "🟠",
    fwm.STATUS_AVAILABLE: "🟢",
}


# ------------------------------------------------------------
# DATA STORAGE (session_state)
# Streamlit re-runs this whole script on every click, so normal
# variables would reset. st.session_state keeps data alive for each
# visitor, and every visitor gets their own separate inventory.
# ------------------------------------------------------------
def sample_inventory():
    """Fresh sample data, with dates relative to today (same idea as the console app)."""
    return [
        {"id": "FD001", "name": "Milk", "category": "Dairy", "quantity": 12, "unit": "L",
         "purchase_date": fwm.days_from_today(-6), "expiry_date": fwm.days_from_today(-1)},
        {"id": "FD002", "name": "Tomatoes", "category": "Vegetables", "quantity": 15, "unit": "kg",
         "purchase_date": fwm.days_from_today(-2), "expiry_date": fwm.days_from_today(2)},
        {"id": "FD003", "name": "Rice", "category": "Grains", "quantity": 25, "unit": "kg",
         "purchase_date": fwm.days_from_today(-10), "expiry_date": fwm.days_from_today(130)},
    ]


if "inventory" not in st.session_state:            # only on the first visit
    st.session_state.inventory = sample_inventory()

inventory = st.session_state.inventory             # short name; changes still save to session_state


# ------------------------------------------------------------
# HELPER FUNCTIONS (web versions that work on session_state data)
# ------------------------------------------------------------
def find_item(item_id):
    """Return the item with this ID, or None if it doesn't exist."""
    for item in inventory:
        if item["id"] == item_id.strip().upper():
            return item
    return None


def count_statuses():
    """Count items per status using the console app's calculate_status()."""
    counts = {fwm.STATUS_EXPIRED: 0, fwm.STATUS_EXPIRING: 0, fwm.STATUS_AVAILABLE: 0}
    for item in inventory:
        status, _ = fwm.calculate_status(item["expiry_date"])
        counts[status] += 1
    return counts


def table_rows(items, show_action=False):
    """Turn inventory dictionaries into rows for st.dataframe."""
    rows = []
    for item in items:
        status, days_left = fwm.calculate_status(item["expiry_date"])
        row = {
            "ID": item["id"],
            "Item": item["name"],
            "Category": item["category"],
            "Quantity": fwm.format_qty(item),
            "Purchased": item["purchase_date"],
            "Expiry": item["expiry_date"],
            "Days Left": days_left,
            "Status": f"{STATUS_ICON[status]} {status}",
        }
        if show_action:                                  # extra column for the expiry monitor
            row["Action"] = fwm.ACTION_FOR_STATUS[status]
        rows.append(row)
    return rows


def item_label(item_id):
    """Text shown in dropdowns, e.g. 'FD001 - Milk'."""
    item = find_item(item_id)
    return f"{item_id} - {item['name']}" if item else item_id


# ------------------------------------------------------------
# SIDEBAR MENU (replaces the numbered console menu)
# ------------------------------------------------------------
st.sidebar.title("🥗 Food-Waste Manager")
page = st.sidebar.radio(
    "Menu",
    ["📊 Inventory Summary", "➕ Add Food Item", "📋 View Inventory", "🔍 Search Food Item",
     "✏️ Update Quantity", "🗑️ Remove Food Item", "⏰ Expiry Monitoring"],
)
st.sidebar.divider()
st.sidebar.caption(f"Operating date: **{fwm.OPERATING_DATE}**")
st.sidebar.caption("Data is stored per session and resets when you refresh the page.")
if st.sidebar.button("Reset sample data"):
    st.session_state.inventory = sample_inventory()
    st.rerun()                                           # reload the page with fresh data

st.title("Smart Food-Waste Management System")


# ------------------------------------------------------------
# PAGE: INVENTORY SUMMARY
# ------------------------------------------------------------
if page == "📊 Inventory Summary":
    st.subheader("📊 Inventory Summary")
    counts = count_statuses()
    total_qty = fwm.clean_number(sum(item["quantity"] for item in inventory))
    attention = counts[fwm.STATUS_EXPIRED] + counts[fwm.STATUS_EXPIRING]

    # st.metric shows a big number with a label, like a dashboard card
    c1, c2, c3 = st.columns(3)
    c1.metric("Total food records", len(inventory))
    c2.metric("Total quantity (all units)", total_qty)
    c3.metric("Attention-required items", attention)

    c4, c5, c6 = st.columns(3)
    c4.metric("🔴 Expired", counts[fwm.STATUS_EXPIRED])
    c5.metric("🟠 Expiring soon", counts[fwm.STATUS_EXPIRING])
    c6.metric("🟢 Available", counts[fwm.STATUS_AVAILABLE])

    if attention:
        st.warning("**Recommendation:** Prioritize expired stock for disposal according to "
                   "food-safety procedures, and review expiring-soon stock for immediate "
                   "consumption, redistribution, or donation where appropriate.")
    else:
        st.success("No action needed right now. Keep monitoring daily.")


# ------------------------------------------------------------
# PAGE: ADD FOOD ITEM
# ------------------------------------------------------------
elif page == "➕ Add Food Item":
    st.subheader("➕ Add Food Item")

    # st.form groups inputs so the app only reacts when "Add Item" is clicked
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        item_id = c1.text_input("Item ID", placeholder="e.g. FD004")
        name = c2.text_input("Food Name", placeholder="e.g. Fresh Paneer")
        category = c1.text_input("Category", placeholder="e.g. Dairy")
        unit = c2.text_input("Unit", placeholder="kg, L, pcs...")
        quantity = c1.text_input("Quantity", placeholder="e.g. 8 or 2.5")
        c2.write("")                                     # small spacer to align columns
        purchase_date = c1.date_input("Purchase Date", value=fwm.OPERATING_DATE)
        expiry_date = c2.date_input("Expiry Date", value=fwm.OPERATING_DATE)
        submitted = st.form_submit_button("Add Item", type="primary")

    if submitted:
        try:
            # Same validation functions as the console app
            clean_id = fwm.validate_text(item_id, "Item ID").upper()
            if find_item(clean_id):
                raise ValueError(f"Item ID {clean_id} already exists. IDs must be unique.")
            clean_name = fwm.validate_text(name, "Food name")
            clean_category = fwm.validate_text(category, "Category")
            clean_unit = fwm.validate_text(unit, "Unit")
            clean_qty = fwm.validate_quantity(quantity)

            if expiry_date < purchase_date:
                raise ValueError("Expiry date cannot be earlier than purchase date.")

            inventory.append({
                "id": clean_id,
                "name": clean_name,
                "category": clean_category,
                "quantity": clean_qty,
                "unit": clean_unit,
                "purchase_date": purchase_date.strftime(fwm.DATE_FORMAT),
                "expiry_date": expiry_date.strftime(fwm.DATE_FORMAT),
            })
            status, _ = fwm.calculate_status(expiry_date.strftime(fwm.DATE_FORMAT))
            st.success(f"Food item {clean_id} added successfully. Status: {STATUS_ICON[status]} {status}")

        except ValueError as error:
            st.error(f"{error}")                          # shown in red, app keeps running


# ------------------------------------------------------------
# PAGE: VIEW INVENTORY
# ------------------------------------------------------------
elif page == "📋 View Inventory":
    st.subheader("📋 Current Inventory")
    if not inventory:
        st.info("Inventory is empty.")
    else:
        st.dataframe(table_rows(inventory), hide_index=True, width="stretch")
        st.caption(f"Total records: {len(inventory)}")


# ------------------------------------------------------------
# PAGE: SEARCH FOOD ITEM
# ------------------------------------------------------------
elif page == "🔍 Search Food Item":
    st.subheader("🔍 Search Food Item")
    keyword = st.text_input("Search by name or category", placeholder="e.g. paneer or dairy")

    if keyword.strip():                                   # only search when something is typed
        key = keyword.strip().lower()
        results = [item for item in inventory
                   if key in item["name"].lower() or key in item["category"].lower()]
        if results:
            st.dataframe(table_rows(results), hide_index=True, width="stretch")
        else:
            st.info(f"No items found matching '{keyword.strip()}'.")


# ------------------------------------------------------------
# PAGE: UPDATE QUANTITY
# ------------------------------------------------------------
elif page == "✏️ Update Quantity":
    st.subheader("✏️ Update Quantity")
    if not inventory:
        st.info("Inventory is empty.")
    else:
        selected_id = st.selectbox("Select item", [i["id"] for i in inventory], format_func=item_label)
        item = find_item(selected_id)
        st.write(f"Current stock: **{fwm.format_qty(item)}**")

        operation = st.radio("Operation", ["Add stock", "Reduce stock"], horizontal=True)
        amount_text = st.text_input("Quantity", placeholder="e.g. 3")

        if st.button("Update", type="primary"):
            try:
                amount = fwm.validate_quantity(amount_text)
                if operation == "Add stock":
                    item["quantity"] = fwm.clean_number(item["quantity"] + amount)
                else:
                    # Business rule: stock must never go negative
                    if amount > item["quantity"]:
                        raise ValueError(f"Cannot reduce by {amount}. Only {fwm.format_qty(item)} in stock.")
                    item["quantity"] = fwm.clean_number(item["quantity"] - amount)

                st.success(f"Quantity updated. Remaining stock: {fwm.format_qty(item)}")
                if item["quantity"] == 0:
                    st.info("Stock is now zero. You may want to remove this item.")
            except ValueError as error:
                st.error(f"{error}")


# ------------------------------------------------------------
# PAGE: REMOVE FOOD ITEM
# ------------------------------------------------------------
elif page == "🗑️ Remove Food Item":
    st.subheader("🗑️ Remove Food Item")
    if not inventory:
        st.info("Inventory is empty.")
    else:
        selected_id = st.selectbox("Select item to remove", [i["id"] for i in inventory],
                                   format_func=item_label)
        confirm = st.checkbox(f"Yes, I want to remove {item_label(selected_id)}")

        if st.button("Remove", type="primary"):
            if not confirm:                               # replaces the console (y/n) prompt
                st.error("Please tick the confirmation box first.")
            else:
                inventory.remove(find_item(selected_id))
                st.success(f"Item {selected_id} removed.")


# ------------------------------------------------------------
# PAGE: EXPIRY MONITORING (+ waste/donation flag)
# ------------------------------------------------------------
elif page == "⏰ Expiry Monitoring":
    st.subheader("⏰ Expiry Monitor")
    if not inventory:
        st.info("Inventory is empty.")
    else:
        st.dataframe(table_rows(inventory, show_action=True), hide_index=True, width="stretch")

        counts = count_statuses()
        expired = counts[fwm.STATUS_EXPIRED]
        expiring = counts[fwm.STATUS_EXPIRING]

        # Alerts with correct singular/plural wording
        if expired:
            st.error(f"🚨 {expired} item{'s have' if expired > 1 else ' has'} expired. Dispose safely.")
        if expiring:
            st.warning(f"⚠️ {expiring} item{'s require' if expiring > 1 else ' requires'} attention "
                       f"within {fwm.EXPIRING_SOON_DAYS} days. Use first or donate.")
        if not expired and not expiring:
            st.success("All items are within their safe period.")
