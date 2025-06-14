import tkinter as tk
from tkinter import messagebox
from prettymaps import plot_map
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import io

def generate_map():
    location = city_entry.get()
    if not location:
        messagebox.showwarning("Brak danych", "Wpisz nazwę miasta.")
        return

    try:
        fig, ax = plt.subplots(figsize=(6, 6))
        plot_map(
            ax,
            location=location,
            radius=1000,  # promień w metrach
            layers={
                "buildings": {"tags": {"building": True}},
                "streets": {"tags": {"highway": True}},
                "water": {"tags": {"natural": "water"}},
                "green": {"tags": {"landuse": "grass"}},
            }
        )

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        img = Image.open(buf)
        img = img.resize((400, 400))  # dopasowanie do GUI
        tk_img = ImageTk.PhotoImage(img)

        map_label.config(image=tk_img)
        map_label.image = tk_img

    except Exception as e:
        messagebox.showerror("Błąd", f"Nie udało się wygenerować mapy:\n{e}")

# --- GUI setup ---
root = tk.Tk()
root.title("Mapa miasta z Prettymaps")

tk.Label(root, text="Wpisz miasto:").pack(pady=5)
city_entry = tk.Entry(root, width=30)
city_entry.pack(pady=5)
city_entry.insert(0, "Warszawa")

tk.Button(root, text="Generuj mapę", command=generate_map).pack(pady=10)

map_label = tk.Label(root)
map_label.pack(padx=10, pady=10)

root.mainloop()
