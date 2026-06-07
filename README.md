# Campsite Availability Finder

A self-hosted web application that monitors [Recreation.gov](https://www.recreation.gov) campgrounds and sends instant webhook notifications the moment a site becomes available on your target dates.

Built with **FastAPI**, **React**, and **Docker** — designed to run on a home server or Proxmox container.

![Dashboard screenshot](docs/screenshot-dashboard.png)

---

## Features

- **Live availability polling** — background scheduler hits the Recreation.gov API on a configurable interval (default: 15 min)
- **Smart watchlist** — specify campground, date range, minimum consecutive nights, and optional site-type filter
- **Instant notifications** — send rich alerts to Discord, Slack, or any generic webhook URL
- **One-click force check** — manually trigger a check for any watchlist entry from the dashboard
- **Pause/resume** — suspend monitoring without deleting the entry
- **Direct booking link** — every found site includes a deep link straight to the Recreation.gov booking page
- **Fully containerized** — single `docker compose up` deployment; SQLite database persisted via Docker volume

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.12 · FastAPI · SQLAlchemy · APScheduler |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · TanStack Query |
| Persistence | SQLite (file-based, zero-config) |
| Deployment | Docker · Docker Compose · nginx reverse proxy |
| Data source | Recreation.gov RIDB API + availability API |

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- A free **RIDB API key** from [ridb.recreation.gov/apikeys](https://ridb.recreation.gov/apikeys) (required for campground search)

### 1. Clone and configure

```bash
git clone https://github.com/AndrewShade/CampsiteAvailabilityFinder.git
cd CampsiteAvailabilityFinder
cp .env.example .env
```

Edit `.env` and set your RIDB API key:

```env
RIDB_API_KEY=your_key_here
CHECK_INTERVAL_MINUTES=15
```

### 2. Build and run

```bash
docker compose up --build -d
```

The app is available at **http://localhost:3000**

### 3. Add campgrounds to your watchlist

1. Go to **Search** and search for a campground by name (e.g. "Yosemite Valley")
2. Click **Watch**, set your desired date range and minimum nights
3. Return to **Dashboard** to monitor availability in real time

### 4. Configure notifications (optional)

Go to **Settings → Webhooks** and add a Discord or Slack webhook URL. The app will post a rich notification the moment a site is found.

---

## Deployment on Proxmox

1. Create an LXC container or VM with Docker installed
2. Clone the repo and follow the steps above
3. Update `ALLOWED_ORIGINS` in `.env` with your container's IP
4. Optionally add the container to a reverse proxy (Nginx Proxy Manager, Traefik) for HTTPS

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── routers/             # API route handlers
│   │   └── services/
│   │       ├── recreation_gov.py  # Recreation.gov API client
│   │       ├── availability.py    # Availability check logic
│   │       ├── notifications.py   # Webhook dispatch
│   │       └── scheduler.py       # APScheduler background job
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # Dashboard, Search, Settings
│   │   ├── components/          # WatchlistCard, SearchResult, etc.
│   │   ├── api/client.ts        # Type-safe API client
│   │   └── types/               # Shared TypeScript interfaces
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## API Reference

The FastAPI backend exposes interactive docs at **http://localhost:8000/docs** when running.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/search?q=` | Search campgrounds via RIDB |
| `GET` | `/api/watchlist` | List all watchlist entries |
| `POST` | `/api/watchlist` | Add a campground to watchlist |
| `PATCH` | `/api/watchlist/{id}` | Update an entry (dates, status, etc.) |
| `DELETE` | `/api/watchlist/{id}` | Remove an entry |
| `POST` | `/api/watchlist/{id}/check` | Force an immediate availability check |
| `GET` | `/api/settings/webhooks` | List notification webhooks |
| `POST` | `/api/settings/webhooks` | Add a webhook |

---

## License

[MIT](LICENSE)
