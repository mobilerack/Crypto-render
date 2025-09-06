#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Indító szkript futtatása..."

# 1. Adatbázis előkészítése (csak akkor tölt le, ha szükséges)
python setup_database.py

# 2. A Gunicorn webszerver elindítása
echo "Adatbázis ellenőrizve, Gunicorn szerver indul..."
gunicorn --workers=4 --timeout=120 --bind 0.0.0.0:${PORT} app:app
