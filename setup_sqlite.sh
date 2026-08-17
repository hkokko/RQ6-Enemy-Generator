#!/bin/bash

# Mythras Encounter Generator - SQLite Setup Script
# This script automates the environment setup for local development.

set -e

echo "-------------------------------------------------------"
echo "Initializing Mythras Encounter Generator (SQLite Dev)"
echo "-------------------------------------------------------"

# 1. Create 'temp' directory (required by the app)
if [ ! -d "temp" ]; then
    echo "[1/4] Creating 'temp' directory..."
    mkdir temp
else
    echo "[1/4] 'temp' directory already exists."
fi

# 2. Install Dependencies
echo "[2/4] Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 3. Configure settings.py (if it doesn't exist)
if [ ! -f "mythras_eg/settings.py" ]; then
    echo "[3/4] Creating mythras_eg/settings.py for SQLite..."
    # Copy from example and set SQLite as default for this local file
    sed "s/USE_SQLITE = os.environ.get('USE_SQLITE', '0') == '1'/USE_SQLITE = True/" mythras_eg/settings_example.py > mythras_eg/settings.py
else
    echo "[3/4] mythras_eg/settings.py already exists."
fi

# 4. Initialize Database
echo "[4/4] Initializing database (migrate & loaddata)..."
python3 manage.py migrate
python3 manage.py loaddata enemygen_testdata.json

echo "-------------------------------------------------------"
echo "Setup Complete!"
echo "Run the server with: python3 manage.py runserver"
echo "Run tests with:      python3 manage.py test"
echo "-------------------------------------------------------"
