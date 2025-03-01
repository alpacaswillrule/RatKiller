#!/bin/bash
# Start script for Rat Reporter application

# Make sure the script is executable
# chmod +x start.sh

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 to run this application."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip3 to run this application."
    exit 1
fi

# Create necessary directories if they don't exist
mkdir -p backend/data/photos

# Install required packages
echo "Installing required packages..."
pip3 install -r backend/requirements.txt

# Start the application
echo "Starting Rat Reporter application..."
python3 run.py
