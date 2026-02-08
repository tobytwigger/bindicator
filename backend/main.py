from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import bins, hardware, schedules, bin_day_replacements, settings
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

app = FastAPI(
    root_path="/api",
    title="Bindicator API"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Nuxt dev server
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://bins.local",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include the routers
app.include_router(bins.router)
app.include_router(hardware.router)
# app.include_router(bins.router)
app.include_router(schedules.router)
app.include_router(bin_day_replacements.router)
app.include_router(settings.router)

