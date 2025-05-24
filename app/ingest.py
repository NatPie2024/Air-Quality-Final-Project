from app import api_GIOS, database

def download_and_save_data(limit=3):
    print("⏬ Pobieranie listy stacji z API GIOŚ...")
    stations = api_GIOS.get_all_stations()

    if not stations:
        print("❌ Nie udało się pobrać danych ze stacji.")
        return

    for station in stations[:limit]:  # pobieramy tylko kilka stacji (np. 3)
        print(f"\n📍 Stacja: {station['stationName']} ({station['city']['name']})")

        # Zapis stacji do bazy
        database.insert_station(station)

        # Pobierz sensory (czujniki) stacji
        sensors = api_GIOS.get_sensors_for_station(station['id'])

        for sensor in sensors:
            param_name = sensor['param']['paramName']
            print(f"  🔎 Sensor: {param_name}")

            # Zapis sensora do bazy
            database.insert_sensor(sensor, station['id'])

            # Pobierz dane z sensora
            measurements = api_GIOS.get_measurements_for_sensor(sensor['id'])

            if not measurements.get("values"):
                print("    ⚠️  Brak danych pomiarowych.")
                continue

            # Zapis pomiarów do bazy
            for m in measurements["values"]:
                database.insert_measurement(sensor['id'], m)

    print("\n✅ Dane zostały pobrane i zapisane do bazy SQLite.")
