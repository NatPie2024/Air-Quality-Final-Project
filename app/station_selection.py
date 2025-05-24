from app import api_GIOS

def select_station_from_city(city_name="Poznań"):
    stations = api_GIOS.get_all_stations()

    # Filtrowanie po nazwie miasta (ignorujemy wielkość liter)
    city_stations = [
        s for s in stations
        if s["city"]["name"].lower() == city_name.lower()
    ]

    if not city_stations:
        print(f"❌ Brak stacji w miejscowości: {city_name}")
        return None

    print(f"\n📍 Stacje w miejscowości: {city_name}")
    for s in city_stations:
        street = s.get("addressStreet") or "(brak ulicy)"
        print(f"  ID: {s['id']} | {s['stationName']} | {street}")

    try:
        selected_id = int(input("\n🔎 Podaj ID wybranej stacji: "))
    except ValueError:
        print("❌ Niepoprawny numer.")
        return None

    match = next((s for s in city_stations if s['id'] == selected_id), None)
    if not match:
        print("❌ Nie znaleziono stacji o podanym ID.")
        return None

    print(f"\n✅ Wybrano stację: {match['stationName']} ({match['city']['name']})")
    return selected_id

