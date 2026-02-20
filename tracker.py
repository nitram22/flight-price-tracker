import csv
from datetime import datetime, timedelta
import json
import os
import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ================================
# Konfiguration
# ================================
API_HOST = "booking-com15.p.rapidapi.com"
API_KEY = os.getenv("API_KEY")

URL = f"https://booking-com15.p.rapidapi.com/api/v1/flights/searchFlights"

PARAMS = {
    "fromId": "FRA.AIRPORT",
    "toId": "FNC.AIRPORT",
    "departDate": "2026-05-25",
    "returnDate": "2026-05-31",
    "stops": "0",
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

    # exaktes departDate filtern
    offer_today = None
    for offer in flight_offers:
        depart_time = offer["segments"][0]["departureTime"]
        depart_date = depart_time.split("T")[0]
        if depart_date == params["departDate"]:
            offer_today = offer
            break

    if not offer_today:
        print("Kein Angebot am gewünschten Datum.")
        return None

    # Gesamtpreis
    price_total = offer_today.get("priceBreakdown", {}).get("total")
    if not price_total:
        print("Kein Preis im Angebot gefunden.")
        return None

    units = price_total.get("units", 0)
    nanos = price_total.get("nanos", 0)
    total_price = units + nanos / 1_000_000_000

    airline = offer_today["segments"][0]["legs"][0]["carriersData"][0]["name"]
    departure_time = offer_today["segments"][0]["departureTime"]  # ISO datetime

    return {
        "date_str": departure_time,
        "price": round(total_price, 2),
        "airline": airline
    }

# ================================
# 2️⃣ CSV speichern
# ================================
def save_csv(data, file=CSV_FILE):
    fieldnames = ["date", "time", "price", "airline"]
    date_part = data["date_str"].split("T")[0]
    time_part = data["date_str"].split("T")[1] if "T" in data["date_str"] else ""

    try:
        with open(file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow({
                "date": date_part,
                "time": time_part,
                "price": round(data["price"]/2,2),  # pro Person
                "airline": data["airline"]
            })
        print(f"Preis gespeichert: {round(data['price']/2,2)} EUR pro Person am {date_part} {time_part}")
    except Exception as e:
        print("Fehler beim Speichern CSV:", e)

# ================================
# 3️⃣ JSON speichern
# ================================
def save_json(data, file=JSON_FILE):
    # aktuellen Abrufzeitpunkt
    now = datetime.now() + timedelta(hours=1)

    # Preis pro Person berechnen
    price_per_person = round(data["price"] / 2, 2)

    data_to_save = {
        "last_price": price_per_person,
        "airline": data["airline"],
        "history": [
            [
                now.strftime("%Y-%m-%dT%H:%M:%S"),  # Abrufzeitpunkt
                price_per_person,
                data["airline"]
            ]
        ],
        "average_price": price_per_person,
        "min_price": price_per_person,
        "max_price": price_per_person
    }

    try:
        with open(file, "w") as f:
            json.dump(data_to_save, f, indent=2)
        print("JSON aktualisiert.")
    except Exception as e:
        print("Fehler beim Speichern JSON:", e)

# ================================
# 4️⃣ Analyse + Chart
# ================================
def analyze_and_plot():
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=[["date","time"]])
    except Exception as e:
        print("CSV konnte nicht gelesen werden:", e)
        return

    if df.empty:
        print("Keine Daten zum Plotten.")
        return

    df = df.sort_values("date_time")
    x = np.arange(len(df))
    y = df["price"].values

    if len(y) < 2:
        print("Zu wenige Daten für Trendlinie.")
        plt.figure(figsize=(10,6))
        plt.plot(df["date_time"], y, marker='o')
        plt.savefig(CHART_FILE)
        plt.close()
        return

    try:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
    except np.linalg.LinAlgError:
        print("Trendlinie konnte nicht berechnet werden.")
        p = None

    plt.figure(figsize=(10, 6))
    plt.plot(df["date_time"], y, marker='o', label="Preis pro Person")
    if p is not None:
        plt.plot(df["date_time"], p(x), linestyle="--", color="red", label="Trendlinie")
    plt.xlabel("Datum / Zeit")
    plt.ylabel("Preis in EUR")
    plt.title("Flugpreis-Entwicklung FRA → FNC")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()
    print(f"Chart gespeichert: {CHART_FILE}")

# ================================
# 5️⃣ Main
# ================================
def main():
    result = fetch_price()
    if result:
        save_csv(result)
        save_json(result)
    analyze_and_plot()

if __name__ == "__main__":
    main()