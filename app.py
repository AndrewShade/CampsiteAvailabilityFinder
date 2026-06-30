import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Campsite Availability Finder",
    page_icon="⛺",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def startup():
    """Runs once across all sessions — initializes DB and starts the background scheduler."""
    from core.config import get_settings
    from core.database import init_db, get_db
    from core.models import NotificationWebhook
    from core.scheduler import get_scheduler

    Path("data").mkdir(exist_ok=True)
    init_db()

    cfg = get_settings()
    if cfg.discord_webhook_url:
        with get_db() as db:
            exists = db.query(NotificationWebhook).filter_by(url=cfg.discord_webhook_url).first()
            if not exists:
                db.add(NotificationWebhook(
                    name="Discord",
                    webhook_type="discord",
                    url=cfg.discord_webhook_url,
                ))
                db.commit()

    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()


startup()

dashboard = st.Page("views/dashboard.py", title="Dashboard", icon="📊", default=True)
search = st.Page("views/search.py", title="Search", icon="🔍")
settings = st.Page("views/settings.py", title="Settings", icon="⚙️")

pg = st.navigation(
    {"Monitor": [dashboard, search], "Configure": [settings]},
    position="sidebar",
)
pg.run()
