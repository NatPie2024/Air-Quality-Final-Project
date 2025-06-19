import logging
from app import api_GIOS

# Logger setup
logger = logging.getLogger("StationSelection")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def select_station_from_city(city_name="Poznań"):

    # Interaktywny wybór stacji z miasta (wersja konsolowa).

    logger.info(f"Rozpoczynanie wyboru stacji dla miasta: {city_name}")
    stations = api_GIOS.get_all_stations()

    city_stations = [
        s for s in stations
        if s["city"]["name"].lower() == city_name.lower()
    ]

    if not city_stations:
        logger.warning(f"Brak stacji w miejscowości: {city_name}")
        print(f"Brak stacji w miejscowości: {city_name}")
        return None

    print(f"\nStacje w miejscowości: {city_name}")
    for s in city_stations:
        street = s.get("addressStreet") or "(brak ulicy)"
        print(f"  ID: {s['id']} | {s['stationName']} | {street}")

    try:
        selected_id = int(input("\nPodaj ID wybranej stacji: "))
    except ValueError:
        logger.warning("Niepoprawny numer stacji podany przez użytkownika")
        print("Niepoprawny numer.")
        return None

    match = next((s for s in city_stations if s['id'] == selected_id), None)
    if not match:
        logger.warning(f"Nie znaleziono stacji o ID: {selected_id} w mieście {city_name}")
        print("Nie znaleziono stacji o podanym ID.")
        return None

    logger.info(f"Wybrano stację ID: {selected_id} - {match['stationName']} ({match['city']['name']})")
    print(f"\nWybrano stację: {match['stationName']} ({match['city']['name']})")
    return selected_id

def get_stations_in_city(city_name):

    # Zwraca listę stacji w danym mieście (do GUI).

    logger.info(f"Pobieranie listy stacji dla miasta: {city_name}")
    stations = api_GIOS.get_all_stations()
    city_stations = [
        s for s in stations
        if s["city"]["name"].lower() == city_name.lower()
    ]
    logger.info(f"Znaleziono {len(city_stations)} stacji w mieście: {city_name}")
    return city_stations
