"""
SQLAlchemy database models.

Defines tables for user mountain lists and weather cache.
"""
from sqlalchemy import Column, Integer, String, JSON, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from .db import Base


class MyMountain(Base):
    """
    User's saved mountain list.
    
    Currently single-user (no user_id). For multi-user support,
    add user_id foreign key and composite unique constraint.
    """
    __tablename__ = "my_mountains"
    
    id = Column(Integer, primary_key=True)
    mountain_id = Column(String, nullable=False, unique=True)
    display_order = Column(Integer, default=0)  # For future drag-and-drop reordering
    added_at = Column(DateTime(timezone=True), server_default=func.now())


class WeatherCache(Base):
    """
    Weather forecast cache with TTL.
    
    Stores 24-hour forecast as JSON blob to reduce API calls.
    Unique constraint on (mountain_id, band) ensures one cache per elevation band.
    """
    __tablename__ = "weather_cache"
    
    id = Column(Integer, primary_key=True)
    mountain_id = Column(String, nullable=False)
    band = Column(String, nullable=False)  # base | mid | summit
    payload = Column(JSON, nullable=False)  # Full 24-hour forecast
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    ttl_seconds = Column(Integer, default=3600)  # Cache lifetime

    __table_args__ = (
        UniqueConstraint("mountain_id", "band", name="uniq_mtn_band"),
    )