# Job Application Tracker

[![CI](https://github.com/Deon-JBW/job-application-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/Deon-JBW/job-application-tracker/actions/workflows/ci.yml)

A small local app I use to keep track of internship applications: where I applied,
what stage each one is at, when to follow up, and a CSV export when I want to look at
the numbers somewhere else.

I built it with Streamlit and SQLite because I wanted something I could run in one
command, with my data staying on my own machine instead of in someone else's spreadsheet.

## What it does

- Add an application (company, role, link, status, applied date, follow-up date, notes)
- Filter by status and see counts for Applied / Interviewing / Offer / Rejected
- Update a status or delete an entry
- Export everything to CSV

## Run it

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The database (`applications.db`) is created on first run and is git-ignored, so
personal data never gets committed. Set `TRACKER_DB` to store it somewhere else.

## How it's put together

```
app.py              Streamlit UI only
tracker/db.py       SQLite access: schema, migration, CRUD, counts
tracker/export.py   Rows -> DataFrame -> CSV
tests/              pytest suite (database layer + headless UI tests)
```

The first version had the SQL mixed into the UI script, which meant the only way to
test it was to click around. Pulling the data layer into `tracker/` made it testable
without a browser, and writing those tests surfaced two bugs I hadn't noticed:

1. **CSV export crashed once any application existed.** The export listed 7 column
   names for an 8-column table. With an empty database it looked fine, which is
   exactly why it slipped through.
2. **Notes and follow-up dates could swap places.** Older databases got the
   `follow_up_date` column appended at the end by a migration, but the UI unpacked
   `SELECT *` as if it sat before `notes`. Queries now name their columns
   explicitly, so the layout on disk no longer matters.

Both have regression tests (`test_csv_export_with_rows`,
`test_migrated_database_keeps_columns_aligned`).

## Tests

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -v
```

`tests/test_app.py` drives the real page with Streamlit's `AppTest`: it fills in the
form, clicks **Add**, and checks the database. GitHub Actions runs lint and the full
suite on Python 3.11–3.13 for every push and pull request.

## What I'd add next

- Edit fields other than status
- A "follow-ups due this week" view
- Response-rate stats by role type
