# setup_database.py
import requests
import pandas as pd
import sqlite3
import os
from datetime import datetime

DATA_DIR = os.environ.get('RENDER_DISK_PATH', '.')
DB_FILE = os.path.join(DATA_DIR, 'crypto_data.db')
CRYPTO_ID = 'bitcoin'
VS_CURRENCY = 'usd'

# Beolvassuk az API kulcsot a környezeti változóból
API_KEY = os.environ.get('COINGECKO_API_KEY')

def init_db():
    # ... (ez a függvény változatlan)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(''' CREATE TABLE IF NOT EXISTS prices (...) ''') # Rövidítve
    conn.commit()
    conn.close()
    print("Adatbázis tábla sikeresen létrehozva/ellenőrizve.")

def populate_initial_data():
    print("Kezdeti adatfeltöltés megkezdése a CoinGecko API-ról...")
    
    # Ha nincs API kulcs, a program leáll egy hibaüzenettel
    if not API_KEY:
        print("Hiba: COINGECKO_API_KEY környezeti változó nincs beállítva!")
        exit(1)

    url = f"https://api.coingecko.com/api/v3/coins/{CRYPTO_ID}/market_chart"
    # Hozzáadjuk az API kulcsot a kérés paramétereihez
    params = {
        'vs_currency': VS_CURRENCY,
        'days': 'max',
        'interval': 'daily',
        'x_cg_demo_api_key': API_KEY 
    }
    try:
        response = requests.get(url, params=params, timeout=180)
        response.raise_for_status()
        # ... (a függvény többi része változatlan)
        data = response.json().get('prices', [])
        if not data:
            print("Nem érkezett adat az API-tól.")
            return
        df = pd.DataFrame(data, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d')
        df['crypto_id'] = CRYPTO_ID
        df = df[['crypto_id', 'date', 'price']]
        conn = sqlite3.connect(DB_FILE)
        df.to_sql('prices', conn, if_exists='append', index=False)
        conn.close()
        print(f"Sikeresen lementve {len(df)} historikus adatpont.")
    except requests.exceptions.RequestException as e:
        print(f"Hiba a kezdeti adatfeltöltés során: {e}")
        exit(1)

if __name__ == '__main__':
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) < 1024:
        print("Adatbázis nem létezik vagy üres, kezdeti feltöltés indul.")
        init_db()
        populate_initial_data()
    else:
        print("Adatbázis már létezik és feltöltve, a kezdeti telepítés kihagyva.")
