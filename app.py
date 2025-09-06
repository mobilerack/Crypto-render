# app.py
import requests
import pandas as pd
from flask import Flask, render_template
from sklearn.linear_model import LinearRegression
import sqlite3
import os
from datetime import datetime

# --- Konfiguráció ---
DATA_DIR = os.environ.get('RENDER_DISK_PATH', '.')
DB_FILE = os.path.join(DATA_DIR, 'crypto_data.db')
CRYPTO_ID = 'bitcoin'
VS_CURRENCY = 'usd'
# Beolvassuk az API kulcsot a környezeti változóból
API_KEY = os.environ.get('COINGECKO_API_KEY')

app = Flask(__name__)
# ... (a /healthz útvonal és a többi függvény változatlan, kivéve az update_database_from_api)

def update_database_from_api():
    """Már csak a legfrissebb, hiányzó adatokat tölti le, API kulccsal."""
    # ... (a függvény eleje változatlan)
    last_date = get_last_date_from_db()
    if not last_date: # ...
        return
    days_diff = (datetime.now().date() - last_date).days
    if days_diff <= 1: # ...
        return
    
    print(f"Adatbázis frissítése, {days_diff} napnyi adat letöltése...")
    url = f"https://api.coingecko.com/api/v3/coins/{CRYPTO_ID}/market_chart"
    
    # Hozzáadjuk az API kulcsot a kérés paramétereihez
    params = {
        'vs_currency': VS_CURRENCY,
        'days': days_diff,
        'interval': 'daily',
        'x_cg_demo_api_key': API_KEY
    }
    
    # Figyelem: Ha nincs API kulcs, a frissítés hiba nélkül átugrásra kerül
    if not API_KEY:
        print("API kulcs hiányzik, a napi frissítés kihagyva.")
        return

    try:
        response = requests.get(url, params=params, timeout=30)
        # ... (a függvény többi része változatlan)
        response.raise_for_status()
        data = response.json().get('prices', [])
        if not data:
            return
        df = pd.DataFrame(data, columns=['timestamp', 'price'])
        # ... (a df feldolgozása és mentése)
    except requests.exceptions.RequestException as e:
        print(f"Hiba a napi frissítés során: {e}")

# ... (a többi függvény, mint a train_and_predict és az index, változatlan)
# Az alábbiakban a teljesség kedvéért a teljes, helyes app.py szerepel.

# app.py TELJES KÓDJA

import requests
import pandas as pd
from flask import Flask, render_template
from sklearn.linear_model import LinearRegression
import sqlite3
import os
from datetime import datetime

DATA_DIR = os.environ.get('RENDER_DISK_PATH', '.')
DB_FILE = os.path.join(DATA_DIR, 'crypto_data.db')
CRYPTO_ID = 'bitcoin'
VS_CURRENCY = 'usd'
API_KEY = os.environ.get('COINGECKO_API_KEY')

app = Flask(__name__)

@app.route('/healthz')
def health_check():
    return "OK", 200

def load_data_from_db():
    if not os.path.exists(DB_FILE): return pd.DataFrame()
    conn = sqlite3.connect(DB_FILE)
    query = f"SELECT date, price FROM prices WHERE crypto_id='{CRYPTO_ID}' ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df

def get_last_date_from_db():
    if not os.path.exists(DB_FILE): return None
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(date) FROM prices WHERE crypto_id='{CRYPTO_ID}'")
    result = cursor.fetchone()[0]
    conn.close()
    return datetime.strptime(result, '%Y-%m-%d').date() if result else None

def update_database_from_api():
    last_date = get_last_date_from_db()
    if not last_date:
        print("Adatbázis üres, a normál frissítés nem fut le.")
        return
    days_diff = (datetime.now().date() - last_date).days
    if days_diff <= 1:
        print("Az adatbázis naprakész.")
        return
    
    if not API_KEY:
        print("API kulcs hiányzik, a napi frissítés kihagyva.")
        return
        
    print(f"Adatbázis frissítése, {days_diff} napnyi adat letöltése...")
    url = f"https://api.coingecko.com/api/v3/coins/{CRYPTO_ID}/market_chart"
    params = {'vs_currency': VS_CURRENCY, 'days': days_diff, 'interval': 'daily', 'x_cg_demo_api_key': API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get('prices', [])
        if not data: return
        df = pd.DataFrame(data, columns=['timestamp', 'price'])
        df = df.iloc[:-1] if len(df) > 1 else df
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d')
        df['crypto_id'] = CRYPTO_ID
        df = df[['crypto_id', 'date', 'price']]
        conn = sqlite3.connect(DB_FILE)
        df.to_sql('prices', conn, if_exists='append', index=False)
        conn.close()
        print(f"{len(df)} új adatpont mentve.")
    except requests.exceptions.RequestException as e:
        print(f"Hiba a napi frissítés során: {e}")

def train_and_predict(df):
    if df is None or len(df) < 2: return 0
    df['target'] = df['price'].shift(-1)
    df.dropna(inplace=True)
    X = df[['price']]
    y = df['target']
    model = LinearRegression()
    model.fit(X, y)
    last_known_price = df[['price']].iloc[-1].values.reshape(1, -1)
    prediction = model.predict(last_known_price)
    return prediction[0]

@app.route('/')
def index():
    update_database_from_api()
    crypto_df = load_data_from_db()
    if crypto_df.empty or len(crypto_df) < 10:
        error_message = "Nincs elegendő adat az adatbázisban. A telepítés valószínűleg sikertelen volt, vagy még folyamatban van."
        return render_template('index.html', error=error_message)
    predicted_price = train_and_predict(crypto_df.copy())
    chart_data = crypto_df.tail(90)
    labels = [date.strftime('%Y-%m-%d') for date in chart_data['date']]
    prices = [price for price in chart_data['price']]
    return render_template('index.html', prediction=predicted_price, labels=labels, prices=prices)

if __name__ == '__main__':
    app.run(debug=True)
