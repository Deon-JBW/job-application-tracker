"""End-to-end checks of the Streamlit page using Streamlit's headless AppTest."""

import pytest
from streamlit.testing.v1 import AppTest

from tracker import db


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("TRACKER_DB", str(tmp_path / "ui.db"))
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception
    return at, tmp_path / "ui.db"


def test_empty_state(app):
    at, _ = app
    assert "No applications yet" in at.info[0].value


def test_add_application_through_form(app):
    at, db_path = app
    at.text_input[0].input("Acme")        # Company
    at.text_input[1].input("ML Intern")   # Role
    at.button[0].click().run()            # Add
    assert not at.exception

    rows = db.get_applications(db_path)
    assert [(r[1], r[2]) for r in rows] == [("Acme", "ML Intern")]
    # The page re-renders with the new row and a working CSV export.
    assert any("Acme — ML Intern" in e.label for e in at.expander)


def test_required_fields_are_enforced(app):
    at, db_path = app
    at.button[0].click().run()
    assert at.error[0].value == "Company and Role are required."
    assert db.get_applications(db_path) == []
