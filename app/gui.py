import tempfile
import tkinter as tk
import webbrowser
from datetime import datetime, timedelta
from tkinter import ttk, messagebox
import logging

from update_db import update_city_measurements
import folium
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app import api_GIOS
from app.analysis import analyze_measurements_to_text
from app.database import insert_sensor, insert_measurement, create_tables, connect
from app.sensor_selection import get_sensors_for_station
from app.station_selection import get_stations_in_city
from app.constants import CITY_NAMES

# Logger setup
logger = logging.getLogger("AirQualityApp")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Styl
THEME = {
    "font": ("Segoe UI", 12),
    "title_font": ("Segoe UI", 14, "bold"),
    "bg_color": "#f0f4f7",
    "btn_bg": "#4CAF50",
    "btn_fg": "black",
    "btn_active": "#45a049",
    "text_bg": "#ffffff",
    "text_fg": "#333333"
}

class AutocompleteCombobox(ttk.Combobox):
    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self["values"] = [city for city in self._completion_list]
        self.bind('<KeyRelease>', self._handle_keyrelease)

    def _handle_keyrelease(self, event):
        value = self.get().strip().lower()
        if value == '':
            data = self._completion_list
        else:
            data = [item for item in self._completion_list if item.lower().startswith(value)]
        self["values"] = [city for city in data]
        self.event_generate('<Down>')


