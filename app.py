import requests
import pandas as pd
from flask import Flask, render_template
from sklearn.linear_model import LinearRegression
import sqlite3
import os
from datetime import datetime

# --- Konfiguráció ---
# Az adatokat a Render által csatolt perzisztens lemezen tároljuk a '/data' mappában.
# A getenv második argumentuma (' . ') a helyi futtatáshoz kell, hogy az adatbázist
# az aktuális mappában hozza létre, ha a RENDER_DISK_PATH változó nem létezik.
DATA_DIR = os.environ.get('RENDER_DISK_PATH', '.')
DB_FILE = os.path.join(DATA_DIR, 'crypto_data.db') # Az adatbázis teljes útvonala
CRYPTO_ID = 'bitcoin'      # Az elemzendő kriptovaluta
VS_CURRENCY = 'usd'        # A pénznem, amiben az árat kérjük

# Flask alkalmazás inicializálása
app = Flask(__name__)

# --- 1. Adatbázis-kezelő Függvények ---

def init_db():
    """Létrehozza az adatbázis táblát, ha még nem létezik."""
    # Biztosítjuk, hogy a /data mappa létezik a Renderen, mielőtt az adatbázist létrehoznánk
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # A tábla létrehozásánál a (crypto_id, date) pár együttesen egyedi,
    # így elkerüljük a duplikált bejegyzéseket.
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

def save_data_to_db(df):
    """Elmenti a DataFrame tartalmát az adatbázisba, a duplikátumokat ignorálja."""
    conn = sqlite3.connect(DB_FILE)
    # Az 'append' és a táblában lévő UNIQUE constraint együtt biztosítja,
    # hogy csak az új adatok kerüljenek beillesztésre.
    df.to_sql('prices', conn, if_exists='append', index=False)
    conn.close()

def load_data_from_db():
    """Betölti az összes adatot az adatbázisból egy Pandas DataFrame-be."""
    if not os.path.exists(DB_FILE):
        return pd.DataFrame() # Üres DataFrame, ha az adatbázis még nem létezik

    conn = sqlite3.connect(DB_FILE)
    query = f"SELECT date, price FROM prices WHERE crypto_id='{CRYPTO_ID}' ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    # A dátumokat megfelelő formátumra alakítjuk
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df

def get_last_date_from_db():
    """Lekérdezi az utolsó rögzített dátumot az adatbázisból."""
    if not os.path.exists(DB_FILE):
        return None

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(date) FROM prices WHERE crypto_id='{CRYPTO_ID}'")
    result = cursor.fetchone()[0]
    conn.close()
    return datetime.strptime(result, '%Y-%m-%d').date() if result else None

# --- 2. Adatgyűjtés és Frissítés ---

def update_database_from_api():
    """
    Letölti a hiányzó adatokat az API-ról és frissíti az adatbázist.
    Ha az adatbázis üres, a maximálisan elérhető adatmennyiséget tölti le.
    """
    last_date = get_last_date_from_db()
    days_to_fetch = 'max' # Alapértelmezett: a teljes historikus adat letöltése

    if last_date:
        days_diff = (datetime.now().date() - last_date).days
        if days_diff > 1:
            days_to_fetch = days_diff
        else:
            print("Az adatbázis naprakész, nincs szükség API hívásra.")
            return # Nincs mit letölteni

    print(f"Adatok letöltése a CoinGecko API-ról... ({days_to_fetch} nap)")
    url = f"https://api.coingecko.com/api/v3/coins/{CRYPTO_ID}/market_chart"
    params = {'vs_currency': VS_CURRENCY, 'days': days_to_fetch, 'interval': 'daily'}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # Hibát dob, ha a HTTP kérés sikertelen
        data = response.json().get('prices', []) # A .get() megvéd a hibától, ha nincs 'prices' kulcs
        
        if not data:
            print("Az API nem adott vissza adatot.")
            return

        df = pd.DataFrame(data, columns=['timestamp', 'price'])
        # Az utolsó adatpont a mai, még nem lezárt nap, ezt kihagyjuk
        df = df.iloc[:-1] if len(df) > 1 else df
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d')
        df['crypto_id'] = CRYPTO_ID
        df = df[['crypto_id', 'date', 'price']]
        
        save_data_to_db(df)
        print(f"{len(df)} új adatpont mentve az adatbázisba.")
        
    except requests.exceptions.RequestException as e:
        print(f"Hiba az API hívás során: {e}")

# --- 3. Gépi Tanulási Modell ---

def train_and_predict(df):
    """Betanít egy egyszerű lineáris regressziós modellt és jósol egy értéket."""
    if df is None or len(df) < 2:
        return 0

    # Feature Engineering: A 'target' oszlop a következő napi ár lesz.
    df['target'] = df['price'].shift(-1)
    df.dropna(inplace=True)

    # Bemenet (X): a mai ár. Cél (y): a holnapi ár.
    X = df[['price']]
    y = df['target']
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Jóslás a következő napra az utolsó ismert ár alapján
    last_known_price = df[['price']].iloc[-1].values.reshape(1, -1)
    prediction = model.predict(last_known_price)
    
    return prediction[0]

# --- 4. Flask Útvonal (Route) ---

@app.route('/')
def index():
    """A főoldal, ami kezeli az adatbázis-frissítést és a megjelenítést."""
    update_database_from_api()

    crypto_df = load_data_from_db()

    predicted_price = train_and_predict(crypto_df.copy())

    # Adatok előkészítése a grafikonhoz (az utolsó 90 napot jelenítjük meg)
    chart_data = crypto_df.tail(90)
    labels = [date.strftime('%Y-%m-%d') for date in chart_data['date']]
    prices = [price for price in chart_data['price']]
    
    return render_template('index.html', 
                           prediction=predicted_price, 
                           labels=labels, 
                           prices=prices)

# --- Alkalmazás Indítása ---

if __name__ == '__main__':
    init_db()  # Adatbázis inicializálása az alkalmazás indításakor
    app.run(debug=True)

