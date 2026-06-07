import streamlit as st
from datetime import date, timedelta
from core.config import get_settings
from core.database import get_db
from core.models import WatchlistEntry
from core.recreation_gov import search_campgrounds

settings = get_settings()


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

    query = st.text_input(
        "Search",
        placeholder="Park or campground name — e.g. Yosemite, Glacier, Grand Teton",
        label_visibility="collapsed",
    )

    if not query or len(query.strip()) < 2:
        st.caption("Type at least 2 characters to search.")
        return

    # Cache results so they survive a rerun (e.g. after adding to watchlist)
    cache_key = f"search_results_{query.strip().lower()}"
    if cache_key not in st.session_state:
        with st.spinner("Searching Recreation.gov…"):
            try:
                st.session_state[cache_key] = search_campgrounds(query.strip())
            except Exception as exc:
                st.error(f"Search failed: {exc}", icon="❌")
                return

    results: list[dict] = st.session_state[cache_key]

    if not results:
        st.info(f"No campgrounds found for **{query}**.")
        return

    st.caption(f"{len(results)} result{'s' if len(results) != 1 else ''}")

    for i, cg in enumerate(results):
        with st.container(border=True):
            left, right = st.columns([4, 1])

            with left:
                location = ", ".join(filter(None, [cg["city"], cg["state"]]))
                st.markdown(f"**{cg['facility_name']}**")
                meta = "  ·  ".join(filter(None, [cg["parent_name"], location]))
                if meta:
                    st.caption(meta)
                if cg["description"]:
                    st.caption(cg["description"][:180])

            with right:
                if st.button("Watch", key=f"watch_{i}", use_container_width=True, type="primary"):
                    st.session_state[f"show_form_{i}"] = True

        if st.session_state.get(f"show_form_{i}"):
            with st.form(key=f"form_{i}", border=True):
                st.markdown(f"**Add *{cg['facility_name']}* to watchlist**")

                c1, c2 = st.columns(2)
                start = c1.date_input(
                    "Start date", value=date.today() + timedelta(days=7), key=f"s_{i}"
                )
                end = c2.date_input(
                    "End date", value=date.today() + timedelta(days=14), key=f"e_{i}"
                )
                c3, c4 = st.columns(2)
                min_nights = c3.number_input("Min consecutive nights", min_value=1, value=1, key=f"n_{i}")
                site_types = c4.text_input(
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
                                    site_types=site_types.strip(),
                                )
                            )
                            db.commit()
                        st.success(f"Added **{cg['facility_name']}** to your watchlist!")
                        del st.session_state[f"show_form_{i}"]
                        st.rerun()


page()
