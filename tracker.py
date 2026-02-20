import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import csv
import sys
import json
import numpy as np

# =====================================
# API CONFIG
# =====================================

API_HOST = "booking-com15.p.rapidapi.com"
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("API_KEY nicht gesetzt!")
    sys.exit(1)

URL = "https://booking-com15.p.rapidapi.com/api/v1/flights/getMinPrice"

PARAMS = {
    "fromId": "FRA.AIRPORT",
    "toId": "FNC.AIRPORT",
    "departDate": "2026-05-25",
    "returnDate": "2026-05-31",
    "cabinClass": "ECONOMY",
    "currency_code": "EUR"
}

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

CSV_FILE = "flight_prices.csv"
CHART_FILE = "price_chart.png"
JSON_FILE = "data.json"

# =====================================
# 1️⃣ Preis abrufen
# =====================================

def fetch_price():
    response = requests.get(URL, headers=HEADERS, params=PARAMS)
    response.raise_for_status()
    data = response.json()

    if not data.get("status"):
        print("API Fehler:", data)
        return None

    for entry in data["data"]:
        if entry["offsetDays"] == 0:
            units = entry["price"]["units"]
            nanos = entry["price"]["nanos"]
            return float(units + nanos / 1_000_000_000)

    return None


# =====================================
# 2️⃣ Preis speichern
# =====================================

def save_price(price):
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["timestamp", "price"])

        writer.writerow([datetime.now(), price])


# =====================================
# 3️⃣ Analyse & Chart
# =====================================

def analyze_and_plot():
    df = pd.read_csv(CSV_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    avg_price = df["price"].mean()
    min_price = df["price"].min()
    max_price = df["price"].max()

    # Gleitender Durchschnitt (3 Werte)
    df["moving_avg"] = df["price"].rolling(window=3).mean()

    # Trendlinie
    x = np.arange(len(df))
    z = np.polyfit(x, df["price"], 1)
    trend = np.poly1d(z)
    df["trend"] = trend(x)

    # Plot
    plt.figure()
    plt.plot(df["timestamp"], df["price"])
    plt.plot(df["timestamp"], df["moving_avg"])
    plt.plot(df["timestamp"], df["trend"])
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

    # JSON für Website
    output = {
        "last_price": float(df["price"].iloc[-1]),
        "average_price": float(avg_price),
        "min_price": float(min_price),
        "max_price": float(max_price),
        "last_updated": str(datetime.now()),
        "history": df[["timestamp", "price"]].astype(str).values.tolist()
    }

    with open(JSON_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print("Analyse abgeschlossen.")


# =====================================
# MAIN
# =====================================

def main():
    print("Starte Preisabfrage:", datetime.now())

    price = fetch_price()

    if price is None:
        print("Kein Preis gespeichert.")
        return

    print("Gefundener Preis:", price, "EUR")

    save_price(price)
    analyze_and_plot()


if __name__ == "__main__":
    main()