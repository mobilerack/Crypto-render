# Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Telepítjük a 'dos2unix' eszközt
RUN apt-get update && apt-get install -y dos2unix

# Az összes fájl másolása
COPY . .

# A dos2unix eszközzel "megtisztítjuk" a kritikus fájlokat
RUN dos2unix ./start.sh
RUN dos2unix ./setup_database.py
RUN dos2unix ./requirements.txt

# Telepítjük a Python függőségeket
RUN pip install -r requirements.txt

# Futtathatóvá tesszük az indító szkriptet
RUN chmod +x ./start.sh

# Alapértelmezett indító parancs (ezt felül fogjuk bírálni a Render UI-ban)
CMD ["bash", "./start.sh"]
