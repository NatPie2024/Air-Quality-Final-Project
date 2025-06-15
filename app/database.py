import sqlite3
import os

# Ustal ścieżkę bezwzględną do katalogu "data/" w katalogu głównym projektu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)  # jeśli folder nie istnieje, utwórz go

DB_PATH = os.path.join(DATA_DIR, "air_quality.db")

def connect():
    return sqlite3.connect(DB_PATH)

def create_tables():
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

# ... pozostałe funkcje insert_station, insert_sensor, insert_measurement pozostają bez zmian

def insert_station(station):
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

def insert_sensor(sensor, station_id):
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

def insert_measurement(sensor_id, measurement):
    if measurement['value'] is not None:
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

def api():
    return None

# pobieranie listy stacji z bazy danych

def get_stations_from_db(city_name):
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
            "addressStreet": "(z bazy)"  # jeśli chcesz, możesz rozbudować
        }
        stations.append(station)
    return stations

# pobieranie listy sensorów z bazy danych
def get_sensors_from_db(station_id):
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
    return sensors
