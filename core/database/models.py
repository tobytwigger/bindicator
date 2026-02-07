# These are the database representation

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from core.database.database import Base
from sqlalchemy.sql import func

class Bin(Base):
    __tablename__ = "bins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    colour = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    schedules = relationship("Schedule", back_populates="bin", cascade="all, delete-orphan")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(Date, nullable=False)
    end = Column(Date, nullable=True)
    repeat_weeks = Column(Integer, nullable=False)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)

    bin = relationship("Bin", back_populates="schedules")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BinDayReplacement(Base):
    __tablename__ = "bin_day_replacements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    replace = Column(Date)
    replace_with = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timeout = Column(Integer, default=120)