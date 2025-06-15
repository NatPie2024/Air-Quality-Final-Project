import logging
from app import api_GIOS

# Logger setup
logger = logging.getLogger("SensorSelection")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def select_sensor_from_station(station_id):
    """
    Interaktywny wybór sensora z terminala dla danej stacji.
    """
    logger.info(f"Rozpoczynanie wyboru sensora dla stacji ID: {station_id}")
    sensors = api_GIOS.get_sensors_for_station(station_id)

    if not sensors:
        logger.warning(f"Brak sensorów dla stacji ID: {station_id}")
        print("Brak sensorów dla tej stacji.")
        return None

    print(f"\nCzujniki dostępne w stacji ID: {station_id}")
    for sensor in sensors:
        param = sensor.get("param", {})
        print(f"  ID: {sensor['id']} | {param.get('paramName')} ({param.get('paramFormula')})")

    try:
        selected_id = int(input("\nPodaj ID czujnika: "))
    except ValueError:
        logger.warning("Niepoprawny numer czujnika podany przez użytkownika")
        print("Niepoprawny numer.")
        return None

    selected_sensor = next((s for s in sensors if s["id"] == selected_id), None)
    if not selected_sensor:
        logger.warning(f"Nie znaleziono czujnika o ID: {selected_id}")
        print("Nie znaleziono czujnika o podanym ID.")
        return None

    logger.info(f"Wybrano czujnik ID: {selected_id}")
    return selected_sensor

def get_sensors_for_station(station_id):
    """
    Zwraca listę sensorów w danej stacji (dla GUI).
    """
    logger.info(f"Pobieranie sensorów dla stacji ID: {station_id} (do GUI)")
    return api_GIOS.get_sensors_for_station(station_id)
