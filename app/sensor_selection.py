from app import api_GIOS

def select_sensor_from_station(station_id):
    """
    Interaktywny wybór sensora z terminala dla danej stacji.
    """
    sensors = api_GIOS.get_sensors_for_station(station_id)

    if not sensors:
        print("Brak sensorów dla tej stacji.")
        return None

    print(f"\nCzujniki dostępne w stacji ID: {station_id}")
    for sensor in sensors:
        param = sensor.get("param", {})
        print(f"  ID: {sensor['id']} | {param.get('paramName')} ({param.get('paramFormula')})")

    try:
        selected_id = int(input("\nPodaj ID czujnika: "))
    except ValueError:
        print("Niepoprawny numer.")
        return None

    selected_sensor = next((s for s in sensors if s["id"] == selected_id), None)
    if not selected_sensor:
        print("Nie znaleziono czujnika o podanym ID.")
        return None

    return selected_sensor


def get_sensors_for_station(station_id):
    """
    Zwraca listę sensorów w danej stacji (dla GUI).
    """
    return api_GIOS.get_sensors_for_station(station_id)

