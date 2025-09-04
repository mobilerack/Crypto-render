# Hivatalos, pehelykönnyű Python alap image használata
FROM python:3.11-slim

# Munkakönyvtár beállítása
WORKDIR /app

# A környezeti változók beállítása
ENV PYTHONUNBUFFERED 1 \
    PYTHONDONTWRITEBYTECODE 1

# Rendszerszintű függőségek telepítése és egy nem-root felhasználó létrehozása
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system app && adduser --system --group app

# Python függőségek telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# A tulajdonos megváltoztatása a nem-root felhasználóra
COPY --chown=app:app . .

# Átváltás a nem-root felhasználóra
USER app

# A port beállítása
ENV PORT 8000
EXPOSE 8000

# Az alkalmazás indító parancsa
CMD ["gunicorn", "--workers=4", "--timeout=120", "--bind", "0.0.0.0:${PORT}", "app:app"]
