#mapa

import folium
from app import api_GIOS

def get_pm10_value(sensor_id):
    data = api_GIOS.get_measurements_for_sensor(sensor_id)
    values = data.get("values", [])
    for v in values:
        if v["value"] is not None:
            return v["value"]  # zwracamy pierwszy dostępny pomiar
    return None

def get_color_for_pm10(value):
    if value is None:
        return "gray"
    elif value <= 20:
        return "green"
    elif value <= 50:
        return "orange"
    else:
        return "red"

def generate_station_map(param_code="PM10"):
    print("⏬ Pobieranie mapy...")
    stations = api_GIOS.get_all_stations()

    station_map = folium.Map(location=[52.4, 16.9], zoom_start=6)  # środek Polski

    for station in stations:
        try:
            lat = float(station["gegrLat"])
            lon = float(station["gegrLon"])
        except (TypeError, ValueError):
            continue

        # pobierz sensory tej stacji
        sensors = api_GIOS.get_sensors_for_station(station["id"])
        sensor = next((s for s in sensors if s["param"]["paramCode"] == param_code), None)

        if not sensor:
            color = "gray"
            value_text = "brak danych"
        else:
            value = get_pm10_value(sensor["id"])
            color = get_color_for_pm10(value)
            value_text = f"{value} µg/m³" if value is not None else "brak danych"

        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>{station['stationName']}</b><br>{station['city']['name']}<br>{param_code}: {value_text}",
                max_width=300
            )
        ).add_to(station_map)

    # zapisz do pliku
    station_map.save("mapa_stacji.html")
    print("✅ Mapa zapisana jako 'mapa_stacji.html'")

#wykres
