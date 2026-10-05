"""
Rebuilds the assignments section of README.md from registry.py.
Only the text between the START/END markers is replaced, so anything
else I write in the README stays untouched.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]       # .github/scripts/ -> repo root
sys.path.insert(0, str(ROOT))                    # so "import registry" works
from registry import APP_URL, discover_assignments

README = ROOT / "README.md"
START = "<!-- ASSIGNMENTS:START -->"
END = "<!-- ASSIGNMENTS:END -->"


def build_section(assignments):
    lines = [
        START,
        "",
        f"[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)]({APP_URL}/)",
        "",
        f"**🔗 Live app (all assignments):** {APP_URL}/",
        "",
        "| # | Assignment | Live Demo | Source Code |",
        "|---|---|---|---|",
    ]
    for number, a in enumerate(assignments, start=1):
        lines.append(f"| {number} | {a['icon']} {a['title']} | [Open App]({APP_URL}/{a['url_path']}) "
                     f"| [{Path(a['source']).name}]({a['source']}) |")
    lines += [
        "",
        '> ℹ️ If the app shows a sleeping screen, click **"Yes, get this app back up!"** and wait ~30 seconds.',
        "",
        "<sub>This section is generated automatically. Edits inside it will be overwritten.</sub>",
        "",
        END,
    ]
    return "\n".join(lines)


def main():
    section = build_section(discover_assignments())
    old_text = README.read_text(encoding="utf-8") if README.exists() else "# 📚 AI/ML Cohort Assignments\n"

    if START in old_text and END in old_text:
        before = old_text.split(START)[0]                # everything above the markers
        after = old_text.split(END, 1)[1]                # everything below the markers
        new_text = before + section + after
    else:
        new_text = old_text.rstrip() + "\n\n" + section + "\n"   # first run: add at the end

    if new_text != old_text:
        README.write_text(new_text, encoding="utf-8")
        print("README.md updated.")
    else:
        print("README.md already up to date.")


if __name__ == "__main__":
    main()
