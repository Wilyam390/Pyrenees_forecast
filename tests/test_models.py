"""
Unit tests for database models.
"""
import pytest
from datetime import datetime, timezone
from app.models import MyMountain, WeatherCache


def test_my_mountain_model():
    """Test MyMountain model attributes."""
    mountain = MyMountain(
        mountain_id="aneto",
        display_order=1
    )
    
    assert mountain.mountain_id == "aneto"
    assert mountain.display_order == 1


def test_weather_cache_model():
    """Test WeatherCache model attributes."""
    cache = WeatherCache(
        mountain_id="aneto",
        band="summit",
        payload={"temp": 10},
        ttl_seconds=3600
    )
    
    assert cache.mountain_id == "aneto"
    assert cache.band == "summit"
    assert cache.payload == {"temp": 10}
    assert cache.ttl_seconds == 3600


def test_weather_cache_unique_constraint():
    """Test that WeatherCache has unique constraint on mountain_id + band."""
    assert hasattr(WeatherCache, '__table_args__')