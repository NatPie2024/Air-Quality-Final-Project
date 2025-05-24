import requests

BASE_URL = "https://api.gios.gov.pl/pjp-api/rest"

# 1. Pobierz listę wszystkich stacji pomiarowych
def get_all_stations():
    url = f"{BASE_URL}/station/findAll"
    response = requests.get(url)
    if response.status_code == 200:
        stations = response.json()
        return stations
    else:
        print("Błąd podczas pobierania stacji:", response.status_code)
        return []


# 2. Pobierz sensory (czujniki) z danej stacji
def get_sensors_for_station(station_id):
    url = f"{BASE_URL}/station/sensors/{station_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd przy pobieraniu sensorów dla stacji {station_id}")
        return []


# 3. Pobierz dane z sensora (pomiar dla konkretnego parametru)
def get_measurements_for_sensor(sensor_id):
    url = f"{BASE_URL}/data/getData/{sensor_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd przy pobieraniu danych z sensora {sensor_id}")
        return {}


# 4. Przykładowe pobranie danych z jednej stacji
def main():
    stations = get_all_stations()

    print(f"Znaleziono {len(stations)} stacji.")

    # Przykład: pobierz dane z pierwszej stacji
    if stations:
        first_station = stations[0]
        print(f"\nStacja: {first_station['stationName']} ({first_station['city']['name']})")

        sensors = get_sensors_for_station(first_station['id'])
        for sensor in sensors:
            param = sensor['param']['paramName']
            print(f"\nPobieranie danych dla parametru: {param}")
            measurements = get_measurements_for_sensor(sensor['id'])

            # Wyświetl kilka pierwszych pomiarów
            for value in measurements.get('values', [])[:5]:
                print(f"{value['date']} -> {value['value']}")


if __name__ == "__main__":
    main()

