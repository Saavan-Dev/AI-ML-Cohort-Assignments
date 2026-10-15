"""
Connects to the MySQL database and runs a tiny query (SELECT 1)
so the free hosting provider sees activity and keeps the DB alive.

All connection details come from environment variables
"""

import os
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ------------------------------------------------------------
# Helper: read a setting from the environment safely.
# .strip() removes accidental spaces/newlines from copy-paste,
# which is a very common cause of "Name or service not known".
# ------------------------------------------------------------
def get_env(name, default=None):
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        print(f"ERROR: secret/env variable '{name}' is missing or empty.")
        sys.exit(1)
    return value.strip()


# ------------------------------------------------------------
# 1. Read all connection settings
# ------------------------------------------------------------
driver   = get_env("DB_DRIVERNAME", "mysql+pymysql")  # e.g. mysql+pymysql
username = get_env("DB_USERNAME")
password = get_env("DB_PASSWORD")
host     = get_env("DB_HOST")
port     = int(get_env("DB_PORT", "3306"))
database = get_env("DB_DATABASE")

# ------------------------------------------------------------
# 2. Catch common mistakes in DB_HOST early, with a clear message
#    (we never print the host itself, logs are public)
# ------------------------------------------------------------
if "://" in host:
    print("ERROR: DB_HOST must not contain 'mysql://' or 'https://'. Use only the hostname.")
    sys.exit(1)
if ":" in host:
    print("ERROR: DB_HOST must not contain ':port'. Put the port in DB_PORT instead.")
    sys.exit(1)

# ------------------------------------------------------------
# 3. Build the connection URL.
#    URL.create() safely handles special characters in the
#    password (like @, #, /), which can break a hand-written URL.
# ------------------------------------------------------------
db_url = URL.create(
    drivername=driver,
    username=username,
    password=password,
    host=host,
    port=port,
    database=database,
)

# pool_pre_ping checks the connection is alive before using it.
# connect_timeout stops it from hanging forever if the DB is down.
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10},
)

# ------------------------------------------------------------
# 4. Try to connect, retrying a few times in case of a
#    temporary network hiccup.
# ------------------------------------------------------------
MAX_ATTEMPTS = 3
WAIT_SECONDS = 10

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
        print(f"SUCCESS: database is alive (SELECT 1 returned {result}).")
        sys.exit(0)

    except Exception as e:
        # Show only the error type, not full details,
        # so no connection info leaks into public logs.
        print(f"Attempt {attempt}/{MAX_ATTEMPTS} failed: {type(e).__name__}")

        if attempt < MAX_ATTEMPTS:
            print(f"Retrying in {WAIT_SECONDS} seconds...")
            time.sleep(WAIT_SECONDS)

# ------------------------------------------------------------
# 5. All attempts failed: exit with error so the Actions run
#    shows a red X and you get an email notification.
# ------------------------------------------------------------
print("FAILED: could not reach the database.")
print("Check: 1) the DB still exists in your provider dashboard,")
print("       2) DB_HOST is the PUBLIC hostname with no scheme, port or spaces.")
sys.exit(1)
