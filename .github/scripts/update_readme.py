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
BASE_URL = APP_URL.rstrip("/")

DEFAULT_HEADER = """# 📚 AI/ML Cohort Assignments

Hands-on AI/ML projects from my Wrench Wise cohort — Python, Streamlit, REST APIs, MySQL and beyond, each deployed as a live demo. #LearnInPublic

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

## 🚀 Projects
"""


def build_section(assignments):
    lines = [
        START,
        "",
        f"[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)]({BASE_URL}/)",
        "",
        f"**🔗 Live app (all assignments):** {BASE_URL}/",
        "",
    ]

    if assignments:
        lines += [
            "| # | Assignment | Live Demo | Source Code |",
            "|---|---|---|---|",
        ]
        for number, a in enumerate(assignments, start=1):
            title = a["title"].replace("|", "\\|")   # keep the table intact
            lines.append(
                f"| {number} | {a['icon']} {title} "
                f"| [Open App]({BASE_URL}/{a['url_path']}) "
                f"| [{Path(a['source']).name}]({a['source']}) |"
            )
    else:
        lines.append("_No assignments published yet._")

    lines += [
        "",
        "> ⚙️ **Always on:** a scheduled GitHub Actions workflow runs an automated health check "
        "to keep the live app awake. If you still see a sleeping screen, click "
        '**"Yes, get this app back up!"** and wait ~30 seconds.',
        "",
        "📌 _More projects will be added as the cohort progresses._",
        "",
        "<sub>This section is generated automatically. Edits inside it will be overwritten.</sub>",
        "",
        END,
    ]
    return "\n".join(lines)


def main():
    section = build_section(discover_assignments())
    old_text = README.read_text(encoding="utf-8") if README.exists() else DEFAULT_HEADER

    if START in old_text and END in old_text:
        before = old_text.split(START, 1)[0]
        after = old_text.split(END, 1)[1]
        new_text = before + section + after
    else:
        new_text = old_text.rstrip() + "\n\n" + section + "\n"   # first run: add at the end

    if new_text != old_text:
        README.write_text(new_text, encoding="utf-8", newline="\n")
        print("README.md updated.")
    else:
        print("README.md already up to date.")


if __name__ == "__main__":
    main()
