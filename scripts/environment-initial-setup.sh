#!/bin/bash
# Exit on error
set -e

echo "Starting environment setup..."

sudo apt update && sudo apt install -y python3-venv nginx git mosquitto mosquitto-clients
curl -LsSf https://astral.sh/uv/install.sh | sh
