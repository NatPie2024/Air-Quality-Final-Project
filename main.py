from app import api_GIOS
from app.database import create_tables, insert_sensor, insert_measurement
from app.sensor_selection import select_sensor_from_station
from app.station_selection import select_station_from_city

def fetch_and_save_measurements(sensor_data):

    #Pobiera dane pomiarowe z API dla wybranego sensora i zapisuje je do bazy danych.

    sensor_id = sensor_data["id"]
    station_id = sensor_data["stationId"]
    insert_sensor(sensor_data, station_id)

    print(f"\nPobieranie danych pomiarowych z czujnika ID: {sensor_id}")
    measurements = api_GIOS.get_measurements_for_sensor(sensor_id)

    if not measurements.get("values"):
        print("Brak danych pomiarowych.")
        return

    for m in measurements["values"]:
        insert_measurement(sensor_id, m)

    print("Dane zostały zapisane do bazy danych.")

def main():

    # Główna funkcja aplikacji konsolowej:
    # tworzy tabele,
    # pobiera dane stacji i sensora,
    # pobiera pomiary i zapisuje je do bazy.

    create_tables()

    city_name = input("Podaj nazwę miasta: ")
    station_id = select_station_from_city(city_name)
    if not station_id:
        return

    sensor_data = select_sensor_from_station(station_id)
    if not sensor_data:
        return

    fetch_and_save_measurements(sensor_data)

if __name__ == "__main__":
    main()



