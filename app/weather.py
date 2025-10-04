# app/weather.py
import httpx
import asyncio

LAPSE_RATE_K_PER_M = 0.0065  # 6.5°C / 1000 m
# Be polite to the upstream API; also reduces flakiness when many cards load
_SEM = asyncio.Semaphore(4)

async def fetch_hourly(lat: float, lon: float):
    """
    Fetch exactly the next 24 hourly steps in Europe/Madrid, with the vars we need.
    Concurrency limited via a small semaphore.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m",
        "timezone": "Europe/Madrid",
        "past_hours": 0,
        "forecast_hours": 24,
    }
    async with _SEM:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            r.raise_for_status()
            return r.json()

def adjust_temperature_to_elevation(t_c: float, elev_target_m: float, elev_model_m: float | None = None):
    if elev_model_m is None:
        return round(t_c, 1)
    return round(t_c + (elev_model_m - elev_target_m) * LAPSE_RATE_K_PER_M, 1)

def slice_next_24h(payload: dict, elev_target_m: float):
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    wind = hourly.get("wind_speed_10m", [])
    gust = hourly.get("wind_gusts_10m", [])
    precip = hourly.get("precipitation", [])
    if not gust:
        gust = [None] * len(times)

    n = min(len(times), len(temps), len(wind), len(gust), len(precip), 24)
    out = []
    for i in range(n):
        t_adj = adjust_temperature_to_elevation(temps[i], elev_target_m, elev_model_m=None)
        out.append({
            "time": times[i],  # "YYYY-MM-DDTHH:MM" in Europe/Madrid
            "temp_c": t_adj,
            "wind_speed_kmh": round(wind[i] * 3.6, 1) if wind[i] is not None else None,
            "wind_gust_kmh": round(gust[i] * 3.6, 1) if gust[i] is not None else None,
            "precip_mm": precip[i],
            "snow_likely": (t_adj <= 0.0) and (precip[i] or 0) > 0
        })
    return out
