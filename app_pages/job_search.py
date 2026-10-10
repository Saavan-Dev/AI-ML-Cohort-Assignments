"""
============================================================
Job Search & Recommendation App  (Wrench Wise - Task 3)
============================================================
Author : Saavan

Flow:
  1. Candidate enters skills + preferred location
  2. Jobs are fetched from a public jobs API (Arbeitnow / Remotive)
  3. Results are filtered, ranked by skill + location relevance
  4. Normalized searches / jobs / links are stored in MySQL
  5. Saved jobs feed a content-based recommender
============================================================
"""

# ---- Page info (read by registry.py to build the menu & README) ----
TITLE = "Job Search & Recommendation App"
NAV_TITLE = "Job Search"
URL_PATH = "job-search"
ICON = "💼"
DESCRIPTION = "Search jobs by skills and location via a public API, store them in MySQL, then filter and rank them."
ORDER = 4

import re
import ssl
import html
from datetime import datetime
import pandas as pd
import requests
import streamlit as st
from sqlalchemy import create_engine, URL, text
from sqlalchemy.exc import SQLAlchemyError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------- config
REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"

SOURCES = {
    "Arbeitnow (Europe, no API key)": "arbeitnow",
    "Remotive (remote jobs)": "remotive",
}


# ---------------------------------------------------------------- DB setup
@st.cache_resource
def get_engine():
    db_url = URL.create(
        drivername=st.secrets["DRIVERNAME"],
        username=st.secrets["USERNAME"],
        password=st.secrets["PASSWORD"],
        host=st.secrets["HOSTNAME"],
        port=int(st.secrets.get("PORT", 3306)),
        database=st.secrets["DATABASE"],
    )
    connect_args = {}
    if st.secrets.get("USE_SSL", True):          # Aiven requires SSL
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx
    return create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)


engine = get_engine()


# ---------------------------------------------------------------- helpers
def clean_html(raw):
    if not raw:
        return ""
    no_tags = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(no_tags)).strip()


def parse_date(value):
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        return datetime.fromisoformat(str(value)[:19])
    except (ValueError, OSError):
        return None


def split_skills(skills):
    return [s.strip().lower() for s in (skills or "").split(",") if s.strip()]


# ---------------------------------------------------------------- users
def get_or_create_user(username):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT IGNORE INTO users (username) VALUES (:u)"),
            {"u": username},
        )
        row = conn.execute(
            text("SELECT * FROM users WHERE username = :u"),
            {"u": username},
        ).mappings().first()
    return dict(row)


