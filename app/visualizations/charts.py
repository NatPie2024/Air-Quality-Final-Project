import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt

DB_PATH = os.path.join("data", "air_quality.db")

def plot_measurements(sensor_id, date_from=None, date_to=None):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT date_time, value
        FROM measurements
        WHERE sensor_id = ?
        ORDER BY date_time
    """
    df = pd.read_sql_query(query, conn, params=(sensor_id,))
    conn.close()

    if df.empty:
        print("❌ Brak danych dla wybranego czujnika.")
        return

    df["date_time"] = pd.to_datetime(df["date_time"])

    if date_from:
        df = df[df["date_time"] >= pd.to_datetime(date_from)]
    if date_to:
        df = df[df["date_time"] <= pd.to_datetime(date_to)]

    if df.empty:
        print("❌ Brak danych w podanym zakresie dat.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(df["date_time"], df["value"], marker='o')
    plt.title(f"Pomiary sensora ID {sensor_id}")
    plt.xlabel("Data")
    plt.ylabel("Wartość pomiaru")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
