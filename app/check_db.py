import sqlite3
import os

# Utwórz folder jeśli nie istnieje
os.makedirs("data", exist_ok=True)

# Ścieżka do bazy
DB_PATH = os.path.join("data", "test.db")

# Próba utworzenia połączenia i tabeli testowej
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT);")
    conn.commit()
    conn.close()
    print("✅ Połączenie z bazą działa. Plik zapisano jako 'data/test.db'")
except Exception as e:
    print("❌ Błąd:", e)
