from app import api_GIOS

def select_sensor_from_station(station_id):
    sensors = api_GIOS.get_sensors_for_station(station_id)

    if not sensors:
        print("❌ Brak czujników dla tej stacji.")
        return None

    print("\n📋 Dostępne czujniki pomiarowe:")
    for sensor in sensors:
        param = sensor["param"]
        print(f"  ID: {sensor['id']} | {param['paramName']} ({param['paramCode']})")

    while True:
        user_input = input("\n🔎 Podaj ID wybranego czujnika (lub 'q' aby wyjść): ")

        if user_input.lower() == 'q':
            print("⏹️ Anulowano wybór czujnika.")
            return None

        try:
            selected_id = int(user_input)
        except ValueError:
            print("❌ Niepoprawny numer. Spróbuj ponownie.")
            continue

        match = next((s for s in sensors if s["id"] == selected_id), None)
        if match:
            param = match["param"]
            print(f"\n✅ Wybrano czujnik: {param['paramName']} ({param['paramCode']})")
            return match
        else:
            print("❌ Nie znaleziono czujnika o podanym ID. Spróbuj ponownie.")

