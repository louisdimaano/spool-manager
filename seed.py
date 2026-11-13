from db import get_db, init_db

init_db()
conn = get_db()

conn.execute(
    "INSERT INTO spools (brand, material, color, remaining_g, cost) VALUES (?, ?, ?, ?, ?)",
    ("Elegoo", "PLA", "Black", 640, 15.99),
)
conn.execute(
    "INSERT INTO spools (brand, material, color, remaining_g, cost) VALUES (?, ?, ?, ?, ?)",
    ("Polymaker", "PETG", "White", 120, 22.99),
)

conn.commit()
conn.close()
print("Added sample spools.")