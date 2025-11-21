# Pyrenees Mountain Weather Forecast

Real-time elevation-specific weather forecasts for Spanish Pyrenees peaks. Designed for mountaineers, hikers, and mountain guides who need base-to-summit weather differentials for trip planning.

## Quick Start

**Prerequisites:** Python 3.9+

```bash
git clone <your-repo-url>
cd Pyrenees_Forecast
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux: use .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open: http://localhost:8000

## Technology Stack

- **Backend:** FastAPI 0.104.1, SQLAlchemy 2.0.23, SQLite (aiosqlite 0.19.0)
- **Frontend:** HTML/CSS/JavaScript (ES6), Chart.js 4.4.0
- **External API:** Open-Meteo (free weather data)

## Project Structure

```
Pyrenees_Forecast/
├── app/
│   ├── main.py              # FastAPI app, 9 REST endpoints
│   ├── models.py            # Database models
│   ├── db.py                # Database config
│   ├── weather.py           # Weather API integration
│   └── catalog/
│       └── spanish_pyrenees.json
├── public/
│   ├── index.html
│   └── app.js
├── requirements.txt
├── test_api.py
└── README.md
```

## Database Setup

SQLite database auto-creates at `./app.db` on first run.

**To reset:**
```bash
rm app.db
uvicorn app.main:app --reload
```

## API Endpoints

**Catalog:**
- `GET /api/catalog/areas` - List regions
- `GET /api/catalog/massifs?area={id}` - List mountain ranges
- `GET /api/catalog/peaks?area={id}&massif={id}` - List peaks
- `GET /api/catalog/peaks_all?q={query}` - Search all peaks
- `GET /api/catalog/peaks/{id}` - Peak details

**User Mountains:**
- `GET /api/my/mountains` - Get saved list
- `POST /api/my/mountains/{id}` - Add mountain
- `DELETE /api/my/mountains/{id}` - Remove mountain

**Weather:**
- `GET /api/weather/{id}?band={base|mid|summit}` - 24-hour forecast

**Example:**
```bash
curl "http://localhost:8000/api/catalog/peaks_all?q=aneto"
curl -X POST http://localhost:8000/api/my/mountains/aneto
curl "http://localhost:8000/api/weather/aneto?band=summit"
```

## Features

- Browse 50+ Pyrenees peaks by region/massif
- Global search across peak names
- Personal mountain list (persisted in SQLite)
- 24-hour forecasts at 3 elevations (base/mid/summit)
- Temperature, wind, precipitation, snow likelihood
- Advanced modal with interactive charts and statistics
- 60-minute weather cache (80%+ API call reduction)

## Testing

```bash
python test_api.py
```

**Manual test:** Open http://localhost:8000, search "aneto", add to list, view weather, click "Advanced Weather"

## Troubleshooting

**Port in use:** `uvicorn app.main:app --reload --port 8001`

**Modules not found:** Verify venv active with `which python`, reinstall with `pip install -r requirements.txt`

**Weather not loading:** Check internet connection, verify `curl http://localhost:8000/api/catalog/areas` works

## Known Limitations

- Single-user only (no authentication)
- SQLite not suitable for >100 concurrent users
- No automated unit tests (manual testing only)
- Local deployment only (no production config)

## Future Work

- User authentication and multi-user support
- PostgreSQL migration for scalability
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Automated pytest suite
- Weather alerts for dangerous conditions

Repository: <https://github.com/Wilyam390/Pyrenees_forecast>
