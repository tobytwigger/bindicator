#!/bin/bash
# Exit on error
set -e

echo "Starting environment update..."

# 1. Update and install dependencies
sudo apt update && sudo apt install -y python3-venv nginx git mosquitto mosquitto-clients
