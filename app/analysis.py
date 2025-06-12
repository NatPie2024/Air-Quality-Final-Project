import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join("data", "air_quality.db")

def analyze_measurements(sensor_id, date_from=None, date_to=None):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT date_time, value
        FROM measurements
        WHERE sensor_id = ?
        ORDER BY date_time
    """
    df = pd.read_sql_query(query, conn, params=(sensor_id,))
    conn.close()

    df["date_time"] = pd.to_datetime(df["date_time"])
    df = df.dropna(subset=["value"])

    if date_from:
        df = df[df["date_time"] >= pd.to_datetime(date_from)]
    if date_to:
        df = df[df["date_time"] <= pd.to_datetime(date_to)]

    if df.empty:
        print("❌ Brak danych w podanym zakresie.")
        return

    min_val = df["value"].min()
    max_val = df["value"].max()
    avg_val = df["value"].mean()

    min_time = df[df["value"] == min_val]["date_time"].iloc[0]
    max_time = df[df["value"] == max_val]["date_time"].iloc[0]

    start_val = df["value"].iloc[0]
    end_val = df["value"].iloc[-1]
    if end_val > start_val:
        trend = "📈 rosnący"
    elif end_val < start_val:
        trend = "📉 malejący"
    else:
        trend = "➖ stabilny"

    print("\n📊 Analiza danych:")
    print(f"🔻 Min: {min_val:.2f} µg/m³ o {min_time}")
    print(f"🔺 Max: {max_val:.2f} µg/m³ o {max_time}")
    print(f"⚖️  Średnia: {avg_val:.2f} µg/m³")
    print(f"📈 Trend: {trend}")
