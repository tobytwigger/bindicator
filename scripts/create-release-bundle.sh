#!/bin/bash

## This script creates a release bundle for the project.

# Exit immediately if a command exits with a non-zero status
set -e

# Navigate to the root directory
cd "$(dirname "$0")/.."

# Check Node.js version
NODE_VERSION=$(node -v | sed 's/v//')
REQUIRED_VERSION=24

# Compare Node.js versions using a more robust method
if [[ $(echo -e "$NODE_VERSION\n$REQUIRED_VERSION" | sort -V | head -n1) != "$REQUIRED_VERSION" ]]; then
    echo "Node.js version must be >=24. Current version: $NODE_VERSION"
    exit 1
fi

# Parse arguments for flags
QUICK_FLAG=false
NO_UI_FLAG=false
for arg in "$@"; do
    if [ "$arg" == "--quick" ]; then
        QUICK_FLAG=true
    fi
    if [ "$arg" == "--no-ui" ]; then
        NO_UI_FLAG=true
    fi
    # ...add more flags as needed...
done

# Update python dependencies (skip if --quick is provided)
if [ "$QUICK_FLAG" == false ]; then
    uv sync
fi

# Create or clear the .output folder
if [ -d ".output" ]; then
    rm -rf .output/*
else
    mkdir .output
fi

# Copy required directories into .output
cp -r backend .output/
cp -r core .output/
cp -r scripts .output/
cp -r hardware .output/

# Generate frontend build (skip npm update and npm run generate if --quick or --no-ui is provided)
cd frontend
if [ "$QUICK_FLAG" == false ] && [ "$NO_UI_FLAG" == false ]; then
    npm update
fi
if [ "$NO_UI_FLAG" == false ]; then
    npm run generate
fi
cp -r .output/public ../.output/frontend
cd ..

# Create a VERSION file in .output
if [ -z "$1" ]; then
    echo "Please provide a version as the first argument."
    exit 1
fi
VERSION=$1
echo "$VERSION" > .output/VERSION

# Copy additional files to .output
cp .env.example .output/
cp .env.example .output/.env
cp alembic.ini .output/
cp pyproject.toml .output/
cp uv.lock .output/
cp README.md .output/
cd .output

# Create a zip file for the release
zip -q -r release-$VERSION.zip . -x "*.zip"

cd ..

cp .output/release-$VERSION.zip .

rm -rf .output

cd scripts

echo "Release bundle created: release-$VERSION.zip"
