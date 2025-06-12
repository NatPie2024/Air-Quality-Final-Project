from app import api_GIOS
from app.database import create_tables, insert_sensor, insert_measurement
from app.sensor_selection import select_sensor_from_station
from app.station_selection import select_station_from_city
from app.visualizations.maps import generate_station_map
from app.visualizations.charts import plot_measurements
from app.analysis import analyze_measurements

def fetch_and_save_measurements(sensor_data):
    sensor_id = sensor_data["id"]
    station_id = sensor_data["stationId"]
    insert_sensor(sensor_data, station_id)

    print(f"\n⏬ Pobieranie danych pomiarowych z czujnika ID: {sensor_id}")
    measurements = api_GIOS.get_measurements_for_sensor(sensor_id)

    if not measurements.get("values"):
        print("❌ Brak danych pomiarowych.")
        return

    for m in measurements["values"]:
        insert_measurement(sensor_id, m)

    print("✅ Dane zostały zapisane do bazy danych.")

def main():
    # 🧱 Krok 1: utwórz tabele
    global date_from, date_to
    create_tables()

    # 🏙️ Krok 2: wybór miasta i stacji
    city_name = input("🏙️ Podaj nazwę miasta: ")
    station_id = select_station_from_city(city_name)
    if not station_id:
        return

    # 🔎 Krok 3: wybór czujnika
    sensor_data = select_sensor_from_station(station_id)
    if not sensor_data:
        return
    sensor_id = sensor_data["id"]

    # 💾 Krok 4: pobierz i zapisz dane
    fetch_and_save_measurements(sensor_data)

    # 🗺️ Krok 5: mapa
    generate_station_map("PM10")

    # 📈 Krok 6: wykres
    wykres = input("📈 Czy chcesz wygenerować wykres? (t/n): ").lower()
    if wykres == 't':
        date_from = input("📅 Data początkowa (YYYY-MM-DD) [Enter = brak]: ") or None
        date_to = input("📅 Data końcowa (YYYY-MM-DD) [Enter = brak]: ") or None
        save = input("💾 Czy zapisać wykres do pliku? (t/n): ").lower()
        if save == 't':
            plot_measurements(sensor_id, date_from, date_to, save_path="wykres.png")
        else:
            plot_measurements(sensor_id, date_from, date_to)

    # 📊 Krok 7: analiza
    analyze = input("📊 Czy chcesz wykonać analizę danych? (t/n): ").lower()
    if analyze == 't':
        analyze_measurements(sensor_id, date_from, date_to)

if __name__ == "__main__":
    main()



