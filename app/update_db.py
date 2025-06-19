import logging
import sqlite3
from datetime import datetime
from typing import Iterable, Dict, Sequence, Callable

from dateutil.parser import isoparse
from app.database import connect, insert_measurement
from app import api_GIOS

log = logging.getLogger(__name__)

def _latest_times(cur: sqlite3.Cursor, station_ids: Sequence[int]) -> Dict[int, datetime | None]:
    if not station_ids:
        return {}

    placeholders = ",".join("?" for _ in station_ids)
    cur.execute(f"""
        SELECT s.id, MAX(m.date_time)
        FROM sensors s
        LEFT JOIN measurements m ON m.sensor_id = s.id
        WHERE s.station_id IN ({placeholders})
        GROUP BY s.id
    """, station_ids)

    return {
        row[0]: (isoparse(row[1]).replace(tzinfo=None) if row[1] else None)
        for row in cur.fetchall()
    }


def update_city_measurements(
        city_name: str,
        *,
        conn: sqlite3.Connection | None = None,
        progress_cb: Callable[[int, int], None] | None = None
) -> int:
    own_conn = conn is None
    if own_conn:
        conn = connect()

    try:
        with conn:
            cur = conn.cursor()

            cur.execute("SELECT id FROM stations WHERE LOWER(city)=LOWER(?)", (city_name,))
            station_ids = [row[0] for row in cur.fetchall()]
            if not station_ids:
                log.warning("Brak stacji w mieście '%s'", city_name)
                return 0

            placeholders = ",".join("?" for _ in station_ids)
            cur.execute(f"""
                SELECT id, param_name
                FROM sensors
                WHERE station_id IN ({placeholders})
            """, station_ids)
            sensors = cur.fetchall()
            latest_map = _latest_times(cur, station_ids)

            total_inserted = 0
            total_sensors = len(sensors)

            for i, (sensor_id, param_name) in enumerate(sensors, 1):
                log.info("(%d/%d) Sensor: %s (ID %d)", i, total_sensors, param_name, sensor_id)
                newest = latest_map.get(sensor_id)

                try:
                    values = api_GIOS.get_measurements_for_sensor(sensor_id).get("values", [])
                except Exception as e:
                    log.error("Błąd pobierania danych z API dla sensora %d: %s", sensor_id, e)
                    continue

                count = 0
                for v in values:
                    if v["value"] is None:
                        continue
                    ts = isoparse(v["date"]).replace(tzinfo=None)
                    if newest is None or ts > newest:
                        insert_measurement(sensor_id, v)
                        count += 1

                total_inserted += count
                log.debug("  ↪ zapisano %d nowych pomiarów", count)

                if progress_cb:
                    progress_cb(i, total_sensors)

            log.info("Zakończono aktualizację miasta '%s' ➜ %d nowych rekordów", city_name, total_inserted)
            return total_inserted
    finally:
        if own_conn:
            conn.close()
