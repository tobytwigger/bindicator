from fastapi import APIRouter
import subprocess

router = APIRouter(
    prefix="/hardware",
    tags=["hardware"],
)

@router.post("/restart/")
def restart_application():
    """
    Restart the hardware application.
    """
    # Run 'sudo systemctl restart bindicator-hardware.service'
    subprocess.call(['sudo', 'systemctl', 'restart', 'bindicator-hardware.service'])