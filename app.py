# app.py

import requests
import pandas as pd
from flask import Flask, render_template
from sklearn.linear_model import LinearRegression
import sqlite3
import os
from datetime import datetime, timedelta

# --- Konfiguráció ---
DATA_DIR = os.environ.get('RENDER_DISK_PATH', '.')
DB_FILE = os.path.join(DATA_DIR, 'crypto_data.db')
CRYPTO_ID = 'BTC' # A CoinDesk API a Bitcoinra (BPI) van specializálódva

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
    if not df.empty:
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
    """A hiányzó adatokat tölti le a CoinDesk-ről."""
    last_date = get_last_date_from_db()
    if not last_date:
        print("Adatbázis üres, a normál frissítés nem fut le.")
        return
    
    today = datetime.now().date()
    # Ha az utolsó dátum a tegnapi vagy a mai, akkor naprakészek vagyunk
    if last_date >= today - timedelta(days=1):
        print("Az adatbázis naprakész.")
        return
        
    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    print(f"Adatbázis frissítése, {start_date} és {end_date} közötti adatok letöltése...")
    # MÓDOSÍTÁS: CoinDesk API URL és dátum alapú paraméterek
    url = f"https://api.coindesk.com/v1/bpi/historical/close.json?start={start_date}&end={end_date}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json().get('bpi', {})
        if not data: 
            print("Nincs új adat a frissítéshez.")
            return
        
        # MÓDOSÍTÁS: A CoinDesk válaszának feldolgozása
        df = pd.DataFrame(list(data.items()), columns=['date', 'price'])
        df['crypto_id'] = CRYPTO_ID
        
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

