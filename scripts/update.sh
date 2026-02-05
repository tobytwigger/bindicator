#!/bin/bash
# Exit on error
set -e

echo "Starting update..."

source .venv/bin/activate
/home/toby/.local/bin/uv sync

# Handles nginx - possibly not all needed?
sudo cp scripts/bindicator.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/bindicator.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Updates systemd services
sudo cp scripts/bindicator-api.service /etc/systemd/system/
sudo cp scripts/bindicator-hardware.service /etc/systemd/system/
sudo cp scripts/bindicator-booting.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bindicator-api bindicator-hardware
sudo systemctl enable bindicator-booting

echo "Update Complete! Access via http://$(hostname).local"
