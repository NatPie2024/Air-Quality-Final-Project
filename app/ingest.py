import logging
from app import api_GIOS
from app.database import create_tables, insert_station, insert_sensor, insert_measurement

# Logger setup
logger = logging.getLogger("FetchSave")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def fetch_and_save_all_data():
    logger.info("Rozpoczynanie pobierania i zapisywania danych z GIOS")

    create_tables()
    logger.info("Tabele w bazie danych zostały utworzone (jeśli nie istniały)")

    stations = api_GIOS.get_all_stations()
    logger.info(f"Pobrano {len(stations)} stacji z API GIOŚ")

    for station in stations:
        insert_station(station)
        station_id = station["id"]
        logger.info(f"Dodano stację: {station['stationName']} ({station['city']['name']})")

        sensors = api_GIOS.get_sensors_for_station(station_id)
        if not sensors:
            logger.warning(f"Brak sensorów dla stacji ID: {station_id}")
            continue

        for sensor in sensors:
            insert_sensor(sensor, station_id)
            sensor_id = sensor["id"]
            logger.info(f"Dodano sensor: {sensor['param']['paramName']} (ID: {sensor_id})")

            measurements = api_GIOS.get_measurements_for_sensor(sensor_id)
            count = 0
            for m in measurements.get("values", []):
                insert_measurement(sensor_id, m)
                count += 1

            logger.info(f"Zapisano {count} pomiarów dla sensora ID: {sensor_id}")

    logger.info("Wszystkie dane zostały pobrane i zapisane do bazy danych.")


if __name__ == "__main__":
    fetch_and_save_all_data()
