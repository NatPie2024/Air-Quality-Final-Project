from app.database import connect
import pandas as pd

def analyze_measurements_to_text(sensor_id, date_from=None, date_to=None):
    conn = connect()
    query = "SELECT value, date_time FROM measurements WHERE sensor_id = ? ORDER BY date_time"
    df = pd.read_sql_query(query, conn, params=(sensor_id,))
    conn.close()

    df["date_time"] = pd.to_datetime(df["date_time"])

    if date_from:
        df = df[df["date_time"] >= pd.to_datetime(date_from)]
    if date_to:
        df = df[df["date_time"] <= pd.to_datetime(date_to)]

    if df.empty:
        return "Brak danych do analizy."

    min_val = df["value"].min()
    max_val = df["value"].max()
    avg_val = df["value"].mean()

    min_time = df[df["value"] == min_val]["date_time"].iloc[0]
    max_time = df[df["value"] == max_val]["date_time"].iloc[0]

    trend = "wzrastający" if df["value"].iloc[-1] > df["value"].iloc[0] else "malejący"

    return (
        f"📊 Analiza danych:\n"
        f"🔻 Min: {min_val:.2f} µg/m³ o {min_time}\n"
        f"🔺 Max: {max_val:.2f} µg/m³ o {max_time}\n"
        f"⚖️  Średnia: {avg_val:.2f} µg/m³\n"
        f"📈 Trend: {trend}"
    )

