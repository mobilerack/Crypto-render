# Dockerfile (MÓDOSÍTOTT)
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Az összes fájl másolása
COPY . .

# A build script futtathatóvá tétele
RUN chmod +x ./render-build.sh

# JAVÍTÁS: Itt futtatjuk le a telepítő szkriptet a Docker image építése közben.
# Ez a lépés fogja létrehozni és feltölteni az adatbázist.
RUN ./render-build.sh

ENV PORT 8000
EXPOSE 8000

# A Start parancs változatlan, ezt fogja használni a Render
CMD ["gunicorn", "--workers=4", "--timeout=120", "--bind", "0.0.0.0:${PORT}", "app:app"]
