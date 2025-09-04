# Használj egy hivatalos, kisméretű Python futtatókörnyezetet
FROM python:3.9-slim

# Állítsd be a munkakönyvtárat a konténeren belül
WORKDIR /app

# Másold át a függőségeket tartalmazó fájlt és telepítsd őket
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Másold át a projekt többi fájlját a konténerbe
COPY . .

# Add meg a portot, amin az alkalmazás futni fog (Render ezt preferálja)
EXPOSE 10000

# Parancs az alkalmazás elindítására egy stabil, több szálon futó Gunicorn szerverrel
# Az "app:app" azt jelenti: futtasd az "app.py" fájlban lévő "app" nevű Flask objektumot
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:10000", "app:app"]
