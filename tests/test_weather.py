"""
Unit tests for weather data processing functions.
"""
import pytest
from app.weather import (
    adjust_temperature_to_elevation,
    get_weather_description,
    get_wind_direction,
    slice_next_24h,
    LAPSE_RATE_K_PER_M
)


def test_adjust_temperature_no_model_elevation():
    """Test temperature adjustment when model elevation is None."""
    result = adjust_temperature_to_elevation(15.0, 2000, None)
    assert result == 15.0


def test_adjust_temperature_with_elevation_difference():
    """Test temperature adjustment with elevation difference."""
    result = adjust_temperature_to_elevation(10.0, 3000, 2000)
    expected = 10.0 + (2000 - 3000) * LAPSE_RATE_K_PER_M
    assert result == round(expected, 1)


def test_adjust_temperature_higher_elevation():
    """Test temperature decreases at higher elevations."""
    result = adjust_temperature_to_elevation(20.0, 3000, 1000)
    assert result < 20.0


def test_get_weather_description_clear():
    """Test weather code 0 returns 'Clear sky'."""
    assert get_weather_description(0) == "Clear sky"


def test_get_weather_description_rain():
    """Test weather code 63 returns 'Rain'."""
    assert get_weather_description(63) == "Rain"


def test_get_weather_description_snow():
    """Test weather code 73 returns 'Snow'."""
    assert get_weather_description(73) == "Snow"


def test_get_weather_description_thunderstorm():
    """Test weather code 95 returns 'Thunderstorm'."""
    assert get_weather_description(95) == "Thunderstorm"


def test_get_weather_description_unknown_code():
    """Test unknown weather code returns 'Unknown'."""
    assert get_weather_description(999) == "Unknown"


def test_get_weather_description_none():
    """Test None weather code returns 'Unknown'."""
    assert get_weather_description(None) == "Unknown"


def test_get_wind_direction_north():
    """Test 0 degrees returns 'N'."""
    assert get_wind_direction(0) == "N"


def test_get_wind_direction_east():
    """Test 90 degrees returns 'E'."""
    assert get_wind_direction(90) == "E"


def test_get_wind_direction_south():
    """Test 180 degrees returns 'S'."""
    assert get_wind_direction(180) == "S"


def test_get_wind_direction_west():
    """Test 270 degrees returns 'W'."""
    assert get_wind_direction(270) == "W"


def test_get_wind_direction_northeast():
    """Test 45 degrees returns 'NE'."""
    assert get_wind_direction(45) == "NE"


def test_get_wind_direction_none():
    """Test None degrees returns 'N/A'."""
    assert get_wind_direction(None) == "N/A"


def test_slice_next_24h_basic():
    """Test basic weather data slicing."""
    mock_payload = {
        "hourly": {
            "time": ["2025-11-21T10:00", "2025-11-21T11:00"],
            "temperature_2m": [15.0, 16.0],
            "wind_speed_10m": [10.0, 12.0],
            "wind_gusts_10m": [20.0, 25.0],
            "precipitation": [0.0, 0.5],
            "wind_direction_10m": [90.0, 180.0],
            "weather_code": [0, 61],
            "relative_humidity_2m": [60, 65],
            "cloud_cover": [20, 30]
        }
    }
    
    result = slice_next_24h(mock_payload, elev_target_m=2000)
    
    assert len(result) == 2
    assert result[0]["time"] == "2025-11-21T10:00"
    assert result[0]["temp_c"] == 15.0
    assert result[0]["wind_speed_kmh"] == 10.0
    assert result[0]["wind_gust_kmh"] == 20.0
    assert result[0]["wind_direction"] == "E"
    assert result[0]["precip_mm"] == 0.0
    assert result[0]["snow_likely"] is False
    assert result[0]["weather_description"] == "Clear sky"


def test_slice_next_24h_snow_detection():
    """Test snow detection when temp <= 0 and precipitation > 0."""
    mock_payload = {
        "hourly": {
            "time": ["2025-11-21T10:00"],
            "temperature_2m": [-2.0],
            "wind_speed_10m": [10.0],
            "wind_gusts_10m": [20.0],
            "precipitation": [1.5],
            "wind_direction_10m": [0.0],
            "weather_code": [71],
            "relative_humidity_2m": [80],
            "cloud_cover": [90]
        }
    }
    
    result = slice_next_24h(mock_payload, elev_target_m=2000)
    
    assert result[0]["snow_likely"] is True
    assert result[0]["weather_description"] == "Light snow"


def test_slice_next_24h_missing_optional_fields():
    """Test handling of missing optional fields (gusts, humidity, etc)."""
    mock_payload = {
        "hourly": {
            "time": ["2025-11-21T10:00"],
            "temperature_2m": [15.0],
            "wind_speed_10m": [10.0],
            "precipitation": [0.0]
        }
    }
    
    result = slice_next_24h(mock_payload, elev_target_m=2000)
    
    assert result[0]["wind_gust_kmh"] is None
    assert result[0]["wind_direction"] == "N/A"
    assert result[0]["humidity"] is None
    assert result[0]["cloud_cover"] is None


def test_slice_next_24h_limits_to_24_hours():
    """Test that result is limited to 24 hours even if more data provided."""
    mock_payload = {
        "hourly": {
            "time": [f"2025-11-21T{i:02d}:00" for i in range(30)],
            "temperature_2m": [15.0] * 30,
            "wind_speed_10m": [10.0] * 30,
            "precipitation": [0.0] * 30
        }
    }
    
    result = slice_next_24h(mock_payload, elev_target_m=2000)
    
    assert len(result) == 24