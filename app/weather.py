"""
Weather data fetching and processing module.

Integrates with Open-Meteo API to fetch hourly weather forecasts
and adjusts temperatures based on elevation using standard atmospheric
lapse rate.
"""
import httpx
import asyncio
from typing import Optional, Dict, List, Any
from .config import settings

# Standard atmospheric lapse rate: 6.5°C per 1000m elevation gain
LAPSE_RATE_K_PER_M: float = 0.0065

# Semaphore to limit concurrent API requests (prevents rate limiting)
_SEM: asyncio.Semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_WEATHER_REQUESTS)


async def fetch_hourly(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch 24-hour weather forecast from Open-Meteo API.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        Dict containing hourly weather data from Open-Meteo API
        
    Raises:
        httpx.HTTPError: If API request fails
        asyncio.TimeoutError: If request exceeds timeout
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


def adjust_temperature_to_elevation(
    t_c: float, 
    elev_target_m: float, 
    elev_model_m: Optional[float] = None
) -> float:
    """
    Adjust temperature for elevation difference using standard lapse rate.
    
    Args:
        t_c: Temperature in Celsius at model elevation
        elev_target_m: Target elevation in meters
        elev_model_m: Model elevation in meters (if None, returns unadjusted temp)
        
    Returns:
        Adjusted temperature in Celsius, rounded to 1 decimal place
    """
    if elev_model_m is None:
        return round(t_c, 1)
    return round(t_c + (elev_model_m - elev_target_m) * LAPSE_RATE_K_PER_M, 1)


def get_weather_description(code: Optional[int]) -> str:
    """
    Convert WMO weather code to human-readable description.
    
    Args:
        code: WMO weather code integer (0-99)
        
    Returns:
        Human-readable weather description string
    """
    if code is None:
        return "Unknown"
    
    weather_map: Dict[int, str] = {
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


def get_wind_direction(degrees: Optional[float]) -> str:
    """
    Convert wind direction degrees to cardinal direction.
    
    Args:
        degrees: Wind direction in degrees (0-360)
        
    Returns:
        Cardinal direction string (N, NNE, NE, etc.)
    """
    if degrees is None:
        return "N/A"
    
    directions: List[str] = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    index: int = round(degrees / 22.5) % 16
    return directions[index]


def slice_next_24h(payload: Dict[str, Any], elev_target_m: float) -> List[Dict[str, Any]]:
    """
    Extract and process next 24 hours of weather data.
    
    Args:
        payload: Raw API response from Open-Meteo
        elev_target_m: Target elevation for temperature adjustment
        
    Returns:
        List of dicts, each containing processed hourly forecast data
    """
    hourly: Dict[str, List] = payload.get("hourly", {})
    times: List[str] = hourly.get("time", [])
    temps: List[float] = hourly.get("temperature_2m", [])
    wind: List[float] = hourly.get("wind_speed_10m", [])
    gust: List[Optional[float]] = hourly.get("wind_gusts_10m", [])
    precip: List[float] = hourly.get("precipitation", [])
    wind_dir: List[Optional[float]] = hourly.get("wind_direction_10m", [])
    weather_codes: List[Optional[int]] = hourly.get("weather_code", [])
    humidity: List[Optional[int]] = hourly.get("relative_humidity_2m", [])
    clouds: List[Optional[int]] = hourly.get("cloud_cover", [])
    
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

    n: int = min(len(times), len(temps), len(wind), len(precip), 24)
    out: List[Dict[str, Any]] = []
    
    for i in range(n):
        t_adj: float = adjust_temperature_to_elevation(temps[i], elev_target_m, elev_model_m=None)
        out.append({
            "time": times[i],
            "temp_c": t_adj,
            "wind_speed_kmh": round(wind[i], 1) if wind[i] is not None else None,
            "wind_gust_kmh": round(gust[i], 1) if gust[i] is not None else None,
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