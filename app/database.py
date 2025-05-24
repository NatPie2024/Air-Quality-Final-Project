import sqlite3
import os

DB_PATH = os.path.join("data", "air_quality.db")

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