class AirQualityApp:
    def __init__(self, root):
        logger.info("Inicjalizacja aplikacji AirQualityApp")
        create_tables()
        self.root = root
        self.root.title(" STAN POWIETRZA W MIASTACH")
        self.root.geometry("700x600")
        self.root.configure(bg=THEME["bg_color"])

        self._setup_style()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        self._init_selection_tab()
        self._init_result_tab()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=THEME["bg_color"])
        style.configure("TLabel", background=THEME["bg_color"], font=THEME["font"])
        style.configure("TButton", font=THEME["font"], padding=10)
        style.configure("TCombobox", font=THEME["font"])
        style.configure("TLabelframe", background=THEME["bg_color"], font=THEME["title_font"])
        style.configure("TLabelframe.Label", background=THEME["bg_color"], font=THEME["title_font"])

    def _init_selection_tab(self):
        self.selection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.selection_frame, text='Wybierz miasto, stację i parametr:')
        self._build_selection_tab()

    def _init_result_tab(self):
        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text='Wykres i analiza danych')
        self._init_map_tab()
        self._build_result_tab()

    def _init_map_tab(self):
        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text='Mapa stacji')

        ttk.Label(
            self.map_frame,
            text="Kliknij przycisk, aby zobaczyć mapę stacji w wybranym mieście.",
            font=THEME["font"]
        ).pack(pady=10)

        self._add_button(self.map_frame, "Pokaż mapę", self.show_station_map)

    def _build_selection_tab(self):
        frame = self.selection_frame

        city_frame = ttk.LabelFrame(frame, text="Wybór miasta")
        city_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(city_frame, text="Miasto:", font=THEME["font"], bg=THEME["bg_color"]).grid(row=0, column=0, padx=5,
                                                                                            pady=5, sticky="w")
        self.city_entry = AutocompleteCombobox(city_frame, font=THEME["font"])
        self.city_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        city_frame.columnconfigure(1, weight=1)

        # Ustawienie listy miast z constants.py
        self.city_entry.set_completion_list(CITY_NAMES)

        fetch_station_btn = tk.Button(
            city_frame, text="Pobierz stację", command=self.fetch_stations,
            bg=THEME["btn_bg"], fg=THEME["btn_fg"], activebackground=THEME["btn_active"],
            font=THEME["font"], relief="flat", bd=0
        )
        fetch_station_btn.grid(row=1, column=0, columnspan=2, pady=5)

        station_frame = ttk.LabelFrame(frame, text="Wybór stacji i sensora")
        station_frame.pack(pady=10, padx=10, fill="x")

        self.station_list = ttk.Combobox(station_frame, state="readonly")
        self.station_list.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        fetch_sensor_btn = tk.Button(
            station_frame, text="Pobierz parametr", command=self.fetch_sensors,
            bg=THEME["btn_bg"], fg=THEME["btn_fg"], activebackground=THEME["btn_active"],
            font=THEME["font"], relief="flat", bd=0
        )
        fetch_sensor_btn.grid(row=1, column=0, columnspan=2, pady=5)

        self.sensor_list = ttk.Combobox(station_frame, state="readonly")
        self.sensor_list.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        update_btn = tk.Button(
            station_frame, text="Pobierz aktualne dane sensorów", command=self.update_database,
            bg=THEME["btn_bg"], fg=THEME["btn_fg"], activebackground=THEME["btn_active"],
            font=THEME["font"], relief="flat", bd=0
        )
        update_btn.grid(row=3, column=0, columnspan=2, pady=5)

        station_frame.columnconfigure(0, weight=1)

        range_frame = ttk.LabelFrame(frame, text="Zakres danych i analiza")
        range_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(range_frame, text="Zakres:", font=THEME["font"], bg=THEME["bg_color"]).grid(row=0, column=0, padx=5,
                                                                                             pady=5, sticky="w")
        self.range_choice = ttk.Combobox(range_frame, state="readonly")
        self.range_choice["values"] = ["Ostatnie 3 dni", "Ostatnie 10 dni", "Ostatnie 30 dni"]
        self.range_choice.current(1)
        self.range_choice.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        range_frame.columnconfigure(1, weight=1)

        analyze_btn = tk.Button(
            range_frame, text="Pobierz dane, rysuj wykres i analizuj", command=self.get_data_and_plot,
            bg=THEME["btn_bg"], fg=THEME["btn_fg"], activebackground=THEME["btn_active"],
            font=THEME["font"], relief="flat", bd=0
        )
        analyze_btn.grid(row=1, column=0, columnspan=2, pady=10)

    def update_database(self):
        city = self.city_entry.get()
        logger.info(f"Aktualizacja danych dla miasta: {city}")
        if not city:
            messagebox.showwarning("Uwaga", "Wpisz nazwę miasta przed aktualizacją.")
            return

        # Okno ładowania
        loading_window = tk.Toplevel(self.root)
        loading_window.title("Ładowanie")
        loading_window.geometry("300x100")
        loading_window.configure(bg=THEME["bg_color"])
        loading_window.resizable(False, False)
        loading_window.grab_set()  # blokuje interakcje z innymi oknami

        label = tk.Label(loading_window, text="Trwa pobieranie danych...", font=THEME["font"], bg=THEME["bg_color"])
        label.pack(pady=10)

        progress = ttk.Progressbar(loading_window, mode='indeterminate')
        progress.pack(fill='x', padx=20, pady=10)
        progress.start()

        # Wyśrodkowanie względem głównego okna
        self.root.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        win_w, win_h = 300, 100
        pos_x = root_x + (root_w - win_w) // 2
        pos_y = root_y + (root_h - win_h) // 2
        loading_window.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.root.update()

        try:
            update_city_measurements(city)
            progress.stop()
            loading_window.grab_release()
            loading_window.destroy()

            # messagebox pojawia się tuż po zamknięciu loading_window (zachowuje pozycję)
            self.root.after(100,
                            lambda: messagebox.showinfo("Sukces", f"Dane dla miasta '{city}' zostały zaktualizowane."))
            logger.info(f"Pomyślnie zaktualizowano dane dla miasta: {city}")

        except Exception as e:
            progress.stop()
            loading_window.grab_release()
            loading_window.destroy()

            self.root.after(100, lambda: messagebox.showerror("Błąd", f"Nie udało się zaktualizować danych:\n{e}"))
            logger.exception("Błąd podczas aktualizacji danych")

    def _add_button(self, parent, text, command, pady=10):
        tk.Button(
            parent, text=text, command=command,
            bg=THEME["btn_bg"], fg=THEME["btn_fg"],
            activebackground=THEME["btn_active"],
            font=THEME["font"], relief="flat", bd=0
        ).pack(pady=pady)

    def _build_result_tab(self):
        self.canvas_frame = ttk.Frame(self.result_frame)
        self.canvas_frame.pack(fill="both", expand=True)

        self.analysis_text = tk.Text(
            self.result_frame, height=8, font=("Courier New", 10),
            bg=THEME["text_bg"], fg=THEME["text_fg"], wrap="word", padx=10, pady=10
        )
        self.analysis_text.pack(fill="x", padx=10, pady=10)

    def fetch_stations(self):
        city = self.city_entry.get()
        logger.info(f"Pobieranie stacji dla miasta: {city}")
        # Czyszczenie pól
        self.station_list.set("")
        self.station_list["values"] = []
        self.sensor_list.set("")
        self.sensor_list["values"] = []
        self.range_choice.current(1)

        if not city:
            messagebox.showwarning("Uwaga", "Wpisz nazwę miasta.")
            return

        stations = get_stations_in_city(city)
        if not stations:
            logger.warning(f"Brak stacji dla miasta: {city}")
            messagebox.showinfo("Brak", "Brak takiego miasta lub brak stacji w tym mieście.")
            return

        self.stations_map = {f"{s['stationName']} ({s.get('addressStreet') or 'brak'})": s["id"] for s in stations}
        self.station_list["values"] = list(self.stations_map.keys())
        logger.info(f"Znaleziono {len(self.stations_map)} stacji w mieście: {city}")

    def fetch_sensors(self):
        station_name = self.station_list.get()
        logger.info(f"Pobieranie sensorów dla stacji: {station_name}")
        if not station_name:
            messagebox.showwarning("Uwaga", "Wybierz stację.")
            return

        station_id = self.stations_map[station_name]
        self.selected_station_id = station_id

        sensors = get_sensors_for_station(station_id)
        if not sensors:
            logger.warning(f"Brak sensorów dla stacji: {station_name}")
            messagebox.showinfo("Brak", "Brak sensorów.")
            return

        self.sensors_map = {s['param']['paramName']: s for s in sensors}
        self.sensor_list["values"] = list(self.sensors_map.keys())
        logger.info(f"Znaleziono {len(self.sensors_map)} sensorów.")

    def get_data_and_plot(self):
        sensor_name = self.sensor_list.get()
        logger.info(f"Wybrany sensor: {sensor_name}")
        if not sensor_name:
            messagebox.showwarning("Uwaga", "Wybierz sensor.")
            return

        sensor_data = self.sensors_map[sensor_name]
        sensor_id = sensor_data["id"]
        station_id = self.selected_station_id

        insert_sensor(sensor_data, station_id)

        try:
            logger.info(f"Pobieranie danych z API dla sensora ID: {sensor_id}")
            measurements = api_GIOS.get_measurements_for_sensor(sensor_id)
            if not measurements.get("values"):
                raise ValueError("Brak danych z API")

            for m in measurements["values"]:
                insert_measurement(sensor_id, m)
            logger.info(f"Pobrano i zapisano {len(measurements['values'])} pomiarów.")
        except Exception as e:
            logger.warning(f"Błąd podczas pobierania danych z API: {e}")
            if not messagebox.askyesno("Błąd połączenia", "Nie udało się pobrać danych z API. Użyć danych z bazy?"):
                return

        selected_range = self.range_choice.get()
        days = 10 if "10" in selected_range else 3 if "3" in selected_range else 30
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)

        logger.info(f"Zakres dat: {date_from.strftime('%Y-%m-%d')} do {date_to.strftime('%Y-%m-%d')}")
        self.show_plot(sensor_id, date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"))
        self.show_analysis(sensor_id, date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"))
        self.notebook.select(self.result_frame)

    def show_plot(self, sensor_id, date_from, date_to):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        conn = connect()
        df = pd.read_sql_query("SELECT date_time, value FROM measurements WHERE sensor_id = ? ORDER BY date_time", conn, params=(sensor_id,))
        conn.close()

        df["date_time"] = pd.to_datetime(df["date_time"], errors='coerce')
        df.dropna(subset=["date_time"], inplace=True)

        try:
            df = df[(df["date_time"] >= pd.to_datetime(date_from)) & (df["date_time"] <= pd.to_datetime(date_to))]
        except ValueError:
            logger.error("Nieprawidłowy zakres dat.")
            messagebox.showerror("Błąd", "Nieprawidłowy zakres dat.")
            return

        if df.empty:
            logger.warning("Brak danych w podanym zakresie.")
            messagebox.showinfo("Brak danych", "Brak danych w podanym zakresie.")
            return

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(df["date_time"], df["value"], marker='o', linestyle='-')
        ax.set_title(f"Stężenie {self.sensor_list.get()}")
        ax.set_xlabel("Data")
        ax.set_ylabel("Wartość [µg/m³]")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.set_facecolor("#f9f9f9")
        fig.patch.set_facecolor("#f9f9f9")
        fig.autofmt_xdate()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_analysis(self, sensor_id, date_from, date_to):
        logger.info("Generowanie analizy danych")
        text = analyze_measurements_to_text(sensor_id, date_from, date_to)
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, text)

    def show_station_map(self):
        city = self.city_entry.get()
        logger.info(f"Wyświetlanie mapy stacji dla miasta: {city}")
        if not city:
            messagebox.showwarning("Uwaga", "Wpisz nazwę miasta.")
            return

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT station_name, latitude, longitude FROM stations WHERE LOWER(city) = LOWER(?)", (city,))
        stations = cur.fetchall()
        conn.close()

        if not stations:
            logger.warning(f"Brak stacji w mieście: {city}")
            messagebox.showinfo("Brak", f"Brak stacji w mieście {city}")
            return

        # Środek mapy: pierwsza stacja
        map_center = [stations[0][1], stations[0][2]]
        fmap = folium.Map(location=map_center, zoom_start=12)

        for name, lat, lon in stations:
            folium.Marker([lat, lon], popup=name).add_to(fmap)

        tmp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
        fmap.save(tmp_file.name)
        webbrowser.open(tmp_file.name)

def run_gui_with_tabs():
    root = tk.Tk()
    app = AirQualityApp(root)
    root.mainloop()