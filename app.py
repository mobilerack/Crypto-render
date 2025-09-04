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

# Flask alkalmazás inicializálása
app = Flask(__name__)

# --- Adatbázis-kezelő Függvények ---
def init_db():
    # Ez a függvény változatlan
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
    print("Adatbázis sikeresen inicializálva.")

# JAVÍTÁS: Eltávolítottuk a @app.before_first_request dekorátort,
# és közvetlenül itt hívjuk meg az init_db() függvényt.
# Ez a kód lefut, amikor a Gunicorn betölti az alkalmazást,
# így az adatbázis garantáltan létezni fog az első kérés előtt.
init_db()

def save_data_to_db(df):
    conn = sqlite3.connect(DB_FILE)
    df.to_sql('prices', conn, if_exists='append', index=False)
    conn.close()

def load_data_from_db():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_FILE)
    query = f"SELECT date, price FROM prices WHERE crypto_id='{CRYPTO_ID}' ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df

def get_last_date_from_db():
    if not os.path.exists(DB_FILE):
        return None
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(date) FROM prices WHERE crypto_id='{CRYPTO_ID}'")
    result = cursor.fetchone()[0]
    conn.close()
    return datetime.strptime(result, '%Y-%m-%d').date() if result else None

# --- Adatgyűjtés és Frissítés ---
def update_database_from_api():
    last_date = get_last_date_from_db()
    days_to_fetch = 'max'
    if last_date:
        days_diff = (datetime.now().date() - last_date).days
        if days_diff > 1:
            days_to_fetch = days_diff
        else:
            print("Az adatbázis naprakész.")
            return
    print(f"Adatok letöltése... ({days_to_fetch} nap)")
    url = f"https://api.coingecko.com/api/v3/coins/{CRYPTO_ID}/market_chart"
    params = {'vs_currency': VS_CURRENCY, 'days': days_to_fetch, 'interval': 'daily'}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get('prices', [])
        if not data:
            return
        df = pd.DataFrame(data, columns=['timestamp', 'price'])
        df = df.iloc[:-1] if len(df) > 1 else df
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d')
        df['crypto_id'] = CRYPTO_ID
        df = df[['crypto_id', 'date', 'price']]
        save_data_to_db(df)
        print(f"{len(df)} új adatpont mentve.")
    except requests.exceptions.RequestException as e:
        print(f"Hiba az API hívás során: {e}")

# --- Gépi Tanulási Modell ---
def train_and_predict(df):
    if df is None or len(df) < 2:
        return 0
    df['target'] = df['price'].shift(-1)
    df.dropna(inplace=True)
    X = df[['price']]
    y = df['target']
    model = LinearRegression()
    model.fit(X, y)
    last_known_price = df[['price']].iloc[-1].values.reshape(1, -1)
    prediction = model.predict(last_known_price)
    return prediction[0]

# --- Flask Útvonal (Route) ---
@app.route('/')
def index():
    update_database_from_api()
    crypto_df = load_data_from_db()
    predicted_price = train_and_predict(crypto_df.copy())
    chart_data = crypto_df.tail(90)
    labels = [date.strftime('%Y-%m-%d') for date in chart_data['date']]
    prices = [price for price in chart_data['price']]
    return render_template('index.html', prediction=predicted_price, labels=labels, prices=prices)

# --- Alkalmazás Indítása ---
if __name__ == '__main__':
    app.run(debug=True)

