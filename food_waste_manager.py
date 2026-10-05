"""
============================================================
 SMART FOOD-WASTE MANAGEMENT SYSTEM
============================================================
 Author   : Saavan
 Course   : Python Fundamentals - Production-Oriented Assignment
 File     : food_waste_manager.py

 About:
   A menu-driven app that keeps track of food stock, checks expiry
   dates and tells staff which items need to be used, donated or
   thrown away before they turn into waste.

 Python concepts I used:
   - Variables & data types  (str, int, float, bool, date)
   - List of dictionaries    (the inventory itself)
   - Functions               (one function per job)
   - if / elif / else        (status classification, menu choices)
   - for / while loops       (going through items, menu loop)
   - try / except            (bad numbers, bad dates, wrong IDs)
   - f-strings               (formatted tables and messages)
   - datetime module         (date checks and day calculations)
============================================================
"""

# I only need these parts of datetime:
#   datetime  -> to convert text like "2026-10-05" into a date (strptime)
#   date      -> to get today's date
#   timedelta -> to add/subtract days (used for the sample data)
from datetime import datetime, date, timedelta
import math  # used to reject weird numbers like "inf" or "nan"


# ============================================================
# SETTINGS (constants) - written in CAPITALS so I know not to change them
# ============================================================
DATE_FORMAT = "%Y-%m-%d"        # every date must be typed as YYYY-MM-DD
EXPIRING_SOON_DAYS = 3          # 0 to 3 days left  -> EXPIRING SOON
OPERATING_DATE = date.today()   # the "current date" all expiry checks use

# Keeping status names in variables avoids spelling mistakes later
STATUS_EXPIRED = "EXPIRED"
STATUS_EXPIRING = "EXPIRING SOON"
STATUS_AVAILABLE = "AVAILABLE"

# What staff should do for each status (used for the waste/donation flag)
ACTION_FOR_STATUS = {
    STATUS_EXPIRED: "DISPOSE",
    STATUS_EXPIRING: "USE FIRST / DONATE",
    STATUS_AVAILABLE: "-",
}


# ============================================================
# SAMPLE DATA
# ============================================================
def days_from_today(days):
    """Return a date string that is 'days' away from today.
    Negative number = past date, positive number = future date.
    I use this so the sample data always shows all 3 statuses,
    no matter which day the program is run."""
    return (OPERATING_DATE + timedelta(days=days)).strftime(DATE_FORMAT)


# The whole inventory is a LIST, and every food item inside it is a DICTIONARY
inventory = [
    {"id": "FD001", "name": "Milk", "category": "Dairy", "quantity": 12, "unit": "L",
     "purchase_date": days_from_today(-6), "expiry_date": days_from_today(-1)},     # already expired
    {"id": "FD002", "name": "Tomatoes", "category": "Vegetables", "quantity": 15, "unit": "kg",
     "purchase_date": days_from_today(-2), "expiry_date": days_from_today(2)},      # expiring soon
    {"id": "FD003", "name": "Rice", "category": "Grains", "quantity": 25, "unit": "kg",
     "purchase_date": days_from_today(-10), "expiry_date": days_from_today(130)},   # available
]


# ============================================================
# VALIDATION FUNCTIONS
# Each one either returns a clean value or raises ValueError with a
# clear message. The calling function catches the error and prints it,
# so the program never crashes because of bad input.
# ============================================================
def validate_text(value, field_name):
    """Make sure a text field (ID, name, category, unit) is not blank."""
    value = value.strip()                      # remove extra spaces from both ends
    if not value:                              # empty string counts as False
        raise ValueError(f"{field_name} cannot be blank.")
    return value


def clean_number(number):
    """Round to 2 decimals and show whole numbers without '.0' (12.0 -> 12)."""
    number = round(number, 2)
    return int(number) if float(number).is_integer() else number


