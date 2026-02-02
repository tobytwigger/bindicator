#!/bin/bash
# Exit on error
set -e

echo "Starting installation..."

# 1. Update and install dependencies
sudo apt update && sudo apt install -y python3-venv nginx git
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Setup Python Virtual Environment
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
/home/toby/.local/bin/uv sync

# 3. Setup Systemd Services
sudo cp scripts/bindicator-api.service /etc/systemd/system/
sudo cp scripts/bindicator-hardware.service /etc/systemd/system/
sudo cp scripts/bindicator-booting.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bindicator-api bindicator-hardware bindicator-booting

# 4. Setup Nginx
sudo cp scripts/bindicator.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/bindicator.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "Installation Complete! Access via http://$(hostname).local"