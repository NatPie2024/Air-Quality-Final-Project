import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox
from tkinter import ttk

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app import api_GIOS
from app.analysis import analyze_measurements_to_text
from app.database import insert_sensor, insert_measurement, create_tables, connect
from app.sensor_selection import get_sensors_for_station
from app.station_selection import get_stations_in_city


class AirQualityApp:
    def __init__(self, root):
        create_tables()
        self.root = root
        self.root.title("STAN POWIETRZA W MIASTACH")
        self.root.geometry("700x600")

        # Notebook (zakładki)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        # Zakładka 1: Wybór
        self.selection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.selection_frame, text='Wybór miasta, stacji i parametrów:')

        # Zakładka 2: Wykres i analiza
        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text='Wykres i analiza danych')

        self.build_selection_tab()
        self.build_result_tab()

    def build_selection_tab(self):
        frame = self.selection_frame

        tk.Label(frame, text="Podaj miasto:").pack(pady=5)
        self.city_entry = tk.Entry(frame)
        self.city_entry.pack()

        tk.Button(frame, text="Wybierz stację:", command=self.fetch_stations).pack(pady=5)

        self.station_list = ttk.Combobox(frame, state="readonly")
        self.station_list.pack(pady=5)

        tk.Button(frame, text="Wybierz parametr:", command=self.fetch_sensors).pack(pady=5)
        self.sensor_list = ttk.Combobox(frame, state="readonly")
        self.sensor_list.pack(pady=5)

        tk.Label(frame, text="Wybierz zakres danych:").pack(pady=5)
        self.range_choice = ttk.Combobox(frame, state="readonly")
        self.range_choice["values"] = ["Ostatnie 3 dni", "Ostatnie 10 dni", "Ostatnie 30 dni"]
        self.range_choice.current(1)
        self.range_choice.pack()

        tk.Button(
            frame,
            text="Pobierz dane, rysuj wykres i analizuj",
            command=self.get_data_and_plot
        ).pack(pady=15)

    def build_result_tab(self):
        self.canvas_frame = ttk.Frame(self.result_frame)
        self.canvas_frame.pack(fill="both", expand=True)

        self.analysis_text = tk.Text(self.result_frame, height=8)
        self.analysis_text.pack(fill="x", padx=10, pady=10)

    def fetch_stations(self):
        city = self.city_entry.get()
        if not city:
            messagebox.showwarning("Uwaga", "Wpisz nazwę miasta.")
            return

        stations = get_stations_in_city(city)
        if not stations:
            messagebox.showinfo("Brak", "Brak takiego miasta lub brak stacji w tym mieście.")
            return

        self.stations_map = {f"{s['stationName']} ({s.get('addressStreet') or 'brak'})": s["id"] for s in stations}
        self.station_list["values"] = list(self.stations_map.keys())

    def fetch_sensors(self):
        station_name = self.station_list.get()
        if not station_name:
            messagebox.showwarning("Uwaga", "Wybierz stację.")
            return

        station_id = self.stations_map[station_name]
        self.selected_station_id = station_id

        sensors = get_sensors_for_station(station_id)
        if not sensors:
            messagebox.showinfo("Brak", "Brak sensorów.")
            return

        self.sensors_map = {s['param']['paramName']: s for s in sensors}
        self.sensor_list["values"] = list(self.sensors_map.keys())

    def get_data_and_plot(self):
        sensor_name = self.sensor_list.get()
        if not sensor_name:
            messagebox.showwarning("Uwaga", "Wybierz sensor.")
            return

        sensor_data = self.sensors_map[sensor_name]
        sensor_id = sensor_data["id"]
        station_id = self.selected_station_id

        insert_sensor(sensor_data, station_id)

        try:
            measurements = api_GIOS.get_measurements_for_sensor(sensor_id)
            if not measurements.get("values"):
                raise ValueError("Brak danych z API")

            for m in measurements["values"]:
                insert_measurement(sensor_id, m)

        except Exception:
            use_db = messagebox.askyesno(
                "Błąd połączenia",
                "Nie udało się pobrać danych z API.\nUżyć danych z bazy?"
            )
            if not use_db:
                return

        # Zakres dat z rozwijanej listy
        selected_range = self.range_choice.get()
        days = 10
        if "3" in selected_range:
            days = 3
        elif "30" in selected_range:
            days = 30

        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)

        # Zamiana na tekst
        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = date_to.strftime("%Y-%m-%d")

        self.show_plot(sensor_id, date_from_str, date_to_str)
        self.show_analysis(sensor_id, date_from_str, date_to_str)
        self.notebook.select(self.result_frame)

    def show_plot(self, sensor_id, date_from, date_to):
        # Usuwanie poprzedniego wykresu
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        # Pobieranie danych z bazy
        conn = connect()
        query = "SELECT date_time, value FROM measurements WHERE sensor_id = ? ORDER BY date_time"
        df = pd.read_sql_query(query, conn, params=(sensor_id,))
        conn.close()

        # Konwersja daty i filtrowanie zakresu
        df["date_time"] = pd.to_datetime(df["date_time"], errors='coerce')
        df.dropna(subset=["date_time"], inplace=True)  # Usuwa błędne daty

        if date_from:
            try:
                df = df[df["date_time"] >= pd.to_datetime(date_from)]
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowa data początkowa.")
                return

        if date_to:
            try:
                df = df[df["date_time"] <= pd.to_datetime(date_to)]
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowa data końcowa.")
                return

        if df.empty:
            messagebox.showinfo("Brak danych", "Brak danych w podanym zakresie.")
            return

        # Tworzenie wykresu
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(df["date_time"], df["value"], marker='o', linestyle='-')
        ax.set_title(f"Stężenie {self.sensor_list.get()}")
        ax.set_xlabel("Data")
        ax.set_ylabel("Wartość [µg/m³]")
        ax.grid(True)
        fig.autofmt_xdate()

        # Osadzenie wykresu w GUI
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_analysis(self, sensor_id, date_from, date_to):
        text = analyze_measurements_to_text(sensor_id, date_from, date_to)
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, text)


def run_gui_with_tabs():
    root = tk.Tk()
    app = AirQualityApp(root)
    root.mainloop()


run_gui_with_tabs()
