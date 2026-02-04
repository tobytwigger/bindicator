# These are the database representation

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from database import Base

class Home(Base):
    __tablename__ = "homes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    council = Column(String)
    council_data = Column(JSON)  # SQLite handles JSON via text under the hood
    active = Column(Boolean, nullable=False, default=False)
    timeout = Column(Integer, nullable=False, default=180)
    put_out_day_before = Column(Boolean, nullable=False, default=False)

    bins = relationship("Bin", back_populates="home")
    schedules = relationship("Schedule", back_populates="home")

class Bin(Base):
    __tablename__ = "bins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    council_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    home_id = Column(Integer, ForeignKey("homes.id"), nullable=False)

    home = relationship("Home", back_populates="bins")
    __table_args__ = (UniqueConstraint('position', 'home_id', name='_position_home_uc'),)

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime)
    repeat_weeks = Column(Integer, nullable=False)
    home_id = Column(Integer, ForeignKey("homes.id"), nullable=False)

    home = relationship("Home", back_populates="schedules")

class BinSchedule(Base):
    __tablename__ = "bin_schedules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)

class BinDay(Base):
    __tablename__ = "bin_days"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    home_id = Column(Integer, ForeignKey("homes.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    put_out_at = Column(DateTime)

class BinDayReplacement(Base):
    __tablename__ = "bin_day_replacements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    replace = Column(DateTime)
    replace_with = Column(DateTime, nullable=False) # 'with' is a reserved keyword in Python
    home_id = Column(Integer, ForeignKey("homes.id"), nullable=False)