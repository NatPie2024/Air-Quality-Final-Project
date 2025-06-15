import logging
import requests

BASE_URL = "https://api.gios.gov.pl/pjp-api/rest"

# Logger setup
logger = logging.getLogger("GIOS_API")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_all_stations():
    url = f"{BASE_URL}/station/findAll"
    try:
        logger.info("Pobieranie wszystkich stacji")
        response = requests.get(url)
        response.raise_for_status()
        stations = response.json()
        logger.info(f"Pobrano {len(stations)} stacji")
        return stations
    except requests.RequestException as e:
        logger.exception("Błąd podczas pobierania stacji")
        return []

def get_sensors_for_station(station_id):
    url = f"{BASE_URL}/station/sensors/{station_id}"
    try:
        logger.info(f"Pobieranie sensorów dla stacji ID: {station_id}")
        response = requests.get(url)
        response.raise_for_status()
        sensors = response.json()
        logger.info(f"Pobrano {len(sensors)} sensorów")
        return sensors
    except requests.RequestException as e:
        logger.exception(f"Błąd przy pobieraniu sensorów dla stacji {station_id}")
        return []

def get_measurements_for_sensor(sensor_id):
    url = f"{BASE_URL}/data/getData/{sensor_id}"
    try:
        logger.info(f"Pobieranie danych z sensora ID: {sensor_id}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        values_count = len(data.get('values', []))
        logger.info(f"Pobrano {values_count} pomiarów")
        return data
    except requests.RequestException as e:
        logger.exception(f"Błąd przy pobieraniu danych z sensora {sensor_id}")
        return {}

def find_stations_by_city(city_name, stations):
    logger.info(f"Filtrowanie stacji dla miasta: {city_name}")
    result = [s for s in stations if s.get("city", {}).get("name", "").lower() == city_name.lower()]
    logger.info(f"Znaleziono {len(result)} stacji w mieście: {city_name}")
    return result

def main():
    stations = get_all_stations()
    print(f"Znaleziono {len(stations)} stacji.")

    city_name = input("Podaj nazwę miasta, dla którego chcesz pobrać dane: ")

    city_stations = find_stations_by_city(city_name, stations)

    if not city_stations:
        print(f"Brak stacji w mieście: {city_name}")
        return

    print(f"\nZnaleziono {len(city_stations)} stacji w mieście {city_name}.")

    for station in city_stations:
        print(f"\nStacja: {station['stationName']} ({station['city']['name']})")
        sensors = get_sensors_for_station(station['id'])
        for sensor in sensors:
            param = sensor['param']['paramName']
            print(f"\nPobieranie danych dla parametru: {param}")
            measurements = get_measurements_for_sensor(sensor['id'])
            for value in measurements.get('values', [])[:5]:
                print(f"{value['date']} -> {value['value']}")

if __name__ == "__main__":
    main()
