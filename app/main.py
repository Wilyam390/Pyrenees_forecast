from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select, insert, delete, update
from sqlalchemy.exc import IntegrityError
from .db import engine, Base, get_session
from .models import MyMountain, WeatherCache
from .weather import fetch_hourly, slice_next_24h
from .config import settings
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json
import pathlib

app = FastAPI(title="Pyrenees Mountain Weather")

CATALOG_PATH = pathlib.Path(__file__).resolve().parents[0] / "catalog" / "spanish_pyrenees.json"
with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    RAW = json.load(f)

AREAS = RAW["areas"]

def iter_peaks():
    for area in AREAS:
        for massif in area["massifs"]:
            for peak in massif["peaks"]:
                yield area, massif, peak

PEAK_BY_ID = {p["id"]: p for _, _, p in iter_peaks()}

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

@app.get("/api/my/mountains")
async def my_mountains(session=Depends(get_session)):
    rows = (
        await session.execute(
            select(MyMountain).order_by(MyMountain.display_order, MyMountain.added_at)
        )
    ).scalars().all()
    return [r.mountain_id for r in rows]

@app.post("/api/my/mountains/{mountain_id}")
async def add_mountain(mountain_id: str, session=Depends(get_session)):
    if mountain_id not in PEAK_BY_ID:
        raise HTTPException(404, "Unknown peak")
    try:
        await session.execute(insert(MyMountain).values(mountain_id=mountain_id))
        await session.commit()
        return {"ok": True}
    except IntegrityError:
        await session.rollback()
        return {"ok": True, "note": "Already added"}

@app.delete("/api/my/mountains/{mountain_id}")
async def remove_mountain(mountain_id: str, session=Depends(get_session)):
    await session.execute(delete(MyMountain).where(MyMountain.mountain_id == mountain_id))
    await session.commit()
    return {"ok": True}

TTL_SECONDS = settings.WEATHER_CACHE_TTL

def is_cache_fresh(row: Optional[WeatherCache]) -> bool:
    try:
        if not row or row.fetched_at is None or row.ttl_seconds is None:
            return False
        age = (datetime.now(timezone.utc) - row.fetched_at).total_seconds()
        return age < row.ttl_seconds
    except Exception:
        return False

async def fetch_and_process_weather(lat: float, lon: float, elev_m: int) -> list[Dict[str, Any]]:
    try:
        payload = await fetch_hourly(lat, lon)
        return slice_next_24h(payload, elev_target_m=elev_m)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream weather error: {e}")

async def update_weather_cache(session, mountain_id: str, band: str, hourly_data: list[Dict[str, Any]]) -> None:
    now_utc = datetime.now(timezone.utc)
    try:
        await session.execute(
            insert(WeatherCache).values(
                mountain_id=mountain_id,
                band=band,
                payload=hourly_data,
                ttl_seconds=TTL_SECONDS,
                fetched_at=now_utc,
            )
        )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        await session.execute(
            update(WeatherCache)
            .where(
                WeatherCache.mountain_id == mountain_id,
                WeatherCache.band == band,
            )
            .values(payload=hourly_data, ttl_seconds=TTL_SECONDS, fetched_at=now_utc)
        )
        await session.commit()

@app.get("/api/weather/{mountain_id}")
async def weather_24h(mountain_id: str, band: str = "base", session=Depends(get_session)):
    m = PEAK_BY_ID.get(mountain_id)
    if not m:
        raise HTTPException(404, "Unknown peak")
    if band not in ("base", "mid", "summit"):
        raise HTTPException(400, "band must be base|mid|summit")

    b = m["bands"][band]

    row = (
        await session.execute(
            select(WeatherCache).where(
                WeatherCache.mountain_id == mountain_id,
                WeatherCache.band == band,
            )
        )
    ).scalars().first()
    
    if row and is_cache_fresh(row):
        return row.payload

    hourly_data = await fetch_and_process_weather(b["lat"], b["lon"], b["elev_m"])
    await update_weather_cache(session, mountain_id, band, hourly_data)
    
    return hourly_data

PUBLIC_DIR = pathlib.Path(__file__).resolve().parents[1] / "public"
INDEX_PATH = PUBLIC_DIR / "index.html"

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(INDEX_PATH)

app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")