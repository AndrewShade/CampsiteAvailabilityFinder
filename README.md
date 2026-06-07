# Campsite Availability Finder

A self-hosted Python app that monitors [Recreation.gov](https://www.recreation.gov) campgrounds and fires a **Discord notification** the moment a site opens up on your target dates.

Built with **Streamlit** and **SQLite** — runs anywhere Python is installed with a single command.

---

## Features

- **Live availability polling** — background scheduler checks Recreation.gov on a configurable interval (default: 15 min)
- **Watchlist** — specify campground, date range, minimum consecutive nights, and optional site-type filter
- **Discord notifications** — rich embed sent automatically when a site is found
- **Manual check** — trigger an immediate check for any entry from the dashboard
- **Pause / resume** — suspend monitoring without losing your entry
- **Direct booking link** — every result links straight to the Recreation.gov booking page

---

## Tech Stack

| | |
|---|---|
| UI | Streamlit |
| Database | SQLite via SQLAlchemy |
| Scheduling | APScheduler (background thread) |
| HTTP | httpx |
| Data source | Recreation.gov RIDB API + availability API |

---

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/AndrewShade/CampsiteAvailabilityFinder.git
cd CampsiteAvailabilityFinder

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
RIDB_API_KEY=your_key_here           # free at ridb.recreation.gov/apikeys
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
CHECK_INTERVAL_MINUTES=15
```

**Getting a Discord webhook URL:** In any Discord channel → Edit Channel → Integrations → Webhooks → New Webhook → Copy URL.

### 3. Run

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Deploying on a home server (Proxmox, Raspberry Pi, etc.)

```bash
# Install dependencies once
pip install -r requirements.txt

# Run in the background with nohup
nohup streamlit run app.py --server.headless true &

# Or add a systemd service so it starts on boot (see docs/systemd.md)
```

---

## Project Structure

```
├── app.py                  # Streamlit entry point, startup, navigation
├── core/
│   ├── config.py           # Settings from .env
│   ├── database.py         # SQLAlchemy + SQLite setup
│   ├── models.py           # ORM models (WatchlistEntry, AvailabilityResult, Webhook)
│   ├── recreation_gov.py   # Recreation.gov API client
│   ├── availability.py     # Availability check + consecutive-night logic
│   ├── notifications.py    # Discord / Slack / generic webhook dispatch
│   └── scheduler.py        # APScheduler background job
├── pages/
│   ├── dashboard.py        # Watchlist view with check / pause / delete actions
│   ├── search.py           # Campground search + add to watchlist
│   └── settings.py         # Webhook management, app status
├── .streamlit/
│   └── config.toml         # Dark theme, server config
├── requirements.txt
└── .env.example
```

---

## License

[MIT](LICENSE)
