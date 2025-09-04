#!/usr/bin/env bash
# exit on error
set -o errexit

# Függőségek telepítése
pip install -r requirements.txt

# Az adatbázis létrehozása és feltöltése
python setup_database.py
