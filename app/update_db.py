from typing import Callable
import sqlite3
import logging
from datetime import datetime
from dateutil.parser import isoparse

from app import api_GIOS
from app.database import insert_measurement, connect

log = logging.getLogger(__name__)


def update_city_measurements(
        city_name: str,
        *,
        conn: sqlite3.Connection | None = None,
        progress_cb: Callable[[int, int], None] | None = None
) -> int:

    # Aktualizuje dane pomiarowe z API GIOS dla wszystkich sensorów w danym mieście. Zwraca liczbę **nowych** rekordów.

    city_name = city_name.strip().lower()
    own_conn = conn is None
    if own_conn:
        conn = connect()

    try:
        with conn:
            cur = conn.cursor()

            cur.execute("SELECT id FROM stations WHERE LOWER(city)=?", (city_name,))
            station_ids = [row[0] for row in cur.fetchall()]
            if not station_ids:
                log.warning("Brak stacji w mieście '%s'", city_name)
                return 0

            placeholders = ",".join("?" for _ in station_ids)
            cur.execute(f"""
                SELECT id, param_name
                FROM sensors
                WHERE station_id IN ({placeholders})
            """, tuple(station_ids))
            sensors = cur.fetchall()

            latest_map = _latest_times(cur, station_ids)
            total_inserted = 0
            total_sensors = len(sensors)

            for i, (sensor_id, param_name) in enumerate(sensors, 1):
                log.info("(%d/%d) Sensor: %s (ID: %d)", i, total_sensors, param_name, sensor_id)
                newest = latest_map.get(sensor_id)

                try:
                    values = api_GIOS.get_measurements_for_sensor(sensor_id).get("values", [])
                except Exception as e:
                    log.error("Błąd pobierania danych z API dla sensora %d: %s", sensor_id, e)
                    continue

                new_values = [
                    v for v in values
                    if v["value"] is not None and (
                        newest is None or isoparse(v["date"]).replace(tzinfo=None) > newest
                    )
                ]

                for v in new_values:
                    insert_measurement(cur, sensor_id, v)

                log.debug("  ↪ zapisano %d nowych pomiarów", len(new_values))
                total_inserted += len(new_values)

                if progress_cb:
                    progress_cb(i, total_sensors)

            log.info("Zakończono aktualizację miasta '%s' ➜ %d nowych rekordów", city_name, total_inserted)
            return total_inserted
    finally:
        if own_conn:
            conn.close()


def _latest_times(cur: sqlite3.Cursor, station_ids: list[int]) -> dict[int, datetime | None]:

    # Zwraca mapę sensor_id → ostatnia data pomiaru (lub None).

    placeholders = ",".join("?" for _ in station_ids)
    cur.execute(f"""
        SELECT s.id, MAX(m.date_time)
        FROM sensors s
        LEFT JOIN measurements m ON m.sensor_id = s.id
        WHERE s.station_id IN ({placeholders})
        GROUP BY s.id
    """, tuple(station_ids))
    return {
        sensor_id: (datetime.fromisoformat(ts) if ts else None)
        for sensor_id, ts in cur.fetchall()
    }

def insert_measurement(cur, sensor_id: int, v: dict):
    cur.execute(
        "INSERT INTO measurements (sensor_id, date_time, value) VALUES (?, ?, ?)",
        (sensor_id, v["date"], v["value"])
    )

