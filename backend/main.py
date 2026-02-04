from fastapi import FastAPI
from routes import homes#, bins, schedules
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

app = FastAPI(
    root_path="/api",
    title="Bindicator API"
)

# Include the routers
app.include_router(homes.router)
# app.include_router(bins.router)
# app.include_router(schedules.router)

@app.get("/")
def root():
    return {"message": "Hardware API is online"}

@app.post("/restart/")
def restart_application():
    # Run 'sudo systemctl restart bindicator-hardware.service'
    subprocess.call(['sudo', 'systemctl', 'restart', 'bindicator-hardware.service'])