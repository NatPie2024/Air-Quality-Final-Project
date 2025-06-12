import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt

DB_PATH = os.path.join("data", "air_quality.db")

def plot_measurements(sensor_id, date_from=None, date_to=None, save_path=None):

    conn = sqlite3.connect(DB_PATH)

    # 🔍 Pobierz nazwę parametru
    cur = conn.cursor()
    cur.execute("SELECT param_name FROM sensors WHERE id = ?", (sensor_id,))
    result = cur.fetchone()

    if result:
        param_name = result[0]
    else:
        print("❌ Nie znaleziono parametru dla podanego sensor_id.")
        conn.close()
        return

    # 📥 Pobierz dane
    query = """
        SELECT date_time, value
        FROM measurements
        WHERE sensor_id = ?
        ORDER BY date_time
    """
    df = pd.read_sql_query(query, conn, params=(sensor_id,))
    conn.close()

    df["date_time"] = pd.to_datetime(df["date_time"])

    if date_from:
        df = df[df["date_time"] >= pd.to_datetime(date_from)]
    if date_to:
        df = df[df["date_time"] <= pd.to_datetime(date_to)]

    if df.empty:
        print("❌ Brak danych w podanym zakresie.")
        return

    # 📈 Rysuj wykres
    plt.figure(figsize=(10, 5))
    plt.plot(df["date_time"], df["value"], marker='o', linestyle='-', color='blue')
    plt.title(f"Stężenie {param_name}", fontsize=14)
    plt.xlabel("Data pomiaru", fontsize=12)
    plt.ylabel("Wartość [µg/m³]", fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(rotation=45)

    if save_path:
        plt.savefig(save_path)
        print(f"✅ Zapisano wykres do pliku: {save_path}")
        plt.close()
    else:
        plt.show()

