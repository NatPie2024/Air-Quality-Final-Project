import requests

BASE_URL = "https://api.gios.gov.pl/pjp-api/rest"

def get_all_stations():
    url = f"{BASE_URL}/station/findAll"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Błąd podczas pobierania stacji:", response.status_code)
        return []

def get_sensors_for_station(station_id):
    url = f"{BASE_URL}/station/sensors/{station_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd przy pobieraniu sensorów dla stacji {station_id}")
        return []

def get_measurements_for_sensor(sensor_id):
    url = f"{BASE_URL}/data/getData/{sensor_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd przy pobieraniu danych z sensora {sensor_id}")
        return {}

def find_stations_by_city(city_name, stations):
    return [s for s in stations if s.get("city", {}).get("name", "").lower() == city_name.lower()]

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
