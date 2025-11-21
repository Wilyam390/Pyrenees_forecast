# app/weather.py
import httpx
import asyncio
from .config import settings

LAPSE_RATE_K_PER_M = 0.0065
_SEM = asyncio.Semaphore(settings.MAX_CONCURRENT_WEATHER_REQUESTS)

async def fetch_hourly(lat: float, lon: float):
    """
    Fetch exactly the next 24 hourly steps with extended weather variables.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,wind_direction_10m,weather_code,relative_humidity_2m,cloud_cover",
        "timezone": "Europe/Madrid",
        "past_hours": 0,
        "forecast_hours": 24,
    }
    async with _SEM:
        async with httpx.AsyncClient(timeout=settings.WEATHER_API_TIMEOUT) as client:
            r = await client.get(settings.WEATHER_API_URL, params=params)
            r.raise_for_status()
            return r.json()

def adjust_temperature_to_elevation(t_c: float, elev_target_m: float, elev_model_m: float | None = None):
    if elev_model_m is None:
        return round(t_c, 1)
    return round(t_c + (elev_model_m - elev_target_m) * LAPSE_RATE_K_PER_M, 1)

def get_weather_description(code: int | None) -> str:
    """Convert WMO weather code to description."""
    if code is None:
        return "Unknown"
    
    weather_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Foggy",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Heavy drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Light showers",
        81: "Showers",
        82: "Heavy showers",
        85: "Light snow showers",
        86: "Snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with hail"
    }
    return weather_map.get(code, "Unknown")

def get_wind_direction(degrees: float | None) -> str:
    """Convert wind direction degrees to cardinal direction."""
    if degrees is None:
        return "N/A"
    
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]

def slice_next_24h(payload: dict, elev_target_m: float):
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    wind = hourly.get("wind_speed_10m", [])
    gust = hourly.get("wind_gusts_10m", [])
    precip = hourly.get("precipitation", [])
    wind_dir = hourly.get("wind_direction_10m", [])
    weather_codes = hourly.get("weather_code", [])
    humidity = hourly.get("relative_humidity_2m", [])
    clouds = hourly.get("cloud_cover", [])
    
    # Ensure all arrays exist
    if not gust:
        gust = [None] * len(times)
    if not wind_dir:
        wind_dir = [None] * len(times)
    if not weather_codes:
        weather_codes = [None] * len(times)
    if not humidity:
        humidity = [None] * len(times)
    if not clouds:
        clouds = [None] * len(times)

    n = min(len(times), len(temps), len(wind), len(precip), 24)
    out = []
    for i in range(n):
        t_adj = adjust_temperature_to_elevation(temps[i], elev_target_m, elev_model_m=None)
        out.append({
            "time": times[i],
            "temp_c": t_adj,
            "wind_speed_kmh": round(wind[i] * 3.6, 1) if wind[i] is not None else None,
            "wind_gust_kmh": round(gust[i] * 3.6, 1) if gust[i] is not None else None,
            "wind_direction": get_wind_direction(wind_dir[i]),
            "wind_direction_deg": wind_dir[i],
            "precip_mm": precip[i],
            "snow_likely": (t_adj <= 0.0) and (precip[i] or 0) > 0,
            "weather_code": weather_codes[i],
            "weather_description": get_weather_description(weather_codes[i]),
            "humidity": humidity[i],
            "cloud_cover": clouds[i]
        })
    return out