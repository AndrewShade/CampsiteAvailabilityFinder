# Campsite Availability Finder

A self-hosted Python app that monitors [Recreation.gov](https://www.recreation.gov) campgrounds and fires a **Discord notification** the moment a site opens up on your target dates.

Built with **Streamlit** and **SQLite** — runs anywhere Python is installed with a single command.

---

## Features

- **Live availability polling** — background scheduler checks Recreation.gov on a configurable interval (default: 15 min)
- **Flexible watchlist filters** — date range, min/max consecutive nights, site type, check-in day, check-out day
- **Multi-mode campground search** — search by campground name, park/rec area name, park/rec area ID, facility ID, or state
- **Discord notifications** — grouped by site type and date window; one message per unique availability window instead of one per site
- **Smart deduplication** — notifications reset nightly so you get a fresh alert each morning but no spam during the day
- **Manual check** — trigger an immediate re-check for any watchlist entry from the dashboard
- **Edit in place** — update filters on any watchlist entry without recreating it
- **Pause / resume** — suspend monitoring without losing your entry
- **Direct booking link** — every result links straight to the Recreation.gov booking page
- **Timezone support** — configure your local timezone via `.env`
- **Rate limiting** — global 45 req/min throttle to stay safely within Recreation.gov API limits

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
CHECK_INTERVAL_MINUTES=60
TIMEZONE=America/New_York            # any tz database name, e.g. America/Los_Angeles
```

**Getting an RIDB API key:** Register at [ridb.recreation.gov/apikeys](https://ridb.recreation.gov/apikeys) — it's free.

**Getting a Discord webhook URL:** In any Discord channel → Edit Channel → Integrations → Webhooks → New Webhook → Copy URL.

The app auto-seeds the Discord webhook from `DISCORD_WEBHOOK_URL` on first startup, so you don't need to add it through the Settings page.

### 3. Run

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Deploying on a home server (Proxmox, Raspberry Pi, etc.)

```bash
pip install -r requirements.txt

# Run in the background
nohup streamlit run app.py --server.headless true &
```

To update, `git pull` from the repo directory — your `.env` and database are not tracked by git and will be untouched.

---

## Project Structure

```
├── app.py                  # Streamlit entry point, startup, navigation
├── core/
│   ├── config.py           # Settings loaded from .env
│   ├── database.py         # SQLAlchemy + SQLite setup, schema migrations
│   ├── models.py           # ORM models (WatchlistEntry, AvailabilityResult, Webhook)
│   ├── recreation_gov.py   # RIDB + availability API client, rate limiter
│   ├── availability.py     # Availability check, consecutive-night and day-of-week logic
│   ├── notifications.py    # Discord / Slack / generic webhook dispatch
│   └── scheduler.py        # APScheduler background jobs
├── views/
│   ├── dashboard.py        # Watchlist with check / edit / pause / delete
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
