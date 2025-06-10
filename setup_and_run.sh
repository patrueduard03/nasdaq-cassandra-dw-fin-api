#!/bin/bash

# NASDAQ Cassandra DW Fin API Setup Script
# This script sets up the environment and runs the NASDAQ Cassandra DW Fin API.

# Auto-set execute permissions
if [[ ! -x "$0" ]]; then
    echo "Setting execute permissions for future use..."
    chmod +x "$0" 2>/dev/null || echo "Note: Could not set execute permissions (use bash setup_and_run.sh instead)."
fi

set -e

echo "Setting up NASDAQ Cassandra DW Fin API...please wait."

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.8+ and try again."
    exit 1
fi

echo "Found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 not found. Please install pip and try again."
    exit 1
fi

# Check requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Run this script from the project directory."
    exit 1
fi

echo "Installing dependencies..."
pip3 install -r requirements.txt

# Find and check main file
if [ -f "src/main.py" ]; then
    MAIN_FILE="src/main.py"
    echo "Starting application from src/main.py..."
    cd src && python3 main.py
elif [ -f "main.py" ]; then
    MAIN_FILE="main.py"
    echo "Starting application from main.py..."
    python3 main.py
else
    echo "Error: main.py not found in src/ or current directory."
    exit 1
fi
