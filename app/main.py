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

TTL_SECONDS = 3600  # 60 minutes

def cache_fresh(row):
    try:
        if not row or row.fetched_at is None or row.ttl_seconds is None:
            return False
        age = (datetime.datetime.now(datetime.timezone.utc) - row.fetched_at).total_seconds()
        return age < row.ttl_seconds
    except Exception:
        return False

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
    if row and cache_fresh(row):
        return row.payload

    try:
        payload = await fetch_hourly(b["lat"], b["lon"])
        hourly = slice_next_24h(payload, elev_target_m=b["elev_m"])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream weather error: {e}")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    try:
        await session.execute(
            insert(WeatherCache).values(
                mountain_id=mountain_id,
                band=band,
                payload=hourly,
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
            .values(payload=hourly, ttl_seconds=TTL_SECONDS, fetched_at=now_utc)
        )
        await session.commit()

    return hourly

# ---------- Static site (mounted AFTER APIs) ----------
PUBLIC_DIR = pathlib.Path(__file__).resolve().parents[1] / "public"
INDEX_PATH = PUBLIC_DIR / "index.html"

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(INDEX_PATH)

app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

