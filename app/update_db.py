# aktualizuję dane dotyczące sensorów
from datetime import datetime, timedelta
from app import api_GIOS
from app.database import get_stations_from_db, get_sensors_from_db, insert_measurement

def update_latest_measurements(days=3):
    """
    Aktualizuje dane pomiarowe z ostatnich dni (domyślnie 3).
    Pobiera z API tylko pomiary i zapisuje je do bazy danych.
    """
    updated_count = 0
    date_limit = datetime.now() - timedelta(days=days)

    # Pobierz wszystkie stacje z bazy
    stations = get_stations_from_db("")
    for station in stations:
        station_id = station["id"]
        sensors = get_sensors_from_db(station_id)

        for sensor in sensors:
            sensor_id = sensor["id"]
            data = api_GIOS.get_measurements_for_sensor(sensor_id)

            for m in data.get("values", []):
                if m["value"] is not None:
                    try:
                        measurement_date = datetime.strptime(m["date"], "%Y-%m-%d %H:%M:%S")
                        if measurement_date > date_limit:
                            insert_measurement(sensor_id, m)
                            updated_count += 1
                    except Exception as e:
                        print(f"❌ Błąd przy przetwarzaniu pomiaru: {e}")

    return updated_count

# Możesz też uruchomić ten plik samodzielnie
if __name__ == "__main__":
    print("🔄 Aktualizacja danych z ostatnich 3 dni...")
    count = update_latest_measurements()
    print(f"✅ Zaktualizowano {count} pomiarów.")