def validate_quantity(qty_text):
    """Convert the typed quantity to a number and make sure it is positive."""
    try:
        qty = float(qty_text)                  # float allows values like 2.5 kg
    except ValueError:
        # 'from None' hides the original Python error so only my message shows
        raise ValueError("Quantity must be a number (e.g. 5 or 2.5).") from None

    if not math.isfinite(qty):                 # blocks "inf" and "nan"
        raise ValueError("Quantity must be a real number.")
    if qty <= 0:                               # zero and negatives are not allowed
        raise ValueError("Quantity must be greater than zero.")
    return clean_number(qty)


def validate_date(date_text):
    """Check the date is in YYYY-MM-DD format and return it as a date object."""
    date_text = date_text.strip()
    if not date_text:
        raise ValueError("Date cannot be empty.")
    try:
        # strptime = "string parse time": turns text into a datetime,
        # .date() then keeps only the date part (no hours/minutes)
        return datetime.strptime(date_text, DATE_FORMAT).date()
    except ValueError:
        raise ValueError(f"Invalid date '{date_text}'. Use YYYY-MM-DD (e.g. 2026-10-05).") from None


# ============================================================
# HELPER FUNCTIONS (small reusable pieces)
# ============================================================
def find_item_by_id(item_id):
    """Look through the inventory and return the item with this ID, or None."""
    for item in inventory:
        if item["id"] == item_id.strip().upper():   # IDs are compared in uppercase
            return item
    return None                                     # loop finished, nothing matched


def format_qty(item):
    """Join quantity and unit together, e.g. '12 kg'."""
    return f"{item['quantity']} {item['unit']}"


def calculate_status(expiry_date_text):
    """Work out the expiry status of one item.
    Returns a tuple: (status, days_left)."""
    expiry_date = validate_date(expiry_date_text)
    days_left = (expiry_date - OPERATING_DATE).days    # subtracting dates gives a timedelta

    if days_left < 0:                                  # expiry date is before today
        return STATUS_EXPIRED, days_left
    elif days_left <= EXPIRING_SOON_DAYS:              # 0, 1, 2 or 3 days left
        return STATUS_EXPIRING, days_left
    else:                                              # more than 3 days left
        return STATUS_AVAILABLE, days_left


def count_statuses():
    """Count how many items fall into each status.
    Used by both the expiry monitor and the summary."""
    counts = {STATUS_EXPIRED: 0, STATUS_EXPIRING: 0, STATUS_AVAILABLE: 0}
    for item in inventory:
        status, _ = calculate_status(item["expiry_date"])   # '_' = value I don't need
        counts[status] += 1
    return counts


def print_item_table(items):
    """Print any list of items as a neat table.
    The :<N inside the f-string means 'left-align in N characters'."""
    print(f"{'ID':<7}{'ITEM':<18}{'CATEGORY':<13}{'QTY':<11}{'PURCHASED':<12}{'EXPIRY':<12}STATUS")
    print("-" * 87)
    for item in items:
        status, _ = calculate_status(item["expiry_date"])
        print(f"{item['id']:<7}{item['name'][:17]:<18}{item['category'][:12]:<13}"
              f"{format_qty(item):<11}{item['purchase_date']:<12}{item['expiry_date']:<12}{status}")


# ============================================================
# MAIN FEATURES (one function per menu option)
# ============================================================
def add_item():
    """Menu 1: ask for item details, validate everything, then save it."""
    print("\n--- ADD FOOD ITEM ---")
    try:
        # .upper() so 'fd005' and 'FD005' are treated as the same ID
        item_id = validate_text(input("Item ID       : "), "Item ID").upper()
        if find_item_by_id(item_id):                    # duplicate ID check
            raise ValueError(f"Item ID {item_id} already exists. IDs must be unique.")

        name = validate_text(input("Food Name     : "), "Food name")
        category = validate_text(input("Category      : "), "Category")
        quantity = validate_quantity(input("Quantity      : "))
        unit = validate_text(input("Unit          : "), "Unit")
        purchase_date = validate_date(input("Purchase Date : "))
        expiry_date = validate_date(input("Expiry Date   : "))

        # Business rule: a product can't expire before it was bought
        if expiry_date < purchase_date:
            raise ValueError("Expiry date cannot be earlier than purchase date.")

        # Build the dictionary for the new item.
        # Dates are saved back as text so they match the data model (and are easy to save to JSON later).
        new_item = {
            "id": item_id,
            "name": name,
            "category": category,
            "quantity": quantity,
            "unit": unit,
            "purchase_date": purchase_date.strftime(DATE_FORMAT),
            "expiry_date": expiry_date.strftime(DATE_FORMAT),
        }
        inventory.append(new_item)                      # add to the end of the list

        status, _ = calculate_status(new_item["expiry_date"])
        print(f"[SUCCESS] Food item {item_id} added successfully. Current status: {status}")

    except ValueError as error:
        # Any validation problem above jumps straight here
        print(f"[ERROR] {error} Please try again.")


