from app import api_GIOS
from app.database import create_tables, insert_sensor, insert_measurement
from app.sensor_selection import select_sensor_from_station
from app.station_selection import select_station_from_city


def fetch_and_save_measurements(sensor_data):
    sensor_id = sensor_data["id"]
    station_id = sensor_data["stationId"]
    insert_sensor(sensor_data, station_id)

    print(f"\n Pobieranie danych pomiarowych z czujnika ID: {sensor_id}")
    measurements = api_GIOS.get_measurements_for_sensor(sensor_id)

    if not measurements.get("values"):
        print("❌ Brak danych pomiarowych.")
        return

    for m in measurements["values"]:
        insert_measurement(sensor_id, m)

    print("✅ Dane zostały zapisane do bazy danych.")

def main():
    create_tables()

    # Krok 1: wybór miasta
    city_name = input(" Podaj nazwę miasta: ")
    station_id = select_station_from_city(city_name)
    if not station_id:
        return

    # Krok 2: wybór czujnika
    sensor_data = select_sensor_from_station(station_id)
    if not sensor_data:
        return

    # Krok 3: pobierz i zapisz dane pomiarowe
    fetch_and_save_measurements(sensor_data)

if __name__ == "__main__":
    main()

# generowanie mapa
from app.visualizations.maps import generate_station_map

def main():
    generate_station_map("PM10")  # możesz też użyć np. "PM2.5"

if __name__ == "__main__":
    main()

# wyświetlanie wykresu
from app.visualizations.charts import plot_measurements

def main():
    try:
        sensor_id = int(input("🔎 Podaj ID czujnika do wykresu: "))
    except ValueError:
        print("❌ Niepoprawny numer ID.")
        return

    date_from = input(" Data początkowa (YYYY-MM-DD) [Enter = brak]: ") or None
    date_to = input(" Data końcowa (YYYY-MM-DD) [Enter = brak]: ") or None
    save = input(" Czy zapisać wykres do pliku? (t/n): ").lower()

    if save == 't':
        plot_measurements(sensor_id, date_from, date_to)
    else:
        plot_measurements(sensor_id, date_from, date_to)

if __name__ == "__main__":
    main()



