"""SQLite persistence for the job application tracker.

Kept separate from the Streamlit UI so it can be tested without a browser.
"""

import sqlite3
from contextlib import closing

STATUSES = ["Applied", "Interviewing", "Offer", "Rejected"]

# Selected explicitly instead of SELECT * so column order never depends on
# how the table was created or migrated.
COLUMNS = ["id", "company", "role", "link", "status", "applied_date", "follow_up_date", "notes"]
_SELECT = f"SELECT {', '.join(COLUMNS)} FROM applications"


def connect(db_path):
    return sqlite3.connect(db_path, check_same_thread=False)


def init_db(db_path):
    with closing(connect(db_path)) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                link TEXT,
                status TEXT NOT NULL,
                applied_date TEXT NOT NULL,
                follow_up_date TEXT,
                notes TEXT
            )
        """)
        # Databases created before follow-up dates existed lack the column.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(applications)")}
        if "follow_up_date" not in existing:
            conn.execute("ALTER TABLE applications ADD COLUMN follow_up_date TEXT")


def add_application(db_path, company, role, link, status, applied_date, follow_up_date, notes):
    if not company or not role:
        raise ValueError("company and role are required")
    if status not in STATUSES:
        raise ValueError(f"unknown status: {status!r}")
    with closing(connect(db_path)) as conn, conn:
        cur = conn.execute(
            """
            INSERT INTO applications (company, role, link, status, applied_date, follow_up_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (company, role, link, status, applied_date, follow_up_date, notes),
        )
        return cur.lastrowid


def get_applications(db_path, status_filter=None):
    with closing(connect(db_path)) as conn:
        if status_filter and status_filter != "All":
            return conn.execute(f"{_SELECT} WHERE status = ? ORDER BY id DESC", (status_filter,)).fetchall()
        return conn.execute(f"{_SELECT} ORDER BY id DESC").fetchall()


def count_by_status(db_path):
    """Return {status: count} for every known status, plus a 'Total' key."""
    with closing(connect(db_path)) as conn:
        counts = dict(conn.execute("SELECT status, COUNT(*) FROM applications GROUP BY status"))
    result = {s: counts.get(s, 0) for s in STATUSES}
    result["Total"] = sum(counts.values())
    return result


def update_status(db_path, app_id, new_status):
    if new_status not in STATUSES:
        raise ValueError(f"unknown status: {new_status!r}")
    with closing(connect(db_path)) as conn, conn:
        conn.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, app_id))


def delete_application(db_path, app_id):
    with closing(connect(db_path)) as conn, conn:
        conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