def view_inventory():
    """Menu 2: show every item in the inventory."""
    print("\n--- CURRENT INVENTORY ---")
    if not inventory:                                   # empty list check
        print("[INFO] Inventory is empty.")
        return
    print_item_table(inventory)
    print(f"[INFO] Total records: {len(inventory)}")


def search_item():
    """Menu 3: find items whose name OR category contains the keyword."""
    print("\n--- SEARCH FOOD ITEM ---")
    keyword = input("Search item (name or category): ").strip().lower()
    if not keyword:
        print("[ERROR] Search text cannot be empty.")
        return

    results = []
    for item in inventory:
        # lower() on both sides makes the search case-insensitive
        # 'in' gives partial match, so 'pan' finds 'Fresh Paneer'
        if keyword in item["name"].lower() or keyword in item["category"].lower():
            results.append(item)

    if not results:
        print(f"[INFO] No items found matching '{keyword}'.")
        return

    for item in results:
        status, _ = calculate_status(item["expiry_date"])
        print(f"[RESULT] {item['id']} | {item['name']} | {item['category']} | "
              f"{format_qty(item)} | {status}")


def update_quantity():
    """Menu 4: increase or reduce stock, without ever going below zero."""
    print("\n--- UPDATE QUANTITY ---")
    item = find_item_by_id(input("Item ID: "))
    if item is None:
        print("[ERROR] Item ID not found.")
        return

    print(f"[INFO] {item['name']} - current stock: {format_qty(item)}")
    operation = input("Operation (add/reduce): ").strip().lower()

    # Accepting a few spellings makes the app friendlier
    if operation not in ("add", "increase", "a", "reduce", "decrease", "r"):
        print("[ERROR] Invalid operation. Type 'add' or 'reduce'.")
        return

    try:
        amount = validate_quantity(input("Quantity: "))
    except ValueError as error:
        print(f"[ERROR] {error}")
        return

    if operation in ("add", "increase", "a"):
        item["quantity"] = clean_number(item["quantity"] + amount)
    else:
        # Business rule: stock reduction must not make quantity negative
        if amount > item["quantity"]:
            print(f"[ERROR] Cannot reduce by {amount}. Only {format_qty(item)} in stock.")
            return
        item["quantity"] = clean_number(item["quantity"] - amount)

    print("[SUCCESS] Quantity updated.")
    print(f"[INFO] Remaining stock: {format_qty(item)}")
    if item["quantity"] == 0:
        print("[INFO] Stock is now zero. You may want to remove this item.")


def remove_item():
    """Menu 5: delete an item using its unique ID (asks for confirmation first)."""
    print("\n--- REMOVE FOOD ITEM ---")
    item = find_item_by_id(input("Item ID: "))
    if item is None:
        print("[ERROR] Item ID not found.")
        return

    confirm = input(f"Remove {item['id']} - {item['name']}? (y/n): ").strip().lower()
    if confirm == "y":
        inventory.remove(item)                          # removes that exact dictionary
        print(f"[SUCCESS] Item {item['id']} removed.")
    else:
        print("[INFO] Removal cancelled.")


