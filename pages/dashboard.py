import json
import streamlit as st
from sqlalchemy.orm import selectinload
from core.database import get_db
from core.models import WatchlistEntry
from core.availability import check_entry
from core.notifications import send_notifications


def page():
    st.title("Dashboard")

    entries = _load_entries()

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(entries))
    col2.metric("Watching", sum(1 for e in entries if e["status"] == "watching"))
    col3.metric("Available 🎉", sum(1 for e in entries if e["status"] == "found"))
    col4.metric("Paused", sum(1 for e in entries if e["status"] == "paused"))

    st.divider()

    if not entries:
        st.info("No campgrounds on your watchlist yet. Head to **Search** to find some.", icon="⛺")
        return

    for entry in entries:
        _render_entry(entry)


def _render_entry(entry: dict):
    status = entry["status"]
    status_icon = {"watching": "🔵", "found": "🟢", "paused": "⚫"}.get(status, "⚫")

    with st.container(border=True):
        header, actions = st.columns([3, 2])

        with header:
            st.markdown(f"#### {status_icon} {entry['campground_name']}")
            parts = [entry["park_name"], f"{entry['start_date']} → {entry['end_date']}"]
            parts.append(f"Min {entry['min_nights']} night{'s' if entry['min_nights'] != 1 else ''}")
            if entry["site_types"]:
                parts.append(f"Types: {entry['site_types']}")
            if entry["last_checked"]:
                parts.append(f"*Checked {entry['last_checked'].strftime('%b %d %I:%M %p')}*")
            st.caption("  ·  ".join(parts))

        with actions:
            c1, c2, c3 = st.columns(3)

            if c1.button("Check", key=f"check_{entry['id']}", use_container_width=True):
                with st.spinner(f"Checking {entry['campground_name']}…"):
                    with get_db() as db:
                        e = db.get(WatchlistEntry, entry["id"])
                        new = check_entry(e, db)
                        if new:
                            send_notifications(e, new, db)
                            st.toast(f"Found {len(new)} available site(s)!", icon="🎉")
                        else:
                            st.toast("No new availability found.", icon="ℹ️")
                st.rerun()

            is_paused = status == "paused"
            if c2.button(
                "Resume" if is_paused else "Pause",
                key=f"toggle_{entry['id']}",
                use_container_width=True,
            ):
                with get_db() as db:
                    e = db.get(WatchlistEntry, entry["id"])
                    e.status = "watching" if is_paused else "paused"
                    db.commit()
                st.rerun()

            if c3.button("Remove", key=f"del_{entry['id']}", use_container_width=True, type="secondary"):
                with get_db() as db:
                    e = db.get(WatchlistEntry, entry["id"])
                    db.delete(e)
                    db.commit()
                st.rerun()

        # Available sites
        if entry["results"]:
            n = len(entry["results"])
            with st.expander(f"✅ {n} available site{'s' if n != 1 else ''} — click to view and book"):
                for result in entry["results"]:
                    dates: list[str] = json.loads(result["available_dates"])
                    span = f"{dates[0]} – {dates[-1]}" if len(dates) > 1 else dates[0]
                    nights = f"{len(dates)} night{'s' if len(dates) != 1 else ''}"

                    left, right = st.columns([3, 1])
                    with left:
                        label = f"**{result['campsite_name']}** ({result['site_type']})"
                        if result["loop"]:
                            label += f" · Loop: {result['loop']}"
                        st.markdown(label)
                        st.caption(f"📅 {span} · {nights}")
                    with right:
                        st.link_button(
                            "Book now",
                            f"https://www.recreation.gov/camping/campsites/{result['campsite_id']}",
                            use_container_width=True,
                        )


def _load_entries() -> list[dict]:
    with get_db() as db:
        rows = (
            db.query(WatchlistEntry)
            .options(selectinload(WatchlistEntry.results))
            .order_by(WatchlistEntry.created_at.desc())
            .all()
        )
        return [
            {
                "id": e.id,
                "campground_id": e.campground_id,
                "campground_name": e.campground_name,
                "park_name": e.park_name,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "min_nights": e.min_nights,
                "site_types": e.site_types,
                "status": e.status,
                "last_checked": e.last_checked,
                "results": [
                    {
                        "id": r.id,
                        "campsite_id": r.campsite_id,
                        "campsite_name": r.campsite_name,
                        "site_type": r.site_type,
                        "loop": r.loop,
                        "available_dates": r.available_dates,
                    }
                    for r in e.results
                ],
            }
            for e in rows
        ]


page()
