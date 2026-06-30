import streamlit as st
from datetime import date, timedelta
from core.config import get_settings
from core.database import get_db
from core.models import WatchlistEntry
from core.recreation_gov import (
    search_by_name,
    search_by_park,
    search_by_facility_id,
    search_by_rec_area_id,
    search_by_state,
    get_site_types,
)

settings = get_settings()

_US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

_MODES = ["Campground Name", "Park / Rec Area", "Park / Rec Area ID", "Facility ID", "State"]

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def page():
    st.title("Search Campgrounds")

    if not settings.ridb_api_key:
        st.warning(
            "**RIDB API key not configured** — search is disabled. "
            "Get a free key at [ridb.recreation.gov/apikeys](https://ridb.recreation.gov/apikeys) "
            "and add `RIDB_API_KEY=your_key` to your `.env` file.",
            icon="⚠️",
        )
        return

    mode = st.radio("Search by", _MODES, horizontal=True, label_visibility="collapsed")

    value, ready = _search_input(mode)
    if not ready:
        return

    cache_key = f"search_{mode}_{value.strip().lower()}"
    if cache_key not in st.session_state:
        with st.spinner("Searching Recreation.gov…"):
            try:
                st.session_state[cache_key] = _run_search(mode, value.strip())
            except Exception as exc:
                st.error(f"Search failed: {exc}", icon="❌")
                return

    results: list[dict] = st.session_state[cache_key]

    if not results:
        st.info("No campgrounds found.")
        return

    st.caption(f"{len(results)} result{'s' if len(results) != 1 else ''}")
    _render_results(results)


def _search_input(mode: str) -> tuple[str, bool]:
    if mode == "Campground Name":
        value = st.text_input("Campground name", placeholder="e.g. Upper Pines", label_visibility="collapsed")
        return value, bool(value and len(value.strip()) >= 2)

    if mode == "Park / Rec Area":
        value = st.text_input("Park or recreation area", placeholder="e.g. Yosemite, Glacier, Grand Teton", label_visibility="collapsed")
        return value, bool(value and len(value.strip()) >= 2)

    if mode == "Park / Rec Area ID":
        value = st.text_input("Park or Rec Area ID", placeholder="e.g. 2991 (Yosemite)", label_visibility="collapsed")
        ready = bool(value and value.strip().isdigit())
        if value and not ready:
            st.caption("Enter a numeric rec area ID.")
        return value, ready

    if mode == "Facility ID":
        value = st.text_input("Facility ID", placeholder="e.g. 232447", label_visibility="collapsed")
        ready = bool(value and value.strip().isdigit())
        if value and not ready:
            st.caption("Enter a numeric facility ID.")
        return value, ready

    if mode == "State":
        state_name = st.selectbox(
            "State",
            options=list(_US_STATES.values()),
            index=None,
            placeholder="Select a state…",
            label_visibility="collapsed",
        )
        if state_name is None:
            return "", False
        code = next(k for k, v in _US_STATES.items() if v == state_name)
        return code, True

    return "", False


def _run_search(mode: str, value: str) -> list[dict]:
    if mode == "Campground Name":
        return search_by_name(value)
    if mode == "Park / Rec Area":
        return search_by_park(value)
    if mode == "Park / Rec Area ID":
        return search_by_rec_area_id(value)
    if mode == "Facility ID":
        return search_by_facility_id(value)
    if mode == "State":
        return search_by_state(value)
    return []


def _render_results(results: list[dict]) -> None:
    for i, cg in enumerate(results):
        with st.container(border=True):
            left, right = st.columns([4, 1])

            with left:
                location = ", ".join(filter(None, [cg["city"], cg["state"]]))
                st.markdown(f"**{cg['facility_name']}**")
                meta = "  ·  ".join(filter(None, [cg["parent_name"], location, f"ID: {cg['facility_id']}"]))
                if meta:
                    st.caption(meta)
                if cg["description"]:
                    st.caption(cg["description"][:180])

            with right:
                if st.button("Watch", key=f"watch_{i}", use_container_width=True, type="primary"):
                    st.session_state[f"show_form_{i}"] = True

        if st.session_state.get(f"show_form_{i}"):
            site_type_key = f"site_types_{cg['facility_id']}"
            if site_type_key not in st.session_state:
                with st.spinner("Loading site types…"):
                    st.session_state[site_type_key] = get_site_types(cg["facility_id"])
            site_type_map: dict[str, int] = st.session_state[site_type_key]

            with st.form(key=f"form_{i}", border=True):
                st.markdown(f"**Add *{cg['facility_name']}* to watchlist**")

                c1, c2 = st.columns(2)
                start = c1.date_input("Start date", value=date.today() + timedelta(days=7), key=f"s_{i}")
                end = c2.date_input("End date", value=date.today() + timedelta(days=14), key=f"e_{i}")
                c3, c4 = st.columns(2)
                checkin_day_names = c3.multiselect(
                    "Check-in day (optional)",
                    options=_DAYS,
                    key=f"ci_{i}",
                )
                checkout_day_names = c4.multiselect(
                    "Check-out day (optional)",
                    options=_DAYS,
                    key=f"co_{i}",
                )

                check_in_day = ",".join(str(_DAYS.index(d)) for d in checkin_day_names) or None
                check_out_day = ",".join(str(_DAYS.index(d)) for d in checkout_day_names) or None

                c5, c6, c7 = st.columns(3)
                min_nights = c5.number_input(
                    "Min nights",
                    min_value=1,
                    value=1,
                    key=f"n_{i}",
                )
                max_nights = c6.number_input(
                    "Max nights (0 = any)",
                    min_value=0,
                    value=0,
                    key=f"mx_{i}",
                )
                if site_type_map:
                    selected_types = c7.multiselect(
                        "Site types (optional)",
                        options=list(site_type_map.keys()),
                        format_func=lambda t: f"{t}  ({site_type_map[t]})",
                        key=f"t_{i}",
                    )
                    site_types = ",".join(selected_types)
                else:
                    site_types = c7.text_input(
                        "Site type filter (optional)",
                        placeholder="e.g. STANDARD ELECTRIC",
                        key=f"t_{i}",
                    )

                submitted = st.form_submit_button("Add to Watchlist", type="primary")
                if submitted:
                    if end <= start:
                        st.error("End date must be after start date.")
                    else:
                        with get_db() as db:
                            db.add(
                                WatchlistEntry(
                                    campground_id=cg["facility_id"],
                                    campground_name=cg["facility_name"],
                                    park_name=cg["parent_name"] or cg["facility_name"],
                                    start_date=start,
                                    end_date=end,
                                    min_nights=int(min_nights),
                                    max_nights=int(max_nights) if max_nights > 0 else None,
                                    site_types=site_types.strip(),
                                    check_in_day=check_in_day,
                                    check_out_day=check_out_day,
                                )
                            )
                            db.commit()
                        st.success(f"Added **{cg['facility_name']}** to your watchlist!")
                        del st.session_state[f"show_form_{i}"]
                        st.rerun()


page()
