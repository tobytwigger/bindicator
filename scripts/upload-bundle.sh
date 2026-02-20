#!/bin/bash

# Ensure the user provides the version to use
if [ -z "$1" ]; then
  echo "Error: Version not provided. Please use the script as follows:"
  echo "Usage: $0 <version> [--quick] [--no-ui]"
  exit 1
fi

VERSION=$1

# Parse arguments for flags
ATTACH_FLAG=false
QUICK_FLAG=false
NO_UI_FLAG=false
for arg in "$@"; do
    if [ "$arg" == "--attach" ]; then
        ATTACH_FLAG=true
    fi
    if [ "$arg" == "--quick" ]; then
        QUICK_FLAG=true
    fi
    if [ "$arg" == "--no-ui" ]; then
        NO_UI_FLAG=true
    fi
    # ...add more flags as needed...
done

# Set options based on flags
QUICK_OPTION=""
NO_UI_OPTION=""
if [ "$QUICK_FLAG" = true ]; then
    QUICK_OPTION="--quick"
    echo "Quick option enabled: Skipping non-essential steps."
fi
if [ "$NO_UI_FLAG" = true ]; then
    NO_UI_OPTION="--no-ui"
    echo "No-UI option enabled: Skipping UI-related steps."
fi
if [ "$ATTACH_FLAG" = true ]; then
    echo "Will not run the services with systemd, instead attaches to them."
fi

# Create a release bundle, upload it to the local bindicator and install it.

# Step 1: Create the release bundle
echo "Creating release bundle for version $VERSION..."
./create-release-bundle.sh "$VERSION" "$QUICK_OPTION" "$NO_UI_OPTION"

cd "$(dirname "$0")/.." || exit

# Step 2: Upload the release bundle to the remote server.
echo "Preparing to upload release bundle to remote server..."
FILE_NAME="release-$VERSION.zip"
REMOTE_FILE_NAME="$FILE_NAME"
REMOTE_PATH="/home/toby"
COUNTER=1

while ssh toby@bins.local "[ -e $REMOTE_PATH/$REMOTE_FILE_NAME ]"; do
  REMOTE_FILE_NAME="release-$VERSION-$COUNTER.zip"
  COUNTER=$((COUNTER + 1))
  echo "File already exists on remote server. Trying with new name: $REMOTE_FILE_NAME"
done

echo "Uploading $REMOTE_FILE_NAME to remote server..."
scp "$FILE_NAME" toby@bins.local:$REMOTE_PATH

# Step 3: SSH into the remote server, extract the bundle, and run the install script
echo "Connecting to remote server to install the release bundle..."

ssh toby@bins.local "export VERSION='$VERSION'; export ATTACH_FLAG='$ATTACH_FLAG'; bash -s" <<'ENDSSH'
echo "Removing old development directory if it exists..."
rm -rf .bindicator-dev 2>/dev/null || true

echo "Extracting release bundle..."
unzip -q -o "/home/toby/release-$VERSION.zip" -d "/home/toby/.bindicator-dev"

echo "Cleaning up release bundle zip file..."
rm "/home/toby/release-$VERSION.zip"

echo "Running installation script..."
if [ "$ATTACH_FLAG" = true ]; then
  /home/toby/.bindicator-dev/scripts/install.sh --attach
else
  /home/toby/.bindicator-dev/scripts/install.sh
fi
ENDSSH

echo "Release bundle installation completed successfully."
