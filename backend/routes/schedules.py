from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database.database import get_db
from core.database import models, schemas

# Define the router
router = APIRouter(
    prefix="schedules",
    tags=["schedules"],  # This groups them in the Swagger UI (/docs)
)
