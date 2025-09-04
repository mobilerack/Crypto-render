# Hivatalos, pehelykönnyű Python alap image használata
FROM python:3.11-slim

# Munkakönyvtár beállítása az appon belül
WORKDIR /app

# A környezeti változók beállítása, hogy a Python logok azonnal megjelenjenek
ENV PYTHONUNBUFFERED 1

# Először csak a requirements fájlt másoljuk be, hogy a Docker cache-t ki tudjuk használni
COPY requirements.txt .

# A Python függőségek telepítése (a script első parancsa)
RUN pip install --no-cache-dir -r requirements.txt

# A projekt összes többi fájljának másolása
COPY . .

# Az adatbázis létrehozása és feltöltése (a script második parancsa)
RUN python setup_database.py

# A port beállítása, amin az alkalmazás futni fog
ENV PORT 8000
EXPOSE 8000

# Az alkalmazás indító parancsa a Gunicorn webszerverrel
CMD ["gunicorn", "--workers=4", "--timeout=120", "--bind", "0.0.0.0:${PORT}", "app:app"]