def expiry_monitor():
    """Menu 6: show every item's status, days left, and what action to take.
    This also covers the Waste/Donation Flag requirement."""
    print("\n--- EXPIRY MONITOR ---")
    print(f"[INFO] Operating date: {OPERATING_DATE}")
    if not inventory:
        print("[INFO] Inventory is empty.")
        return

    print(f"{'ID':<7}{'ITEM':<18}{'QTY':<11}{'EXPIRY':<12}{'DAYS LEFT':<11}{'STATUS':<15}ACTION")
    print("-" * 92)
    for item in inventory:
        status, days_left = calculate_status(item["expiry_date"])
        print(f"{item['id']:<7}{item['name'][:17]:<18}{format_qty(item):<11}"
              f"{item['expiry_date']:<12}{days_left:<11}{status:<15}{ACTION_FOR_STATUS[status]}")

    # Alerts with correct singular/plural wording
    counts = count_statuses()
    expired = counts[STATUS_EXPIRED]
    expiring = counts[STATUS_EXPIRING]

    if expired:                                         # 0 counts as False, so this skips when none
        print(f"[ALERT] {expired} item{'s have' if expired > 1 else ' has'} expired.")
    if expiring:
        print(f"[ALERT] {expiring} item{'s require' if expiring > 1 else ' requires'} "
              f"attention within {EXPIRING_SOON_DAYS} days.")
    if not expired and not expiring:
        print("[INFO] All items are within their safe period.")


def generate_summary():
    """Menu 7: overall numbers plus a recommendation for staff."""
    print("\n--- INVENTORY SUMMARY ---")
    counts = count_statuses()

    # sum() with a generator: adds up the quantity of every item
    # (note: this mixes units like kg and L, it's just a total count of stock)
    total_quantity = clean_number(sum(item["quantity"] for item in inventory))
    attention_required = counts[STATUS_EXPIRED] + counts[STATUS_EXPIRING]

    print(f"Total food records       : {len(inventory)}")
    print(f"Total quantity (all units): {total_quantity}")
    print(f"Expired items            : {counts[STATUS_EXPIRED]}")
    print(f"Expiring-soon items      : {counts[STATUS_EXPIRING]}")
    print(f"Available items          : {counts[STATUS_AVAILABLE]}")
    print(f"Attention-required items : {attention_required}")

    # Recommendation changes depending on the situation
    if attention_required:
        print("[RECOMMENDATION] Prioritize expired stock for disposal according to "
              "food-safety procedures, and review expiring-soon stock for immediate "
              "consumption, redistribution, or donation where appropriate.")
    else:
        print("[RECOMMENDATION] No action needed right now. Keep monitoring daily.")


# ============================================================
# MAIN MENU - controls the whole program flow
# ============================================================
def main_menu():
    """Keep showing the menu until the user chooses 8 (Exit)."""
    print("[INFO] Smart Food-Waste Management System started")
    print(f"[INFO] Operating date: {OPERATING_DATE}")

    while True:                                         # infinite loop, 'break' ends it
        print("\n" + "=" * 50)
        print("        SMART FOOD-WASTE MANAGEMENT SYSTEM")
        print("=" * 50)
        print("1. Add Food Item")
        print("2. View Inventory")
        print("3. Search Food Item")
        print("4. Update Quantity")
        print("5. Remove Food Item")
        print("6. Expiry Monitoring")
        print("7. Inventory Summary")
        print("8. Exit")
        print("-" * 50)

        try:
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                add_item()
            elif choice == "2":
                view_inventory()
            elif choice == "3":
                search_item()
            elif choice == "4":
                update_quantity()
            elif choice == "5":
                remove_item()
            elif choice == "6":
                expiry_monitor()
            elif choice == "7":
                generate_summary()
            elif choice == "8":
                print("[INFO] Application closed successfully.")
                break                                   # leaves the while loop
            else:
                print("[ERROR] Invalid choice. Please enter a number from 1 to 8.")

        except (KeyboardInterrupt, EOFError):
            # Ctrl+C / Ctrl+D -> exit cleanly instead of showing a traceback
            print("\n[INFO] Application closed by user.")
            break
        except Exception as error:
            # Safety net: any unexpected error is shown, and the menu keeps running
            print(f"[ERROR] Something went wrong: {error}")


# This makes sure the menu only starts when I run this file directly,
# not when it's imported into another file (e.g. for unit tests).
if __name__ == "__main__":
    main_menu()
