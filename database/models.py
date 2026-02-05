# These are the database representation

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from database.database import Base

class Bin(Base):
    __tablename__ = "bins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    colour = Column(String)

    __table_args__ = (UniqueConstraint('position', name='_position_uc'),)
    schedules = relationship("Schedule", back_populates="bin")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=True)
    repeat_weeks = Column(Integer, nullable=False)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)

    bin = relationship("Bin", back_populates="schedules")

class BinDay(Base):
    __tablename__ = "bin_days"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    put_out_at = Column(DateTime)

class BinDayReplacement(Base):
    __tablename__ = "bin_day_replacements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    replace = Column(DateTime)
    replace_with = Column(DateTime, nullable=False)
