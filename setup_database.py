# setup_database.py

import requests
import pandas as pd
import sqlite3
import os
from datetime import datetime

DATA_DIR = os.environ.get('RENDER_DISK_PATH', '.')
DB_FILE = os.path.join(DATA_DIR, 'crypto_data.db')
CRYPTO_ID = 'BTC' # A CoinDesk API a Bitcoinra (BPI) van specializálódva

def init_db():
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
    print("Kezdeti adatfeltöltés megkezdése a CoinDesk API-ról...")
    
    # MÓDOSÍTÁS: CoinDesk API URL és dátum alapú paraméterek. Nincs API kulcs.
    start_date = "2010-07-18" # A CoinDesk BPI adatainak kezdete
    end_date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.coindesk.com/v1/bpi/historical/close.json?start={start_date}&end={end_date}"
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        data = response.json().get('bpi', {})
        
        if not data:
            print("Nem érkezett adat az API-tól.")
            return

        # MÓDOSÍTÁS: A CoinDesk válaszának (dictionary) feldolgozása
        df = pd.DataFrame(list(data.items()), columns=['date', 'price'])
        df['crypto_id'] = CRYPTO_ID
        
        conn = sqlite3.connect(DB_FILE)
        df.to_sql('prices', conn, if_exists='replace', index=False)
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

