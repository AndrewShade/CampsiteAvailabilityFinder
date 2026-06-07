import streamlit as st
from core.config import get_settings
from core.database import get_db
from core.models import NotificationWebhook

settings = get_settings()


def page():
    st.title("Settings")

    # Status
    st.subheader("Status")
    c1, c2 = st.columns(2)
    with c1:
        if settings.ridb_api_key:
            st.success("RIDB API key configured", icon="✅")
        else:
            st.warning(
                "RIDB API key not set — search disabled. "
                "Get a free key at [ridb.recreation.gov/apikeys](https://ridb.recreation.gov/apikeys).",
                icon="⚠️",
            )
    with c2:
        st.info(f"Polling every **{settings.check_interval_minutes} minutes**", icon="🕐")

    st.divider()

    # Webhooks list
    st.subheader("Notification Webhooks")
    st.caption("Get notified in Discord, Slack, or any service that accepts a webhook URL.")

    with get_db() as db:
        webhooks = [
            {"id": w.id, "name": w.name, "type": w.webhook_type, "url": w.url, "enabled": w.enabled}
            for w in db.query(NotificationWebhook).order_by(NotificationWebhook.created_at).all()
        ]

    if not webhooks:
        st.info("No webhooks yet. Add one below.")
    else:
        for wh in webhooks:
            with st.container(border=True):
                left, right = st.columns([3, 2])
                with left:
                    st.markdown(f"**{wh['name']}** · {wh['type'].capitalize()}")
                    display_url = wh["url"][:55] + ("…" if len(wh["url"]) > 55 else "")
                    st.caption(display_url)
                with right:
                    tc, dc = st.columns(2)
                    new_state = tc.toggle("On", value=wh["enabled"], key=f"tog_{wh['id']}")
                    if new_state != wh["enabled"]:
                        with get_db() as db:
                            w = db.get(NotificationWebhook, wh["id"])
                            w.enabled = new_state
                            db.commit()
                        st.rerun()
                    if dc.button("Delete", key=f"del_{wh['id']}", type="secondary", use_container_width=True):
                        with get_db() as db:
                            w = db.get(NotificationWebhook, wh["id"])
                            db.delete(w)
                            db.commit()
                        st.rerun()

    # Add webhook
    st.divider()
    st.markdown("**Add a webhook**")
    with st.form("add_webhook"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", placeholder="My Discord server")
        wtype = c2.selectbox("Type", ["discord", "slack", "generic"])
        url = st.text_input("Webhook URL", placeholder="https://discord.com/api/webhooks/…")

        if st.form_submit_button("Add Webhook", type="primary"):
            if not name.strip() or not url.strip():
                st.error("Name and URL are required.")
            elif not url.startswith("http"):
                st.error("URL must start with http:// or https://")
            else:
                with get_db() as db:
                    db.add(NotificationWebhook(name=name.strip(), webhook_type=wtype, url=url.strip()))
                    db.commit()
                st.success(f"Added **{name}**!")
                st.rerun()


page()
