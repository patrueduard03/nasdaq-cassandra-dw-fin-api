#!/bin/bash

# NASDAQ Cassandra DW Fin API Setup Script
# This script sets up the environment and runs the NASDAQ Cassandra DW Fin API.
# Works on any computer with Python 3.8+

# Auto-set execute permissions
if [[ ! -x "$0" ]]; then
    echo "Setting execute permissions for future use..."
    chmod +x "$0" 2>/dev/null || echo "Note: Could not set execute permissions (use bash setup_and_run.sh instead)."
fi

set -e

echo "Setting up NASDAQ Cassandra DW Fin API...please wait."

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" &> /dev/null; then
        local version=$($python_cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        
        if [[ $major -eq 3 && $minor -ge 8 ]]; then
            echo "$python_cmd"
            return 0
        fi
    fi
    return 1
}

# Find suitable Python executable
PYTHON_CMD=""
echo "Checking for Python 3.8+..."

# Try different Python commands in order of preference
for cmd in python3.12 python3.11 python3.10 python3.9 python3.8 python3 python; do
    if PYTHON_CMD=$(check_python_version "$cmd"); then
        echo "Found suitable Python: $($PYTHON_CMD --version)"
        break
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo "Error: Python 3.8+ not found. Please install Python 3.8 or higher and try again."
    echo "Available Python versions:"
    for cmd in python python3; do
        if command -v "$cmd" &> /dev/null; then
            echo "  $cmd: $($cmd --version 2>&1)"
        fi
    done
    exit 1
fi

# Check if virtual environment already exists
VENV_DIR=".venv"
if [[ -d "$VENV_DIR" && -f "$VENV_DIR/bin/activate" ]]; then
    echo "Found existing virtual environment. Using it..."
    source "$VENV_DIR/bin/activate"
elif [[ -d "$VENV_DIR" && -f "$VENV_DIR/Scripts/activate" ]]; then
    # Windows-style venv
    echo "Found existing virtual environment (Windows). Using it..."
    source "$VENV_DIR/Scripts/activate"
else
    echo "Creating new virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    # Activate virtual environment (cross-platform)
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        source "$VENV_DIR/bin/activate"
    elif [[ -f "$VENV_DIR/Scripts/activate" ]]; then
        source "$VENV_DIR/Scripts/activate"
    else
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created and activated."
fi

# Upgrade pip in virtual environment
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Check pip availability
if ! command -v pip &> /dev/null; then
    echo "Error: pip not found even after virtual environment setup."
    exit 1
fi

# Check requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Run this script from the project directory."
    exit 1
fi

echo "Installing dependencies..."
pip install -r requirements.txt

# Find and check main file
if [ -f "src/main.py" ]; then
    MAIN_FILE="src/main.py"
    echo "Starting application from src/main.py..."
    cd src && python main.py
elif [ -f "main.py" ]; then
    MAIN_FILE="main.py"
    echo "Starting application from main.py..."
    python main.py
else
    echo "Error: main.py not found in src/ or current directory."
    exit 1
fi