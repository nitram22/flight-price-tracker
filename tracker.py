import csv
import json
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

API_HOST = "booking-com15.p.rapidapi.com"
API_KEY = os.getenv("API_KEY")

URL = f"https://booking-com15.p.rapidapi.com/api/v1/flights/searchFlights"

PARAMS = {
    "fromId": "FRA.AIRPORT",
    "toId": "FNC.AIRPORT",
    "departDate": "2026-05-25",
    "returnDate": "2026-05-31",
    "stops": "none",
    "pageNo": 1,
    "adults": 2,
    "sort": "BEST",
    "cabinClass": "ECONOMY",
    "currency_code": "EUR"
}

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

CSV_FILE = "flight_prices.csv"
JSON_FILE = "data.json"
CHART_FILE = "price_chart.png"


# ================================
# 1️⃣ Preis abrufen
# ================================
def fetch_price(params=PARAMS):
    try:
        response = requests.get(URL, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Fehler beim Abrufen der API:", e)
        return None

    if not data.get("status"):
        print("API Status False:", data)
        return None

    flight_offers = data.get("data", {}).get("flightOffers", [])
    if not flight_offers:
        print("Keine Flugangebote gefunden.")
        return None

    # exact departDate filtern
    offer_today = None
    for offer in flight_offers:
        depart_date = offer["segments"][0]["departureTime"].split("T")[0]
        if depart_date == params["departDate"]:
            offer_today = offer
            break

    if not offer_today:
        print("Kein Angebot am gewünschten Datum.")
        return None

    price_total = offer_today.get("priceBreakdown", {}).get("total")
    if not price_total:
        print("Kein Preis im Angebot gefunden.")
        return None

    units = price_total.get("units", 0)
    nanos = price_total.get("nanos", 0)
    total_price = units + nanos / 1_000_000_000

    # Preis pro Person
    adults = params.get("adults", 1)
    per_person_price = round(total_price / adults, 2)

    airline = offer_today["segments"][0]["legs"][0]["carriersData"][0]["name"]

    # aktuelle Uhrzeit für den Abruf
    now = datetime.now() + timedelta(hours=0)  # hier ggf. Zeitzone anpassen
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")

    return {
        "timestamp": timestamp,
        "price": per_person_price,
        "airline": airline
    }


# ================================
# 2️⃣ CSV + JSON speichern
# ================================
def save_csv(data, file=CSV_FILE):
    fieldnames = ["timestamp", "price", "airline"]
    try:
        with open(file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow({
                "timestamp": data["timestamp"],
                "price": data["price"],
                "airline": data["airline"]
            })
        print(f"Preis gespeichert: {data['price']} EUR am {data['timestamp']}")
    except Exception as e:
        print("Fehler beim Speichern CSV:", e)


def save_json(data, file=JSON_FILE):
    history = []

    # alte Daten einlesen
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                existing = json.load(f)
                history = existing.get("history", [])
        except Exception:
            pass

    # neuen Punkt anhängen
    history.append([data["timestamp"], data["price"], data["airline"]])

    prices = [p[1] for p in history]
    avg_price = round(sum(prices) / len(prices), 2)
    min_price = round(min(prices), 2)
    max_price = round(max(prices), 2)

    json_data = {
        "last_price": data["price"],
        "airline": data["airline"],
        "history": history,
        "average_price": avg_price,
        "min_price": min_price,
        "max_price": max_price
    }

    try:
        with open(file, "w") as f:
            json.dump(json_data, f, indent=2)
        print("JSON aktualisiert.")
    except Exception as e:
        print("Fehler beim Speichern JSON:", e)


# ================================
# 3️⃣ Analyse + Chart
# ================================
def analyze_and_plot():
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
    except Exception as e:
        print("CSV konnte nicht gelesen werden:", e)
        return

    if df.empty:
        print("Keine Daten zum Plotten.")
        return

    df = df.sort_values("timestamp")
    x = np.arange(len(df))
    y = df["price"].values

    # Trendlinie nur wenn mehr als 1 Punkt
    if len(df) > 1:
        try:
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
        except Exception as e:
            print("Fehler Trendlinie:", e)
            p = lambda x: np.zeros_like(x)
    else:
        p = lambda x: y[0]

    plt.figure(figsize=(10, 6))
    plt.plot(df["timestamp"], y, marker='o', label="Preis pro Person")
    plt.plot(df["timestamp"], p(x), linestyle="--", color="red", label="Trendlinie")
    plt.xlabel("Datum")
    plt.ylabel("Preis in EUR")
    plt.title("Flugpreis-Entwicklung")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    print(f"Chart gespeichert: {CHART_FILE}")
    plt.close()


# ================================
# 4️⃣ Main
# ================================
def main():
    result = fetch_price()
    if result:
        save_csv(result)
        save_json(result)
    analyze_and_plot()


if __name__ == "__main__":
    main()