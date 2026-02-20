import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta
import os

# ==============================
# API KONFIGURATION
# ==============================

API_HOST = "DEIN_API_HOST"
API_KEY = "DEIN_API_KEY"

HEADERS = {
    "X-RapidAPI-Host": API_HOST,
    "X-RapidAPI-Key": API_KEY
}

BASE_URL = "https://apiheya/api/sky-scrapper/flights"

origin = "STR"
destination = "FNC"
depart_date = "2026-05-25"
return_date = "2026-05-31"

CSV_FILE = "flight_prices.csv"

# ==============================
# FUNKTION ZUM ABRUFEN
# ==============================

def get_price():
    params = {
        "origin": origin,
        "destination": destination,
        "departDate": depart_date,
        "returnDate": return_date
    }

    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()

    # Preis extrahieren (anpassen falls API anders strukturiert ist)
    price = data["data"][0]["price"]

    return price

# ==============================
# SPEICHERN DER DATEN
# ==============================

def save_price(price):
    now = datetime.now()

    df = pd.DataFrame([{
        "timestamp": now,
        "price": price
    }])

    if not os.path.isfile(CSV_FILE):
        df.to_csv(CSV_FILE, index=False)
    else:
        df.to_csv(CSV_FILE, mode='a', header=False, index=False)

# ==============================
# AUSWERTUNG
# ==============================

def analyze_data():
    df = pd.read_csv(CSV_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    avg_price = df["price"].mean()
    print(f"\nDurchschnittspreis über 5 Tage: {avg_price:.2f} €")

    plt.figure()
    plt.plot(df["timestamp"], df["price"])
    plt.xlabel("Zeit")
    plt.ylabel("Preis (€)")
    plt.title("Preisentwicklung STR → FNC")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# ==============================
# HAUPTSCHLEIFE (5 TAGE)
# ==============================

def run_tracker():
    start_time = datetime.now()
    end_time = start_time + timedelta(days=5)

    requests_per_day = 4
    interval_hours = 24 / requests_per_day   # = 6 Stunden
    interval_seconds = interval_hours * 3600

    total_requests = 0

    while datetime.now() < end_time and total_requests < 20:
        try:
            print(f"Abfrage #{total_requests + 1} - {datetime.now()}")
            price = get_price()
            print(f"Gefundener Preis: {price} €")

            save_price(price)
            total_requests += 1

        except Exception as e:
            print("Fehler bei API-Abfrage:", e)

        if total_requests >= 20:
            break

        time.sleep(interval_seconds)

    print("\nTracking abgeschlossen.")
    analyze_data()

# ==============================
# START
# ==============================

if __name__ == "__main__":
    run_tracker()