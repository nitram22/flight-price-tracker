import csv
import json

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

    airline = offer_today["segments"][0]["legs"][0]["carriersData"][0]["name"]

    return {
        "date_str": offer_today["segments"][0]["departureTime"].split("T")[0],
        "price": round(total_price, 2),
        "airline": airline
    }

# ================================
# 2️⃣ CSV + JSON speichern
# ================================
def save_csv(data, file=CSV_FILE):
    fieldnames = ["date", "price", "airline"]
    try:
        with open(file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow({
                "date": data["date_str"],
                "price": data["price"],
                "airline": data["airline"]
            })
        print(f"Preis gespeichert: {data['price']} EUR am {data['date_str']}")
    except Exception as e:
        print("Fehler beim Speichern CSV:", e)

def save_json(data, file=JSON_FILE):
    try:
        with open(file, "w") as f:
            json.dump(data, f, indent=2)
        print("JSON aktualisiert.")
    except Exception as e:
        print("Fehler beim Speichern JSON:", e)

# ================================
# 3️⃣ Analyse + Chart
# ================================
def analyze_and_plot():
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=["date"])
    except Exception as e:
        print("CSV konnte nicht gelesen werden:", e)
        return

    if df.empty:
        print("Keine Daten zum Plotten.")
        return

    df = df.sort_values("date")
    x = np.arange(len(df))
    y = df["price"].values

    # Lineare Trendlinie
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)

    plt.figure(figsize=(10, 6))
    plt.plot(df["date"], y, marker='o', label="Preis")
    plt.plot(df["date"], p(x), linestyle="--", color="red", label="Trendlinie")
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