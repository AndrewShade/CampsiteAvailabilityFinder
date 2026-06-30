import json
from datetime import date, timedelta, timezone
from zoneinfo import ZoneInfo
import streamlit as st
from sqlalchemy.orm import selectinload
from core.config import get_settings
from core.database import get_db
from core.models import WatchlistEntry, AvailabilityResult
from core.availability import check_entry
from core.notifications import send_notifications
from core.recreation_gov import get_site_types

_tz = ZoneInfo(get_settings().timezone)
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _fmt_dt(dt) -> str:
    if not dt:
        return ""
    return dt.replace(tzinfo=timezone.utc).astimezone(_tz).strftime("%b %d %I:%M %p")


def _parse_days(value) -> list[str]:
    if value is None:
        return []
    return [_DAYS[int(d)] for d in str(value).split(",") if str(d).strip().isdigit()]


def page():
    st.title("Dashboard")

    entries = _load_entries()

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
    eid = entry["id"]
    status = entry["status"]
    status_icon = {"watching": "🔵", "found": "🟢", "paused": "⚫"}.get(status, "⚫")

    with st.container(border=True):
        header, actions = st.columns([3, 2])

        with header:
            st.markdown(f"#### {status_icon} {entry['campground_name']}")
            parts = [entry["park_name"], f"{entry['start_date']} → {entry['end_date']}"]
            nights_label = f"Min {entry['min_nights']}"
            if entry.get("max_nights"):
                nights_label += f"–{entry['max_nights']}"
            nights_label += f" night{'s' if entry['min_nights'] != 1 or entry.get('max_nights') else ''}"
            parts.append(nights_label)
            if entry["site_types"]:
                parts.append(f"Types: {entry['site_types']}")
            ci = _parse_days(entry.get("check_in_day"))
            co = _parse_days(entry.get("check_out_day"))
            if ci:
                parts.append(f"Check-in: {'/'.join(ci)}")
            if co:
                parts.append(f"Check-out: {'/'.join(co)}")
            if entry["last_checked"]:
                parts.append(f"*Checked {_fmt_dt(entry['last_checked'])}*")
            st.caption("  ·  ".join(parts))

        with actions:
            c1, c2, c3, c4 = st.columns(4)

            if c1.button("Check", key=f"check_{eid}", use_container_width=True):
                with st.spinner(f"Checking {entry['campground_name']}…"):
                    with get_db() as db:
                        e = db.get(WatchlistEntry, eid)
                        check_entry(e, db)
                        all_results = db.query(AvailabilityResult).filter_by(entry_id=eid).all()
                        if all_results:
                            for r in all_results:
                                r.notification_sent = False
                            db.commit()
                            send_notifications(e, all_results, db)
                            st.toast(f"Found {len(all_results)} available site(s)!", icon="🎉")
                        else:
                            st.toast("No availability found.", icon="ℹ️")
                st.rerun()

            if c2.button("Edit", key=f"edit_btn_{eid}", use_container_width=True):
                st.session_state[f"edit_{eid}"] = not st.session_state.get(f"edit_{eid}", False)
                st.rerun()

            is_paused = status == "paused"
            if c3.button("Resume" if is_paused else "Pause", key=f"toggle_{eid}", use_container_width=True):
                with get_db() as db:
                    e = db.get(WatchlistEntry, eid)
                    e.status = "watching" if is_paused else "paused"
                    db.commit()
                st.rerun()

            if c4.button("Remove", key=f"del_{eid}", use_container_width=True, type="secondary"):
                with get_db() as db:
                    e = db.get(WatchlistEntry, eid)
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

    if st.session_state.get(f"edit_{eid}"):
        _render_edit_form(entry)


def _render_edit_form(entry: dict):
    eid = entry["id"]
    cid = entry["campground_id"]

    site_type_key = f"site_types_{cid}"
    if site_type_key not in st.session_state:
        with st.spinner("Loading site types…"):
            st.session_state[site_type_key] = get_site_types(cid)
    site_type_map: dict[str, int] = st.session_state[site_type_key]

    current_site_types = [t.strip() for t in (entry["site_types"] or "").split(",") if t.strip()]
    current_ci = _parse_days(entry.get("check_in_day"))
    current_co = _parse_days(entry.get("check_out_day"))

    with st.form(key=f"edit_form_{eid}", border=True):
        st.markdown(f"**Edit — {entry['campground_name']}**")

        c1, c2 = st.columns(2)
        start = c1.date_input("Start date", value=entry["start_date"], key=f"es_{eid}")
        end = c2.date_input("End date", value=entry["end_date"], key=f"ee_{eid}")

        c3, c4 = st.columns(2)
        checkin_day_names = c3.multiselect("Check-in day", options=_DAYS, default=current_ci, key=f"eci_{eid}")
        checkout_day_names = c4.multiselect("Check-out day", options=_DAYS, default=current_co, key=f"eco_{eid}")

        c5, c6, c7 = st.columns(3)
        min_nights = c5.number_input("Min nights", min_value=1, value=entry["min_nights"], key=f"en_{eid}")
        max_nights = c6.number_input(
            "Max nights (0 = any)",
            min_value=0,
            value=entry.get("max_nights") or 0,
            key=f"emx_{eid}",
        )

        if site_type_map:
            valid_defaults = [t for t in current_site_types if t in site_type_map]
            selected_types = c7.multiselect(
                "Site types",
                options=list(site_type_map.keys()),
                default=valid_defaults,
                format_func=lambda t: f"{t}  ({site_type_map[t]})",
                key=f"et_{eid}",
            )
            site_types_str = ",".join(selected_types)
        else:
            site_types_str = c7.text_input("Site types", value=entry["site_types"] or "", key=f"et_{eid}")

        cs, cc = st.columns(2)
        save = cs.form_submit_button("Save", type="primary", use_container_width=True)
        cancel = cc.form_submit_button("Cancel", use_container_width=True)

        if cancel:
            del st.session_state[f"edit_{eid}"]
            st.rerun()

        if save:
            if end <= start:
                st.error("End date must be after start date.")
            else:
                check_in_day = ",".join(str(_DAYS.index(d)) for d in checkin_day_names) or None
                check_out_day = ",".join(str(_DAYS.index(d)) for d in checkout_day_names) or None
                with get_db() as db:
                    e = db.get(WatchlistEntry, eid)
                    e.start_date = start
                    e.end_date = end
                    e.min_nights = int(min_nights)
                    e.max_nights = int(max_nights) if max_nights > 0 else None
                    e.site_types = site_types_str
                    e.check_in_day = check_in_day
                    e.check_out_day = check_out_day
                    e.status = "watching"
                    db.commit()
                del st.session_state[f"edit_{eid}"]
                st.rerun()


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
                "max_nights": e.max_nights,
                "site_types": e.site_types,
                "check_in_day": e.check_in_day,
                "check_out_day": e.check_out_day,
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