def update_profile(user_id, skills, location):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE users
                SET skills = :s, preferred_location = :l
                WHERE user_id = :id
            """),
            {"s": skills, "l": location, "id": user_id},
        )


# ---------------------------------------------------------------- API
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_arbeitnow():
    """Arbeitnow has no search parameter, so we fetch a page and filter locally."""
    response = requests.get(ARBEITNOW_URL, timeout=30)
    response.raise_for_status()

    jobs = []
    for j in response.json().get("data", []):
        tags = j.get("tags") or []
        job_types = j.get("job_types") or []
        location = j.get("location") or ""
        if j.get("remote"):
            location = f"{location} (Remote)".strip()
        slug = j.get("slug") or ""
        jobs.append({
            "source": "arbeitnow",
            "external_id": slug[:100],
            "title": (j.get("title") or "Untitled")[:255],
            "company": (j.get("company_name") or "")[:255],
            "category": (tags[0] if tags else None),
            "job_type": ", ".join(job_types)[:50] or None,
            "location": location[:255],
            "salary": None,
            "tags": ", ".join(tags),
            "url": (j.get("url") or "")[:500],
            "description": clean_html(j.get("description")),
            "published_at": parse_date(j.get("created_at")),
        })
    return jobs


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_remotive(term, limit=50):
    params = {"limit": limit}
    if term:
        params["search"] = term

    response = requests.get(REMOTIVE_URL, params=params, timeout=30)
    response.raise_for_status()

    jobs = []
    for j in response.json().get("jobs", []):
        jobs.append({
            "source": "remotive",
            "external_id": str(j.get("id"))[:100],
            "title": (j.get("title") or "Untitled")[:255],
            "company": (j.get("company_name") or "")[:255],
            "category": j.get("category"),
            "job_type": j.get("job_type"),
            "location": (j.get("candidate_required_location") or "")[:255],
            "salary": (j.get("salary") or "")[:100] or None,
            "tags": ", ".join(j.get("tags") or []),
            "url": (j.get("url") or "")[:500],
            "description": clean_html(j.get("description")),
            "published_at": parse_date(j.get("publication_date")),
        })
    return jobs


def fetch_jobs(source, skills, location, limit):
    """Fetch from the chosen API, keep only jobs matching a skill and the location."""
    skill_list = split_skills(skills)

    if source == "arbeitnow":
        jobs = fetch_arbeitnow()
    else:
        # Remotive supports a text search: query each skill (max 3) and merge
        merged = {}
        for term in (skill_list[:3] or [""]):
            for job in fetch_remotive(term, limit):
                merged[job["external_id"]] = job
        jobs = list(merged.values())

    loc = (location or "").lower().strip()
    result = []
    for job in jobs:
        blob = f"{job['title']} {job['tags']} {job['description']}".lower()
        if skill_list and not any(s in blob for s in skill_list):
            continue
        job_loc = (job["location"] or "").lower()
        # Remotive jobs are all remote, so the location only ranks them (below);
        # Arbeitnow jobs must match the location or be remote-friendly.
        if loc and source == "arbeitnow" and loc not in job_loc \
                and "remote" not in job_loc:
            continue
        result.append(job)
    return result


# ---------------------------------------------------------------- ranking
def score_jobs(df, skills, preferred_location, extra_profile=""):
    """
    Relevance score for every row of `df`:
      TF-IDF cosine similarity (skills weighted x3, plus extra_profile text)
      + 0.05 for a location match (or worldwide / remote)
      + up to 0.03 for recency
    Also adds a `matched_skills` column explaining the match.
    """
    df = df.copy()
    profile = (skills.strip() + " ") * 3 + extra_profile
    if df.empty or not profile.strip():
        df["score"] = 0.0
        df["matched_skills"] = ""
        return df

    docs = (
        (df["title"] + " ") * 2
        + df["tags"].fillna("") + " "
        + df["category"].fillna("") + " "
        + df["description"].fillna("").str[:3000]
    )
    vectorizer = TfidfVectorizer(
        stop_words="english", ngram_range=(1, 2),
        sublinear_tf=True, max_features=30000,
    )
    matrix = vectorizer.fit_transform(docs.tolist() + [profile])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()

    pref = (preferred_location or "").lower().strip()
    locs = df["location"].fillna("").str.lower()
    loc_match = locs.str.contains("worldwide|anywhere|remote", regex=True)
    if pref:
        loc_match |= locs.str.contains(re.escape(pref), regex=True)
    scores += loc_match.to_numpy() * 0.05

    published = pd.to_datetime(df["published_at"], errors="coerce")
    age_days = (pd.Timestamp.now() - published).dt.days.fillna(60).clip(0, 60)
    scores += (1 - age_days / 60).to_numpy() * 0.03

    df["score"] = scores

    skill_list = split_skills(skills)

    def matched(row):
        blob = f"{row['title']} {row['tags']} {row['description']}".lower()
        return ", ".join(s for s in skill_list if s in blob)

    df["matched_skills"] = df.apply(matched, axis=1)
    return df


# ---------------------------------------------------------------- persistence
UPSERT_JOB = text("""
    INSERT INTO jobs (
        source, external_id, title, company, category, job_type,
        location, salary, tags, url, description, published_at
    )
    VALUES (
        :source, :external_id, :title, :company, :category, :job_type,
        :location, :salary, :tags, :url, :description, :published_at
    )
    ON DUPLICATE KEY UPDATE
        job_id      = LAST_INSERT_ID(job_id),
        title       = VALUES(title),
        company     = VALUES(company),
        salary      = VALUES(salary),
        tags        = VALUES(tags),
        url         = VALUES(url),
        description = VALUES(description)
""")

JOB_COLUMNS = ["source", "external_id", "title", "company", "category",
               "job_type", "location", "salary", "tags", "url",
               "description", "published_at"]


def persist_search(user_id, keyword, location, jobs):
    """Save the search, upsert every job, and link them — in one transaction.
    `jobs` must already be ranked (best first)."""
    saved = []
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO searches (user_id, keyword, category, result_count)
                VALUES (:uid, :kw, :cat, :n)
            """),
            # the schema has no location column, so it is stored in `category`
            {"uid": user_id, "kw": keyword or None,
             "cat": (location or None), "n": len(jobs)},
        )
        search_id = result.lastrowid

        for rank, job in enumerate(jobs, start=1):
            params = {k: job.get(k) for k in JOB_COLUMNS}
            if pd.isna(params["published_at"]):
                params["published_at"] = None
            job_id = conn.execute(UPSERT_JOB, params).lastrowid
            conn.execute(
                text("""
                    INSERT IGNORE INTO search_results (search_id, job_id, rank_position)
                    VALUES (:sid, :jid, :r)
                """),
                {"sid": search_id, "jid": job_id, "r": rank},
            )
            saved.append({**job, "job_id": job_id})
    return saved


