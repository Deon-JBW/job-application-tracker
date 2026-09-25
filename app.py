import os
from datetime import date

import streamlit as st

from tracker import db
from tracker.export import to_csv_bytes

DB_PATH = os.environ.get("TRACKER_DB", "applications.db")

# ---- UI ----
st.set_page_config(page_title="Job Application Tracker", layout="wide")
db.init_db(DB_PATH)

st.title("📌 Job Application Tracker")

statuses = db.STATUSES
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Add an application")
    company = st.text_input("Company *")
    role = st.text_input("Role *")
    link = st.text_input("Job link (optional)")
    status = st.selectbox("Status", statuses, index=0)
    applied_date = st.date_input("Applied date", value=date.today())
    follow_up_date = st.date_input("Follow-up date (optional)", value=None)
    notes = st.text_area("Notes (optional)")

    if st.button("Add"):
        if not company.strip() or not role.strip():
            st.error("Company and Role are required.")
        else:
            db.add_application(
                DB_PATH,
                company.strip(),
                role.strip(),
                link.strip(),
                status,
                str(applied_date),
                str(follow_up_date) if follow_up_date else None,
                notes.strip(),
            )
            st.success("Application added!")
            st.rerun()

with col2:
    st.subheader("Filter & stats")
    status_filter = st.selectbox("Show", ["All"] + statuses)

    counts = db.count_by_status(DB_PATH)
    st.write("**Totals:**")
    st.write(f"- Total: {counts['Total']}")
    st.write(f"- Applied: {counts['Applied']}")
    st.write(f"- Interviewing: {counts['Interviewing']}")
    st.write(f"- Offers: {counts['Offer']}")
    st.write(f"- Rejected: {counts['Rejected']}")

st.divider()
st.subheader("Your applications")

# Export all applications (ignores filters) to CSV
st.download_button(
    label="⬇️ Export to CSV",
    data=to_csv_bytes(db.get_applications(DB_PATH)),
    file_name="job_applications.csv",
    mime="text/csv",
)

apps = db.get_applications(DB_PATH, status_filter)

if not apps:
    st.info("No applications yet. Add one above.")
else:
    for row in apps:
        app_id, company, role, link, status, applied_date, follow_up_date, notes = row

        with st.expander(f"{company} — {role} | {status} | {applied_date}"):
            st.write(f"**Link:** {link if link else '—'}")
            st.write(f"**Notes:** {notes if notes else '—'}")
            st.write(f"**Follow-up date:** {follow_up_date if follow_up_date else '—'}")

            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                new_status = st.selectbox(
                    f"Update status (ID {app_id})",
                    statuses,
                    index=statuses.index(status),
                    key=f"status_{app_id}",
                )
                if st.button("Save status", key=f"save_{app_id}"):
                    db.update_status(DB_PATH, app_id, new_status)
                    st.success("Status updated.")
                    st.rerun()

            with c2:
                if st.button("Delete", key=f"del_{app_id}"):
                    db.delete_application(DB_PATH, app_id)
                    st.warning("Deleted.")
                    st.rerun()
