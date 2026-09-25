import csv
import io
import sqlite3

import pytest

from tracker import db
from tracker.export import rows_to_df, to_csv_bytes


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    return path


def add(db_path, company="Acme", role="Data Intern", status="Applied", **kw):
    return db.add_application(
        db_path,
        company,
        role,
        kw.get("link", ""),
        status,
        kw.get("applied_date", "2026-09-01"),
        kw.get("follow_up_date"),
        kw.get("notes", ""),
    )


def test_add_and_read_back(db_path):
    app_id = add(db_path, link="https://example.com", follow_up_date="2026-09-15", notes="referral")
    (row,) = db.get_applications(db_path)
    assert row == (app_id, "Acme", "Data Intern", "https://example.com", "Applied",
                   "2026-09-01", "2026-09-15", "referral")


def test_newest_first(db_path):
    first = add(db_path, company="First")
    second = add(db_path, company="Second")
    assert [r[0] for r in db.get_applications(db_path)] == [second, first]


def test_status_filter(db_path):
    add(db_path, status="Applied")
    add(db_path, status="Offer")
    assert [r[4] for r in db.get_applications(db_path, "Offer")] == ["Offer"]
    assert len(db.get_applications(db_path, "All")) == 2


def test_count_by_status(db_path):
    add(db_path, status="Applied")
    add(db_path, status="Applied")
    add(db_path, status="Rejected")
    assert db.count_by_status(db_path) == {
        "Applied": 2, "Interviewing": 0, "Offer": 0, "Rejected": 1, "Total": 3,
    }


def test_update_status(db_path):
    app_id = add(db_path)
    db.update_status(db_path, app_id, "Interviewing")
    assert db.get_applications(db_path)[0][4] == "Interviewing"


def test_delete(db_path):
    keep = add(db_path, company="Keep")
    drop = add(db_path, company="Drop")
    db.delete_application(db_path, drop)
    assert [r[0] for r in db.get_applications(db_path)] == [keep]


@pytest.mark.parametrize("company,role", [("", "Intern"), ("Acme", "")])
def test_rejects_missing_required_fields(db_path, company, role):
    with pytest.raises(ValueError):
        add(db_path, company=company, role=role)


def test_rejects_unknown_status(db_path):
    with pytest.raises(ValueError):
        add(db_path, status="Ghosted")
    app_id = add(db_path)
    with pytest.raises(ValueError):
        db.update_status(db_path, app_id, "Ghosted")


def test_init_db_is_idempotent(db_path):
    add(db_path)
    db.init_db(db_path)
    assert len(db.get_applications(db_path)) == 1


def test_migrated_database_keeps_columns_aligned(tmp_path):
    """Regression: a table created before follow_up_date existed gets that
    column appended last, so SELECT * used to swap notes and follow-up date."""
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.execute("""
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL, role TEXT NOT NULL, link TEXT,
                status TEXT NOT NULL, applied_date TEXT NOT NULL, notes TEXT
            )
        """)
    conn.close()

    db.init_db(path)
    add(path, follow_up_date="2026-10-01", notes="call recruiter")
    row = db.get_applications(path)[0]
    assert row[db.COLUMNS.index("follow_up_date")] == "2026-10-01"
    assert row[db.COLUMNS.index("notes")] == "call recruiter"


def test_csv_export_with_rows(db_path):
    """Regression: export used to pass 7 column names for 8-column rows and
    crash as soon as a single application existed."""
    add(db_path, company="Acme", notes="hello, world")
    rows = db.get_applications(db_path)
    assert list(rows_to_df(rows).columns) == db.COLUMNS

    records = list(csv.DictReader(io.StringIO(to_csv_bytes(rows).decode("utf-8"))))
    assert records[0]["company"] == "Acme"
    assert records[0]["notes"] == "hello, world"


def test_csv_export_empty(db_path):
    header = to_csv_bytes([]).decode("utf-8").strip()
    assert header.split(",") == db.COLUMNS
