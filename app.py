# setup_database.py

import requests
import pandas as pd
import sqlite3
import os
from datetime import datetime

# A konfigurációs változók ugyanazok, mint az app.py-ban
DATA_DIR = os.environ.get('RENDER_DISK_PATH', '.')
DB_FILE = os.path.join(DATA_DIR, 'crypto_data.db')
CRYPTO_ID = 'bitcoin'
VS_CURRENCY = 'usd'

def init_db():
    """Létrehozza az adatbázis táblát, ha még nem létezik."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crypto_id TEXT NOT NULL,
            date DATE NOT NULL,
            price REAL NOT NULL,
            UNIQUE(crypto_id, date)
        )
    ''')
    conn.commit()
    conn.close()
    print("Adatbázis tábla sikeresen létrehozva/ellenőrizve.")

def populate_initial_data():
    """Letölti a teljes historikus adatmennyiséget és elmenti az adatbázisba."""
    print("Kezdeti adatfeltöltés megkezdése a CoinGecko API-ról...")
    url = f"https://api.coingecko.com/api/v3/coins/{CRYPTO_ID}/market_chart"
    params = {'vs_currency': VS_CURRENCY, 'days': 'max', 'interval': 'daily'}
    try:
        response = requests.get(url, params=params, timeout=120) # Hosszabb timeout a nagy letöltéshez
        response.raise_for_status()
        data = response.json().get('prices', [])
        
        if not data:
            print("Nem érkezett adat az API-tól.")
            return

        df = pd.DataFrame(data, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d')
        df['crypto_id'] = CRYPTO_ID
        df = df[['crypto_id', 'date', 'price']]
        
        conn = sqlite3.connect(DB_FILE)
        df.to_sql('prices', conn, if_exists='replace', index=False) # 'replace' biztosítja a tiszta feltöltést
        conn.close()
        
        print(f"Sikeresen lementve {len(df)} historikus adatpont.")
        
    except requests.exceptions.RequestException as e:
        print(f"Hiba a kezdeti adatfeltöltés során: {e}")
        # Hiba esetén a program leáll, és a build sikertelen lesz, ami helyes.
        exit(1)

if __name__ == '__main__':
    init_db()
    populate_initial_data()
