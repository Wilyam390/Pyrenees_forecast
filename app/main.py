# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sqlalchemy import select, insert, delete, update
from sqlalchemy.exc import IntegrityError

from .db import engine, Base, get_session
from .models import MyMountain, WeatherCache
from .weather import fetch_hourly, slice_next_24h

import json
import pathlib
import datetime

app = FastAPI(title="Pyrenees Mountain Weather")

# ---------- Load hierarchical catalog (Area -> Massif -> Peaks) ----------
CATALOG_PATH = pathlib.Path(__file__).resolve().parents[0] / "catalog" / "spanish_pyrenees.json"
with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    RAW = json.load(f)

AREAS = RAW["areas"]

def iter_peaks():
    for area in AREAS:
        for massif in area["massifs"]:
            for peak in massif["peaks"]:
                yield area, massif, peak

# Flat lookup by peak id (used by /api/my/* and /api/weather/*)
PEAK_BY_ID = {p["id"]: p for _, _, p in iter_peaks()}

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---------- Catalog drill-down & search ----------
@app.get("/api/catalog/areas")
def list_areas():
    return [{"id": a["id"], "name": a["name"]} for a in AREAS]

@app.get("/api/catalog/massifs")
def list_massifs(area: str):
    for a in AREAS:
        if a["id"] == area:
            return [{"id": m["id"], "name": m["name"]} for m in a["massifs"]]
    raise HTTPException(404, "Unknown area")

@app.get("/api/catalog/peaks")
def list_peaks(area: str, massif: str, q: str | None = None):
    for a in AREAS:
        if a["id"] == area:
            for m in a["massifs"]:
                if m["id"] == massif:
                    items = m["peaks"]
                    if q:
                        qn = q.lower()
                        items = [p for p in items if qn in p["name"].lower()]
                    return items
    raise HTTPException(404, "Unknown area/massif")

@app.get("/api/catalog/peaks_all")
def list_peaks_all(q: str | None = None):
    items = [p for _, _, p in iter_peaks()]
    if q:
        qn = q.lower()
        items = [p for p in items if qn in p["name"].lower() or qn in p.get("massif", "").lower()]
    return [
        {"id": p["id"], "name": p["name"], "summit_elev_m": p["summit_elev_m"], "massif": p.get("massif")}
        for p in items
    ]

@app.get("/api/catalog/peaks/{peak_id}")
def peak_details(peak_id: str):
    p = PEAK_BY_ID.get(peak_id)
    if not p:
        raise HTTPException(404, "Unknown peak")
    return p
