from flask import Flask, render_template

# Flask alkalmazás inicializálása
app = Flask(__name__)

# Főoldal útvonalának (route) definiálása
@app.route('/')
def home():
    # Adatok, amiket átadunk a HTML sablonnak
    # A korábbi hibás sort javítottuk, és most egyszerű adatokat adunk át
    kripto_adatok = {
        'nev': 'Bitcoin',
        'ticker': 'BTC',
        'ar': 45000  # Példa adat
    }
    
    # Az 'index.html' sablon renderelése és az adatok átadása
    return render_template('index.html', crypto=kripto_adatok)

# Fontos: A 'app.run()' részt NEM kell ideírni,
# mert a Gunicorn szerver felelős az alkalmazás futtatásáért!
