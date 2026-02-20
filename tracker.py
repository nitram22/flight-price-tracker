import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import csv
import sys

# =====================================
# API CONFIG
# =====================================

API_HOST = os.getenv("API_HOST")
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("API_KEY nicht gesetzt!")
    sys.exit(1)

URL = "https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlights"

QUERYSTRING = {
    "originSkyId": "STR",
    "destinationSkyId": "FNC",
    "originEntityId": "27539733",       # ggf prüfen
    "destinationEntityId": "27537558",  # ggf prüfen
    "departureDate": "2026-05-25",
    "returnDate": "2026-05-31",
    "cabinClass": "economy",
    "adults": "1",
    "sortBy": "best",
    "currency": "EUR",
    "market": "de-DE",
    "countryCode": "DE"
}

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

CSV_FILE = "flight_prices.csv"
CHART_FILE = "price_chart.png"

# =====================================
# 1️⃣ Preis abrufen
# =====================================

def fetch_price():
    response = requests.get(URL, headers=HEADERS, params=QUERYSTRING)
    response.raise_for_status()
    data = response.json()

    try:
        price = data["data"]["itineraries"][0]["price"]["raw"]
        return float(price)
    except (KeyError, IndexError):
        print("Preis konnte nicht extrahiert werden.")
        print(data)
        return None

# =====================================
# 2️⃣ Preis speichern
# =====================================

def save_price(price):
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), price])

# =====================================
# 3️⃣ Durchschnitt & Chart
# =====================================

def analyze_and_plot():
    df = pd.read_csv(CSV_FILE, header=None, names=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    avg_price = df["price"].mean()

    print(f"\nDurchschnittspreis: {avg_price:.2f} EUR")
    print(f"Min Preis: {df['price'].min():.2f} EUR")
    print(f"Max Preis: {df['price'].max():.2f} EUR")

    plt.figure()
    plt.plot(df["timestamp"], df["price"])
    plt.xlabel("Zeit")
    plt.ylabel("Preis (EUR)")
    plt.title("Preisentwicklung STR → FNC")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

    print("Chart gespeichert als:", CHART_FILE)

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
    generate_html()

# =====================================
# 4️⃣ HTML Seite generieren
# =====================================

def generate_html():
    df = pd.read_csv(CSV_FILE)
    avg_price = df["price"].mean()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Flight Price Tracker</title>
        <style>
            body {{
                font-family: Arial;
                margin: 40px;
                background-color: #f4f4f4;
            }}
            h1 {{
                color: #333;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                background: white;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #333;
                color: white;
            }}
            img {{
                max-width: 100%;
                height: auto;
                background: white;
                padding: 10px;
            }}
        </style>
    </head>
    <body>

        <h1>Flugpreis Tracker</h1>
        <h2>STR → FNC (25.05.2026 - 31.05.2026)</h2>

        <p><strong>Durchschnittspreis:</strong> {avg_price:.2f} EUR</p>

        <h3>Preisentwicklung</h3>
        <img src="price_chart.png" alt="Preisentwicklung">

        <h3>Historische Daten</h3>
        {df.to_html(index=False)}

    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("HTML Seite generiert.")


if __name__ == "__main__":
    main()