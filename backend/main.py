from fastapi import Depends, FastAPI, HTTPException, Query
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select

class Home(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str

sqlite_url = "sqlite+pysqlite:///home/toby/data/database.sqlite"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/home/")
def read_home(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Home]:
    homes = session.exec(select(Home).offset(offset).limit(limit)).all()
    return homes