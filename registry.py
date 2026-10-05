"""
============================================================
 ASSIGNMENT REGISTRY
============================================================
 Automatically finds every assignment page inside app_pages/ and
 reads its info (title, icon, link...) from simple constants at the
 top of each page file.

 Used by:
   - streamlit_app.py                  -> builds the navigation menu
   - app_pages/home.py                 -> builds the home page cards
   - .github/scripts/update_readme.py  -> builds the README table

 Every page file in app_pages/ must start with an info block like:

     TITLE = "Smart Food-Waste Management System"   # required
     URL_PATH = "food-waste"                        # required, unique, no spaces
     NAV_TITLE = "Food-Waste Manager"               # optional, short name for the menu
     ICON = "🥗"                                     # optional
     DESCRIPTION = "One line about the assignment"  # optional
     SOURCE = "food_waste_manager.py"               # optional, main code file
     ORDER = 1                                      # optional, sort order
============================================================
"""

import ast
from pathlib import Path

# ---- My links (change these to yours, no trailing slash) ----
APP_URL = "https://saavan-assignments.streamlit.app"
REPO_URL = "https://github.com/Saavan-Dev/ai-ml-cohort-assignments"

REPO_ROOT = Path(__file__).resolve().parent     # folder this file lives in
PAGES_DIR = REPO_ROOT / "app_pages"
SKIP_FILES = {"home.py", "__init__.py"}          # files that are not assignments

INFO_KEYS = ("TITLE", "NAV_TITLE", "ICON", "URL_PATH", "DESCRIPTION", "SOURCE", "ORDER")
REQUIRED_KEYS = ("TITLE", "URL_PATH")


def read_page_info(path):
    """Read the info constants from a page file WITHOUT running it.
    ast.parse turns the code into a tree; I only look at simple
    'NAME = value' lines at the top level of the file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as error:
        print(f"[registry] Skipping {path.name}: syntax error ({error})")
        return {}

    info = {}
    for node in tree.body:
        # only plain assignments like  TITLE = "..."
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in INFO_KEYS):
            try:
                # literal_eval safely reads strings/numbers (never runs code)
                info[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass                                   # ignore non-literal values
    return info


def discover_assignments():
    """Return a sorted list of dictionaries, one per assignment page."""
    assignments = []
    seen_paths = set()

    for path in sorted(PAGES_DIR.glob("*.py")):
        if path.name in SKIP_FILES or path.name.startswith("_"):
            continue

        info = read_page_info(path)
        if not all(key in info for key in REQUIRED_KEYS):
            print(f"[registry] Skipping {path.name}: needs TITLE and URL_PATH")
            continue
        if info["URL_PATH"] in seen_paths:
            print(f"[registry] Skipping {path.name}: URL_PATH '{info['URL_PATH']}' already used")
            continue
        seen_paths.add(info["URL_PATH"])

        assignments.append({
            "file": f"app_pages/{path.name}",
            "title": info["TITLE"],
            "nav_title": info.get("NAV_TITLE", info["TITLE"]),
            "icon": info.get("ICON", "📄"),
            "url_path": info["URL_PATH"],
            "description": info.get("DESCRIPTION", ""),
            "source": info.get("SOURCE", f"app_pages/{path.name}"),
            "order": info.get("ORDER", 999),            # no ORDER -> goes to the end
        })

    # Sort by ORDER first, then alphabetically by title
    assignments.sort(key=lambda a: (a["order"], a["title"]))
    return assignments


# Quick check: run "python registry.py" to see what gets detected
if __name__ == "__main__":
    for a in discover_assignments():
        print(f"{a['order']:>3}  {a['icon']} {a['title']}  ->  {APP_URL}/{a['url_path']}")
