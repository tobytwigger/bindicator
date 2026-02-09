from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

load_dotenv(dotenv_path=root_dir / ".env")

SQLALCHEMY_DATABASE_URL = f"sqlite+pysqlite:///{os.getenv("DATABASE_FILE_PATH")}"

# 'check_same_thread' is only needed for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Enable Foreign Key support in SQLite (disabled by default)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()