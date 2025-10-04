# Pyrenees Mountain Weather Forecast

A weather dashboard for Spanish Pyrenees mountains using FastAPI and Open-Meteo API.

## Setup Instructions

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `uvicorn app.main:app --reload`
6. Open: http://localhost:8000

## Features
- Browse Spanish Pyrenees peaks by area and massif
- Search peaks globally
- Add mountains to personal list
- View 24-hour weather forecasts at different elevations
- Weather caching to reduce API calls