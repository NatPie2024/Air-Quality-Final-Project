from app import api_GIOS
from app.database import create_tables, insert_station, insert_sensor, insert_measurement

def fetch_and_save_all_data():
    # Utworzenie tabel w bazie danych (jeśli nie istnieją)
    create_tables()

    # Pobranie listy wszystkich stacji z API GIOŚ
    stations = api_GIOS.get_all_stations()
    print(f"Znaleziono {len(stations)} stacji.")

    for station in stations:
        # Zapis stacji do bazy danych
        insert_station(station)
        station_id = station["id"]
        print(f"\nStacja: {station['stationName']} ({station['city']['name']})")

        # Pobranie listy sensorów dla danej stacji
        sensors = api_GIOS.get_sensors_for_station(station_id)
        if not sensors:
            print("   Brak sensorów.")
            continue

        for sensor in sensors:
            # Zapis sensora do bazy
            insert_sensor(sensor, station_id)
            sensor_id = sensor["id"]
            print(f"   Sensor: {sensor['param']['paramName']}")

            # Pobranie danych pomiarowych z sensora
            measurements = api_GIOS.get_measurements_for_sensor(sensor_id)
            count = 0
            for m in measurements.get("values", []):
                insert_measurement(sensor_id, m)
                count += 1

            print(f"   Zapisano {count} pomiarów.")


    print("Wszystkie dane zostały pobrane i zapisane do bazy danych.")

if __name__ == "__main__":
    fetch_and_save_all_data()
