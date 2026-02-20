#!/bin/bash
# Exit on error
set -e

echo "Starting update..."

# Parse arguments
ATTACH_FLAG=false
for arg in "$@"; do
    if [ "$arg" == "--attach" ]; then
        ATTACH_FLAG=true
    fi
done


cd /home/toby

# We need to work out the folder to move it to. This is the format `/home/toby/bindicator-<version>`. If it exists, add -{number}, where number is the first free number.
#cd "$(dirname "$0")/.."

VERSION=$(cat .bindicator-dev/VERSION)
TARGET_FOLDER="/home/toby/bindicator-$VERSION"
if [ -d "$TARGET_FOLDER" ]; then
    NUMBER=1
    while [ -d "${TARGET_FOLDER}-${NUMBER}" ]; do
        NUMBER=$((NUMBER + 1))
    done
    TARGET_FOLDER="${TARGET_FOLDER}-${NUMBER}"
fi

# Create the target folder if it doesn't exist
mkdir -p "$TARGET_FOLDER"
echo "Moving new version to $TARGET_FOLDER"

# Move the new version into place (including hidden files)
shopt -s dotglob
mv .bindicator-dev/* "$TARGET_FOLDER"
shopt -u dotglob

echo "Cleaning up old development folder..."
rm -rf .bindicator-dev

echo "Stopping services..."
sudo systemctl stop bindicator-api bindicator-hardware bindicator-booting

echo "Switching live version"
# Update or create the symlink `/home/toby/bindicator` to point to the new version
ln -sfn "$TARGET_FOLDER" /home/toby/bindicator

cd "$TARGET_FOLDER"

echo "Update Python"
# Complete the updates
/home/toby/.local/bin/uv sync

echo "Updating the database"
/home/toby/bindicator/.venv/bin/alembic upgrade head


# Handles nginx - possibly not all needed?
echo "Updating nginx configuration..."
sudo cp scripts/bindicator.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/bindicator.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
echo "Restarting nginx..."
sudo systemctl restart nginx

# Updates systemd services
echo "Updating systemd services..."
sudo cp scripts/bindicator-api.service /etc/systemd/system/
sudo cp scripts/bindicator-hardware.service /etc/systemd/system/
sudo cp scripts/bindicator-booting.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "Enabling boot scripts"
sudo systemctl enable bindicator-booting

echo "Restarting mosquito"
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

echo "Cleaning up old versions..."
# Remove old versions, keeping the last 5 (excluding the current one)
ls -dt /home/toby/bindicator-* | grep -v "$(readlink -f /home/toby/bindicator)" | tail -n +6 | xargs -r rm -rf

if [ "$ATTACH_FLAG" = false ]; then
    echo "Enabling and starting bindicator-api and bindicator-hardware services..."
    sudo systemctl enable --now bindicator-api bindicator-hardware
    echo "Update Complete! Access via http://$(hostname).local"
else
    echo "--attach flag detected. Running processes directly with tagged output..."
    echo "Not yet implemented! Please run the services directly with"
    echo "/home/toby/bindicator/.venv/bin/python /home/toby/bindicator/hardware/main.py"
    echo "/home/toby/bindicator/.venv/bin/python /home/toby/bindicator/.venv/bin/fastapi run /home/toby/bindicator/backend/main.py"

fi

