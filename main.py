from typing import List
import databases
import sqlalchemy
from sqlalchemy.dialects import postgresql
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import os
import urllib

from secrets import db_pass
# from pathlib import Path
# script_path = Path(__file__, '..').resolve()
# with open(script_path.joinpath("models.py")) as f:
#     from models import Event, EventIn

from pydantic import BaseModel
import datetime 

host_server = os.environ.get('host_server', 'localhost')
db_server_port = urllib.parse.quote_plus(str(os.environ.get('db_server_port', '5432')))
database_name = os.environ.get('database_name', 'events_db')
db_username = urllib.parse.quote_plus(str(os.environ.get('db_username', 'dbuser')))
db_password = urllib.parse.quote_plus(str(os.environ.get('db_password', db_pass)))
ssl_mode = urllib.parse.quote_plus(str(os.environ.get('ssl_mode','prefer')))
DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}?sslmode={}'.format(db_username, db_password, host_server, db_server_port, database_name, ssl_mode)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData(schema="Event")

events = sqlalchemy.Table(
    "Events",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("event_name", sqlalchemy.String),
    sqlalchemy.Column("venue", sqlalchemy.String),
    sqlalchemy.Column("when_start_date", sqlalchemy.Date),
    sqlalchemy.Column("when_start_time", sqlalchemy.Time),
    sqlalchemy.Column("when_end_date", sqlalchemy.Date),
    sqlalchemy.Column("when_end_time", sqlalchemy.Time),
    sqlalchemy.Column("website", sqlalchemy.String),
    sqlalchemy.Column("description", sqlalchemy.String),
    sqlalchemy.Column("venue_details", sqlalchemy.String),
    sqlalchemy.Column("tags", postgresql.ARRAY(sqlalchemy.String))
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, pool_size=3, max_overflow=0
)
metadata.create_all(engine)

class EventIn(BaseModel):
    event_name: str
    venue: str
    when_start_date: datetime.date
    when_start_time: datetime.time
    when_end_date: datetime.date
    when_end_time: datetime.time
    website: str
    description: str
    venue_details: str
    tags: list[str]

class Event(BaseModel):
    id: int
    event_name: str
    venue: str
    when_start_date: datetime.date
    when_start_time: datetime.time
    when_end_date: datetime.date
    when_end_time: datetime.time
    website: str
    description: str
    venue_details: str
    tags: list[str]

app = FastAPI(title="REST API using FastAPI PostgreSQL Async EndPoints")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Create a Event using HTTP Verb POST
@app.post("/events/", response_model=Event, status_code = status.HTTP_201_CREATED)
async def create_note(event: EventIn):
    query = events.insert().values(text=note.text, completed=note.completed)
    last_record_id = await database.execute(query)
    return {**note.dict(), "id": last_record_id}

# Update Event using HTTP Verb PUT
@app.put("/events/{event_id}/", response_model=Event, status_code = status.HTTP_200_OK)
async def update_note(event_id: int, payload: EventIn):
    query = events.update().where(events.c.id == event_id).values(text=payload.text, completed=payload.completed)
    await database.execute(query)
    return {**payload.dict(), "id": event_id}

# Get Paginated List of Notes using HTTP Verb GET
@app.get("/events/", response_model=List[Event], status_code = status.HTTP_200_OK)
async def read_notes(skip: int = 0, take: int = 20):
    query = events.select().offset(skip).limit(take)
    print(query)
    return await database.fetch_all(query)

# Get single Event Given its Id using HTTP Verb GET
@app.get("/events/{event_id}/", response_model=Event, status_code = status.HTTP_200_OK)
async def read_notes(event_id: int):
    query = events.select().where(events.c.id == event_id)
    return await database.fetch_one(query)

# Delete single Event Given its Id using HTTP Verb DELETE
@app.delete("/events/{event_id}/", status_code = status.HTTP_200_OK)
async def update_note(event_id: int):
    query = events.delete().where(events.c.id == event_id)
    await database.execute(query)
    return {"message": "Event with id: {} deleted successfully!".format(event_id)}