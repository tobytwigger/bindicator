from fastapi import FastAPI
from backend.routes import bins, hardware, schedules, bin_day_replacements, settings
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

app = FastAPI(
    root_path="/api",
    title="Bindicator API"
)

# Include the routers
app.include_router(bins.router)
app.include_router(hardware.router)
# app.include_router(bins.router)
app.include_router(schedules.router)
app.include_router(bin_day_replacements.router)
app.include_router(settings.router)

