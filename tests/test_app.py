import os
import sqlite3
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))
from app.update_db import update_city_measurements


@pytest.fixture
def create_test_db():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE stations (
            id INTEGER PRIMARY KEY,
            city TEXT NOT NULL
        );
        CREATE TABLE sensors (
            id INTEGER PRIMARY KEY,
            param_name TEXT,
            station_id INTEGER,
            FOREIGN KEY (station_id) REFERENCES stations(id)
        );
        CREATE TABLE measurements (
            id INTEGER PRIMARY KEY,
            sensor_id INTEGER,
            date_time TEXT,
            value REAL,
            FOREIGN KEY (sensor_id) REFERENCES sensors(id)
        );
    """)
    return conn

# --- Test gdy brak stacji ---
def test_update_city_no_stations(create_test_db):
    conn = create_test_db

    result = update_city_measurements("WymyśloneMiasto", conn=conn)
    assert result == 0

# --- Test gdy są stacje i sensory, ale API nic nie zwraca ---
@patch("app.update_db.api_GIOS.get_measurements_for_sensor")
def test_update_city_no_new_data(mock_get, create_test_db):
    conn = create_test_db
    cur = conn.cursor()

    # Wstawiamy dane testowe
    cur.execute("INSERT INTO stations (id, city) VALUES (1, 'Testowo')")
    cur.execute("INSERT INTO sensors (id, param_name, station_id) VALUES (10, 'PM10', 1)")
    cur.execute("INSERT INTO measurements (sensor_id, date_time, value) VALUES (?, ?, ?)", (
        10, "2024-06-01T10:00:00", 42.0
    ))
    conn.commit()

    # Mock: API zwraca starszy pomiar niż mamy w bazie
    mock_get.return_value = {
        "values": [
            {"date": "2024-05-30T12:00:00", "value": 41.5}
        ]
    }

    result = update_city_measurements("Testowo", conn=conn)
    assert result == 0  # nie dodano nowych rekordów

# --- Test gdy API zwraca nowe dane ---
@patch("app.update_db.api_GIOS.get_measurements_for_sensor")
def test_update_city_with_new_data(mock_get, create_test_db):
    conn = create_test_db
    cur = conn.cursor()

    cur.execute("INSERT INTO stations (id, city) VALUES (1, 'NoweMiasto')")
    cur.execute("INSERT INTO sensors (id, param_name, station_id) VALUES (10, 'PM2.5', 1)")
    conn.commit()

    # Mock: API zwraca 2 nowe pomiary
    mock_get.return_value = {
        "values": [
            {"date": "2024-06-10T10:00:00", "value": 15.2},
            {"date": "2024-06-10T11:00:00", "value": 16.8}
        ]
    }

    result = update_city_measurements("NoweMiasto", conn=conn)
    assert result == 2

    # Sprawdź czy dane są w bazie
    cur.execute("SELECT COUNT(*) FROM measurements")
    count = cur.fetchone()[0]
    assert count

@patch("app.update_db.api_GIOS.get_measurements_for_sensor")
def test_update_city_api_failure_does_not_crash(mock_get, create_test_db):
    conn = create_test_db
    cur = conn.cursor()
    cur.execute("INSERT INTO stations (id, city) VALUES (1, 'Awaria')")
    cur.execute("INSERT INTO sensors (id, param_name, station_id) VALUES (10, 'O3', 1)")
    conn.commit()

    mock_get.side_effect = Exception("Błąd API")

    result = update_city_measurements("Awaria", conn=conn)
    assert result == 0

@patch("app.update_db.api_GIOS.get_measurements_for_sensor")
def test_update_city_calls_progress_cb(mock_get, create_test_db):
    conn = create_test_db
    cur = conn.cursor()
    cur.execute("INSERT INTO stations (id, city) VALUES (1, 'Postępowo')")
    cur.execute("INSERT INTO sensors (id, param_name, station_id) VALUES (10, 'CO', 1)")
    conn.commit()

    mock_get.return_value = {
        "values": [{"date": "2024-06-12T08:00:00", "value": 3.3}]
    }

    called = []
    def fake_cb(done, total):
        called.append((done, total))

    result = update_city_measurements("Postępowo", conn=conn, progress_cb=fake_cb)
    assert result == 1
    assert called == [(1, 1)]

