# These are the database representation

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, JSON
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

    schedules = relationship("Schedule", back_populates="bin")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=True)
    repeat_weeks = Column(Integer, nullable=False)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)

    bin = relationship("Bin", back_populates="schedules")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BinDayReplacement(Base):
    __tablename__ = "bin_day_replacements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    replace = Column(DateTime)
    replace_with = Column(DateTime, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