def set_job_status(user_id, job_id, status):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO saved_jobs (user_id, job_id, status)
                VALUES (:u, :j, :s)
                ON DUPLICATE KEY UPDATE status = VALUES(status)
            """),
            {"u": user_id, "j": job_id, "s": status},
        )


def get_saved_jobs(user_id):
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT j.*, s.status, s.saved_at
                FROM saved_jobs s
                JOIN jobs j ON j.job_id = s.job_id
                WHERE s.user_id = :u AND s.status IN ('saved', 'applied')
                ORDER BY s.saved_at DESC
            """),
            conn, params={"u": user_id},
        )


def get_search_history(user_id):
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT keyword AS skills, category AS location,
                       result_count, searched_at
                FROM searches
                WHERE user_id = :u
                ORDER BY searched_at DESC
                LIMIT 50
            """),
            conn, params={"u": user_id},
        )


# ---------------------------------------------------------------- recommender
def recommend(user, top_n=10):
    """
    Content-based recommendations from every job stored in MySQL.
    Profile = your skills + titles/tags of jobs you saved/applied to.
    Jobs you've already saved, applied to, or dismissed are excluded.
    """
    with engine.connect() as conn:
        candidates = pd.read_sql(
            text("""
                SELECT j.*
                FROM jobs j
                LEFT JOIN saved_jobs s
                       ON s.job_id = j.job_id AND s.user_id = :u
                WHERE s.job_id IS NULL
            """),
            conn, params={"u": user["user_id"]},
        )
        liked = pd.read_sql(
            text("""
                SELECT j.title, j.tags, j.category
                FROM saved_jobs s
                JOIN jobs j ON j.job_id = s.job_id
                WHERE s.user_id = :u AND s.status IN ('saved', 'applied')
            """),
            conn, params={"u": user["user_id"]},
        )

    if candidates.empty:
        return pd.DataFrame()

    liked_text = " ".join(
        (liked["title"] + " " + liked["tags"].fillna("") + " "
         + liked["category"].fillna("")).tolist()
    )
    scored = score_jobs(candidates, user.get("skills") or "",
                        user.get("preferred_location"), liked_text)
    return scored.nlargest(top_n, "score")


# ---------------------------------------------------------------- UI pieces
def job_card(job, user_id, key_prefix, show_score=False, show_actions=True):
    with st.container(border=True):
        st.markdown(f"#### {job['title']}")
        st.markdown(f"**{job['company'] or 'Unknown company'}**")

        meta = [
            f"📍 {job['location'] or 'Anywhere'}",
            job.get("job_type") or "",
            job.get("category") or "",
        ]
        st.caption(" · ".join(m for m in meta if m))

        if job.get("salary"):
            st.write(f"💰 {job['salary']}")
        if job.get("tags"):
            st.caption(f"🏷️ {job['tags']}")
        if show_score:
            st.progress(min(float(job["score"]), 1.0),
                        text=f"Match score: {job['score']:.2f}")
            if job.get("matched_skills"):
                st.caption(f"✅ Matches your skills: {job['matched_skills']}")

        with st.expander("Description"):
            desc = job.get("description") or "No description."
            st.write(desc[:2000] + ("…" if len(desc) > 2000 else ""))

        cols = st.columns(4)
        if job.get("url"):
            cols[0].link_button("Open ↗", job["url"])

        if show_actions:
            jid = int(job["job_id"])
            if cols[1].button("⭐ Save", key=f"{key_prefix}_save_{jid}"):
                set_job_status(user_id, jid, "saved")
                st.toast("Saved!")
            if cols[2].button("✅ Applied", key=f"{key_prefix}_apply_{jid}"):
                set_job_status(user_id, jid, "applied")
                st.toast("Marked as applied")
            if cols[3].button("🚫 Not for me", key=f"{key_prefix}_dis_{jid}"):
                set_job_status(user_id, jid, "dismissed")
                st.toast("Hidden from recommendations")


# ---------------------------------------------------------------- page
st.title("💼 Job Search & Recommendations")

# Sidebar: user profile
with st.sidebar:
    st.header("Your profile")
    username = st.text_input("Username", placeholder="e.g. priya")

    if not username:
        st.info("Enter a username to start.")
        st.stop()

    try:
        user = get_or_create_user(username.strip())
    except SQLAlchemyError as e:
        st.error(f"Database error: {e}")
        st.stop()

    skills = st.text_area(
        "Skills (comma-separated)",
        value=user.get("skills") or "",
        placeholder="python, sql, streamlit, machine learning",
    )
    location = st.text_input(
        "Preferred location",
        value=user.get("preferred_location") or "",
        placeholder="Berlin, Germany, Remote…",
    )
    if st.button("Save profile"):
        update_profile(user["user_id"], skills, location)
        st.success("Profile saved")
        st.rerun()

    st.caption("Job data from [Arbeitnow](https://www.arbeitnow.com) and "
               "[Remotive](https://remotive.com)")

tab_search, tab_recs, tab_saved, tab_history = st.tabs(
    ["🔍 Search", "✨ Recommended", "⭐ Saved", "🕘 History"]
)

# Search tab
with tab_search:
    st.caption("Searches use the skills and location typed in the sidebar.")
    source_label = st.selectbox("Job source", list(SOURCES.keys()))
    limit = st.slider("Max results per skill (Remotive)", 10, 100, 50, step=10)

    if st.button("Search Jobs", type="primary"):
        if not split_skills(skills):
            st.warning("Add at least one skill in the sidebar.")
        else:
            try:
                with st.spinner("Fetching and ranking jobs..."):
                    found = fetch_jobs(SOURCES[source_label], skills,
                                       location, limit)
                    if found:
                        ranked = score_jobs(pd.DataFrame(found), skills, location)
                        ranked = ranked.sort_values("score", ascending=False)
                        ranked_jobs = ranked.to_dict("records")
                    else:
                        ranked_jobs = []
                    st.session_state.results = persist_search(
                        user["user_id"], skills, location, ranked_jobs
                    )
            except requests.RequestException as e:
                st.error(f"API error: {e}")
            except SQLAlchemyError as e:
                st.error(f"Database error: {e}")

    results = st.session_state.get("results", [])
    if results:
        # ---- filters on the already-ranked results
        st.subheader("Filters")
        f1, f2 = st.columns(2)
        types = sorted({t.strip() for r in results
                        for t in (r.get("job_type") or "").split(",") if t.strip()})
        chosen_types = f1.multiselect("Job type", types)
        remote_only = f2.checkbox("Remote only")
        min_score = st.slider("Minimum match score", 0.0, 1.0, 0.0, step=0.05)
        sort_by = st.radio("Sort by", ["Relevance", "Newest"], horizontal=True)

        shown = [
            r for r in results
            if r["score"] >= min_score
            and (not chosen_types
                 or any(t in (r.get("job_type") or "") for t in chosen_types))
            and (not remote_only
                 or "remote" in f"{r.get('location')} {r.get('tags')}".lower()
                 or r["source"] == "remotive")
        ]
        if sort_by == "Newest":
            shown.sort(key=lambda r: r["published_at"]
                       if pd.notna(r["published_at"]) else datetime.min,
                       reverse=True)

        st.success(f"Showing {len(shown)} of {len(results)} jobs "
                   "(all saved to database)")
        for job in shown:
            job_card(job, user["user_id"], key_prefix="search", show_score=True)
    elif "results" in st.session_state:
        st.info("No jobs found. Try broader skills or another location/source.")

# Recommendations tab
with tab_recs:
    if not (user.get("skills") or "").strip():
        st.info("Add your skills in the sidebar to get recommendations. "
                "Saving jobs also improves them.")
    else:
        recs = recommend(user, top_n=10)
        if recs.empty:
            st.info("No stored jobs yet. Run a few searches first. "
                    "Recommendations come from every job in your database.")
        else:
            for _, job in recs.iterrows():
                job_card(job.to_dict(), user["user_id"],
                         key_prefix="rec", show_score=True)

# Saved tab
with tab_saved:
    saved = get_saved_jobs(user["user_id"])
    if saved.empty:
        st.info("You haven't saved any jobs yet.")
    else:
        for status in ("applied", "saved"):
            subset = saved[saved["status"] == status]
            if not subset.empty:
                st.subheader(f"{status.title()} ({len(subset)})")
                for _, job in subset.iterrows():
                    job_card(job.to_dict(), user["user_id"],
                             key_prefix=f"saved_{status}", show_actions=False)

# History tab
with tab_history:
    history = get_search_history(user["user_id"])
    if history.empty:
        st.info("No searches yet.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)
