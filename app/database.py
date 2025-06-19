import sys
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

def resource_path(relative_path):
    #Zwraca ścieżkę do pliku zarówno w .py jak i .exe (PyInstaller)
    try:
        base_path = sys._MEIPASS  # działa w PyInstallerze
    except AttributeError:
        base_path = os.path.abspath(".")  # działa w trybie dev
    return os.path.join(base_path, relative_path)

DB_PATH = resource_path(os.path.join("data", "air_quality.db"))

def connect():
    logger.info(f"Nawiązywanie połączenia z bazą danych: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def connect():
    logger.info("Nawiązywanie połączenia z bazą danych")
    return sqlite3.connect(DB_PATH)

def create_tables():
    logger.info("Tworzenie tabel w bazie danych, jeśli nie istnieją")
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY,
            station_name TEXT,
            city TEXT,
            commune TEXT,
            province TEXT,
            latitude REAL,
            longitude REAL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensors (
            id INTEGER PRIMARY KEY,
            station_id INTEGER,
            param_code TEXT,
            param_name TEXT,
            FOREIGN KEY(station_id) REFERENCES stations(id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id INTEGER,
            value REAL,
            date_time TEXT,
            FOREIGN KEY(sensor_id) REFERENCES sensors(id)
        );
    """)

    conn.commit()
    conn.close()
    logger.info("Tabele utworzone lub już istniały")

def insert_station(station):
    logger.info(f"Wstawianie stacji do bazy: {station['stationName']}, ID: {station['id']}")
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO stations (id, station_name, city, commune, province, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        station['id'],
        station['stationName'],
        station['city']['name'],
        station['city']['commune']['communeName'],
        station['city']['commune']['provinceName'],
        float(station['gegrLat']),
        float(station['gegrLon'])
    ))
    conn.commit()
    conn.close()
    logger.info("Stacja dodana (lub już istniała)")

def insert_sensor(sensor, station_id):
    logger.info(f"Wstawianie sensora ID: {sensor['id']} do stacji ID: {station_id}")
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO sensors (id, station_id, param_code, param_name)
        VALUES (?, ?, ?, ?);
    """, (
        sensor['id'],
        station_id,
        sensor['param']['paramCode'],
        sensor['param']['paramName']
    ))
    conn.commit()
    conn.close()
    logger.info("Sensor dodany (lub już istniał)")

def insert_measurement(sensor_id, measurement):
    if measurement['value'] is not None:
        logger.info(f"Dodawanie pomiaru dla sensora ID: {sensor_id}, data: {measurement['date']}, wartość: {measurement['value']}")
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO measurements (sensor_id, value, date_time)
            VALUES (?, ?, ?);
        """, (
            sensor_id,
            measurement['value'],
            measurement['date']
        ))
        conn.commit()
        conn.close()
        logger.info("Pomiar dodany")
    else:
        logger.warning(f"Pominięto pomiar bez wartości dla sensora ID: {sensor_id}")

def api():
    return None

# pobieranie listy stacji z bazy danych
def get_stations_from_db(city_name):
    logger.info(f"Pobieranie stacji z bazy danych dla miasta: {city_name}")
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, station_name, city, latitude, longitude
        FROM stations
        WHERE LOWER(city) = LOWER(?)
    """, (city_name,))
    rows = cur.fetchall()
    conn.close()

    stations = []
    for row in rows:
        station = {
            "id": row[0],
            "stationName": row[1],
            "city": {"name": row[2]},
            "gegrLat": row[3],
            "gegrLon": row[4],
            "addressStreet": "(z bazy)"
        }
        stations.append(station)
    logger.info(f"Znaleziono {len(stations)} stacji w bazie danych")
    return stations

# pobieranie listy sensorów z bazy danych
def get_sensors_from_db(station_id):
    logger.info(f"Pobieranie sensorów z bazy danych dla stacji ID: {station_id}")
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, param_code, param_name
        FROM sensors
        WHERE station_id = ?
    """, (station_id,))
    rows = cur.fetchall()
    conn.close()

    sensors = []
    for row in rows:
        sensor = {
            "id": row[0],
            "param": {
                "paramCode": row[1],
                "paramName": row[2]
            }
        }
        sensors.append(sensor)
    logger.info(f"Znaleziono {len(sensors)} sensorów w bazie danych")
    return sensors

def get_city_names():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT city FROM stations ORDER BY city")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows if row[0]]
