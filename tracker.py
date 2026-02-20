import requests
import os
import json
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
    "originEntityId": "27539733",
    "destinationEntityId": "27537558",
    "date": "2026-05-25",
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
    generate_modern_site()

# =====================================
# 4️⃣ JSON + Moderne HTML generieren
# =====================================

def generate_modern_site():
    df = pd.read_csv(CSV_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    avg_price = df["price"].mean()
    min_price = df["price"].min()
    max_price = df["price"].max()

    # JSON Daten für Chart
    data_json = {
        "labels": df["timestamp"].dt.strftime("%Y-%m-%d %H:%M").tolist(),
        "prices": df["price"].tolist(),
        "avg": round(avg_price, 2),
        "min": round(min_price, 2),
        "max": round(max_price, 2)
    }

    with open("data.json", "w") as f:
        json.dump(data_json, f)

    html_content = """
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flight Price Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #121212;
    color: white;
}
.container {
    max-width: 1100px;
    margin: auto;
    padding: 20px;
}
h1 {
    text-align: center;
}
.stats {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin-bottom: 30px;
}
.card {
    flex: 1;
    min-width: 150px;
    background: #1f1f1f;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}
canvas {
    background: #1f1f1f;
    border-radius: 10px;
    padding: 10px;
}
footer {
    margin-top: 40px;
    text-align: center;
    font-size: 12px;
    opacity: 0.6;
}
</style>
</head>
<body>

<div class="container">
    <h1>✈ Flugpreis Tracker</h1>
    <p style="text-align:center;">STR → FNC (25.05.2026 - 31.05.2026)</p>

    <div class="stats">
        <div class="card">
            <h3>Durchschnitt</h3>
            <p id="avg"></p>
        </div>
        <div class="card">
            <h3>Minimum</h3>
            <p id="min"></p>
        </div>
        <div class="card">
            <h3>Maximum</h3>
            <p id="max"></p>
        </div>
    </div>

    <canvas id="priceChart"></canvas>

    <footer>
        Automatisch aktualisiert über GitHub Actions
    </footer>
</div>

<script>
fetch('data.json')
.then(response => response.json())
.then(data => {

    document.getElementById("avg").innerText = data.avg + " EUR";
    document.getElementById("min").innerText = data.min + " EUR";
    document.getElementById("max").innerText = data.max + " EUR";

    const ctx = document.getElementById('priceChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Preis (EUR)',
                data: data.prices,
                borderColor: '#4CAF50',
                tension: 0.2,
                fill: false
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: {
                    ticks: { color: 'white' }
                },
                y: {
                    ticks: { color: 'white' }
                }
            }
        }
    });

});
</script>

</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Moderne Webseite generiert.")


if __name__ == "__main__":
    main()