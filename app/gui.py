import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app import api_GIOS
from app.analysis import analyze_measurements_to_text
from app.database import insert_sensor, insert_measurement, create_tables, connect
from app.sensor_selection import get_sensors_for_station
from app.station_selection import get_stations_in_city

# Styl
THEME = {
    "font": ("Segoe UI", 10),
    "title_font": ("Segoe UI", 12, "bold"),
    "bg_color": "#f0f4f7",
    "btn_bg": "#4CAF50",
    "btn_fg": "white",
    "btn_active": "#45a049",
    "text_bg": "#ffffff",
    "text_fg": "#333333"
}

class AirQualityApp:
    def __init__(self, root):
        create_tables()
        self.root = root
        self.root.title("\ud83c\udf2c\ufe0f Stan Powietrza – Monitor Jako\u015bci")
        self.root.geometry("700x600")
        self.root.configure(bg=THEME["bg_color"])

        style = ttk.Style()
        style.configure("TFrame", background=THEME["bg_color"])
        style.configure("TLabel", background=THEME["bg_color"], font=THEME["font"])
        style.configure("TButton", font=THEME["font"], padding=5)
        style.configure("TCombobox", font=THEME["font"])

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        self.selection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.selection_frame, text='Wyb\xf3r miasta, stacji i parametr\xf3w:')

        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text='Wykres i analiza danych')

        self.build_selection_tab()
        self.build_result_tab()

    def build_selection_tab(self):
        frame = self.selection_frame

        tk.Label(frame, text="Podaj miasto:", font=THEME["font"], bg=THEME["bg_color"]).pack(pady=5)
        self.city_entry = tk.Entry(frame, font=THEME["font"])
        self.city_entry.pack()

        self.add_button(frame, "Pobierz stacj\u0119:", self.fetch_stations)
        self.station_list = ttk.Combobox(frame, state="readonly")
        self.station_list.pack(pady=5)

        self.add_button(frame, "Pobierz parametr:", self.fetch_sensors)
        self.sensor_list = ttk.Combobox(frame, state="readonly")
        self.sensor_list.pack(pady=5)

        tk.Label(frame, text="Wybierz zakres danych:", font=THEME["font"], bg=THEME["bg_color"]).pack(pady=5)
        self.range_choice = ttk.Combobox(frame, state="readonly")
        self.range_choice["values"] = ["Ostatnie 3 dni", "Ostatnie 10 dni", "Ostatnie 30 dni"]
        self.range_choice.current(1)
        self.range_choice.pack()

        self.add_button(frame, "Pobierz dane, rysuj wykres i analizuj", self.get_data_and_plot, pady=15)

    def add_button(self, parent, text, command, pady=8):
        tk.Button(
            parent, text=text, command=command,
            bg=THEME["btn_bg"], fg=THEME["btn_fg"],
            activebackground=THEME["btn_active"],
            font=THEME["font"], relief="flat", bd=0
        ).pack(pady=pady)

    def build_result_tab(self):
        self.canvas_frame = ttk.Frame(self.result_frame)
        self.canvas_frame.pack(fill="both", expand=True)

        self.analysis_text = tk.Text(
            self.result_frame, height=8, font=("Courier New", 10),
            bg=THEME["text_bg"], fg=THEME["text_fg"], wrap="word", padx=10, pady=10
        )
        self.analysis_text.pack(fill="x", padx=10, pady=10)

    def fetch_stations(self):
        city = self.city_entry.get()
        if not city:
            messagebox.showwarning("Uwaga", "Wpisz nazw\u0119 miasta.")
            return

        stations = get_stations_in_city(city)
        if not stations:
            messagebox.showinfo("Brak", "Brak takiego miasta lub brak stacji w tym mie\u015bcie.")
            return

        self.stations_map = {f"{s['stationName']} ({s.get('addressStreet') or 'brak'})": s["id"] for s in stations}
        self.station_list["values"] = list(self.stations_map.keys())

    def fetch_sensors(self):
        station_name = self.station_list.get()
        if not station_name:
            messagebox.showwarning("Uwaga", "Wybierz stacj\u0119.")
            return

        station_id = self.stations_map[station_name]
        self.selected_station_id = station_id

        sensors = get_sensors_for_station(station_id)
        if not sensors:
            messagebox.showinfo("Brak", "Brak sensor\xf3w.")
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
                "B\u0142\u0105d po\u0142\u0105czenia",
                "Nie uda\u0142o si\u0119 pobra\u0107 danych z API.\nU\u017cy\u0107 danych z bazy?"
            )
            if not use_db:
                return

        selected_range = self.range_choice.get()
        days = 10
        if "3" in selected_range:
            days = 3
        elif "30" in selected_range:
            days = 30

        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)

        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = date_to.strftime("%Y-%m-%d")

        self.show_plot(sensor_id, date_from_str, date_to_str)
        self.show_analysis(sensor_id, date_from_str, date_to_str)
        self.notebook.select(self.result_frame)

    def show_plot(self, sensor_id, date_from, date_to):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        conn = connect()
        query = "SELECT date_time, value FROM measurements WHERE sensor_id = ? ORDER BY date_time"
        df = pd.read_sql_query(query, conn, params=(sensor_id,))
        conn.close()

        df["date_time"] = pd.to_datetime(df["date_time"], errors='coerce')
        df.dropna(subset=["date_time"], inplace=True)

        if date_from:
            try:
                df = df[df["date_time"] >= pd.to_datetime(date_from)]
            except ValueError:
                messagebox.showerror("B\u0142\u0105d", "Nieprawid\u0142owa data pocz\u0105tkowa.")
                return

        if date_to:
            try:
                df = df[df["date_time"] <= pd.to_datetime(date_to)]
            except ValueError:
                messagebox.showerror("B\u0142\u0105d", "Nieprawid\u0142owa data ko\u0144cowa.")
                return

        if df.empty:
            messagebox.showinfo("Brak danych", "Brak danych w podanym zakresie.")
            return

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(df["date_time"], df["value"], marker='o', linestyle='-')
        ax.set_title(f"St\u0119\u017cenie {self.sensor_list.get()}")
        ax.set_xlabel("Data")
        ax.set_ylabel("Warto\u015b\u0107 [\u00b5g/m\xb3]")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.set_facecolor("#f9f9f9")
        fig.patch.set_facecolor("#f9f9f9")
        fig.autofmt_xdate()

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



