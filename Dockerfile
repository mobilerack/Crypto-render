# # Dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Az összes fájl másolása
COPY . .

# Ez a két sor biztosítja, hogy a script Linux-kompatibilis legyen.
# 1. Eltávolítja a Windows-specifikus sorvégződéseket.
RUN sed -i 's/\r$//' ./render-build.sh
# 2. Futtathatóvá teszi a build scriptet.
RUN chmod +x ./render-build.sh

# A telepítő szkript futtatása a Docker image építése közben.
RUN ./render-build.sh

ENV PORT 8000
EXPOSE 8000

# Az alkalmazás indító parancsa
CMD ["gunicorn", "--workers=4", "--timeout=120", "--bind", "0.0.0.0:${PORT}", "app:app"]

FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Az összes fájl másolása
COPY . .

# Ez a két sor biztosítja, hogy a script Linux-kompatibilis legyen.
# 1. Eltávolítja a Windows-specifikus sorvégződéseket.
RUN sed -i 's/\r$//' ./render-build.sh
# 2. Futtathatóvá teszi a build scriptet.
RUN chmod +x ./render-build.sh

# A telepítő szkript futtatása a Docker image építése közben.
RUN ./render-build.sh

ENV PORT 8000
EXPOSE 8000

# Az alkalmazás indító parancsa
CMD ["gunicorn", "--workers=4", "--timeout=120", "--bind", "0.0.0.0:${PORT}", "app:app"]
