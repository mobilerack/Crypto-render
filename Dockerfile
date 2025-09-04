# 1. Alapkép kiválasztása: Egy vékony Python 3.11 környezet
FROM python:3.11-slim

# 2. Munkakönyvtár beállítása a konténeren belül
WORKDIR /app

# 3. A függőségek telepítése
# Először csak a requirements.txt-t másoljuk be, hogy a Docker kihasználhassa a "layer caching"-et.
# Így ha csak a kódot változtatod, de a függőségeket nem, a telepítés nem fut le újra.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. Az alkalmazás kódjának bemásolása
COPY . .

# 5. A Gunicorn számára szükséges környezeti változó beállítása
# A Render a PORT változón keresztül közli, hogy melyik porton kell figyelni
ENV PORT 8000

# 6. Port megnyitása
EXPOSE 8000

# 7. Az alkalmazás indító parancsa
# A Gunicorn elindítja az app.py fájlban található 'app' nevű Flask alkalmazást.
# A '0.0.0.0' host szükséges, hogy a konténeren kívülről is elérhető legyen.
# A --workers=4 a párhuzamos kérések kezelését segíti, a --timeout 120 pedig időt ad a hosszabb adatletöltéseknek.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:10000", "app:app"]
