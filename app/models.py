from sqlalchemy import Column, Integer, String, JSON, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from .db import Base

class MyMountain(Base):
    __tablename__ = "my_mountains"
    id = Column(Integer, primary_key=True)
    mountain_id = Column(String, nullable=False, unique=True)   # one list for now
    display_order = Column(Integer, default=0)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

class WeatherCache(Base):
    __tablename__ = "weather_cache"
    id = Column(Integer, primary_key=True)
    mountain_id = Column(String, nullable=False)
    band = Column(String, nullable=False)  # base|mid|summit
    payload = Column(JSON, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    ttl_seconds = Column(Integer, default=3600)

    __table_args__ = (
        UniqueConstraint("mountain_id", "band", name="uniq_mtn_band"),
    )
