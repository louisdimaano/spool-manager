# SpoolManager

A web app I built to keep track of my 3D printer filament. It shows every spool I own, how much is left, and whether a print will fit on a spool before I start it. It runs in Docker on my home server, so I can check it from my phone at the printer.

## Features

- Add, edit, and delete spools (brand, material, color, weight, cost, CFS slot, dry box, backup brand, notes)
- Cards that show the real filament color, including dual color, tri color, gradient, and translucent spools
- Fill bar and percent left on every spool, with a LOW badge under 150 g that shows the backup brand to reorder
- "Can I print this?" checker: enter what the slicer says in grams or meters, and it answers Enough, Tight, or Not enough based on a safety margin you set
- One click to subtract a finished print from the spool, or log a print by hand
- Update grams left by weighing the spool (scale reading minus the empty spool weight)
- Print history saved in the database
- Works on phones, with light and dark mode

## Built With

- Python and Flask
- SQLite (using Python's built-in sqlite3, no ORM)
- Jinja templates, HTML, CSS, and a small amount of JavaScript
- Gunicorn and Docker Compose for running it on my home server

## How the print check works

Slicers report filament in grams or meters. Meters are converted to grams using the volume of the filament times the density of the material:

```
grams = π × (diameter ÷ 2)² × length × density
```

For 1.75 mm filament, 1 meter of PLA is about 2.98 g. Densities used (g/cm³):

| Material | Density |
| -------- | ------- |
| PLA      | 1.24    |
| PETG     | 1.27    |
| ABS      | 1.04    |
| ASA      | 1.07    |
| TPU      | 1.21    |

A print is **Enough** when the spool has the needed grams plus the safety margin (10% by default), **Tight** when it has enough but not the full margin, and **Not enough** when it falls short.

## Project Structure

```
spool-manager/
├── app.py              # Routes, form checks, and page logic
├── db.py               # Database connection and setup
├── filament.py         # Meters-to-grams math and the print check
├── schema.sql          # Database tables
├── templates/          # Jinja page templates
├── static/style.css    # Styles
├── Dockerfile
└── docker-compose.yml
```

## Running It Locally

```
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000. The database (`spools.db`) is created automatically on the first run.

## Running It with Docker

1. Create a `.env` file next to `docker-compose.yml` with a random secret key:

   ```
   SECRET_KEY=your-long-random-string
   ```

   One way to make one: `python3 -c "import secrets; print(secrets.token_hex(32))"`

2. Build and start it:

   ```
   docker compose up -d --build
   ```

3. Open http://localhost:5000 (or your server's address on port 5000).

The database is stored in `./data`, outside the container, so it survives rebuilds. Back up that folder.

> **Note:** there is no login yet, so only run this on a private network. Don't expose it to the internet.

## What I Learned

- How Flask routes handle GET and POST requests, and why the app redirects after saving a form (so a refresh doesn't submit it twice)
- Checking every form on the server, even when the browser already checks it, because browser checks can be skipped
- Using `?` and named placeholders in SQL so user input is never run as a command (SQL injection)
- Linking tables with a foreign key, and turning on `PRAGMA foreign_keys` so deleting a spool also deletes its print history
- Saving two related changes in one commit so they both happen or neither does
- Adding new columns to an existing database without losing data (a simple migration)
- Template inheritance in Jinja, so every page shares one layout
- Pulling repeated code into shared functions instead of copying it
- Keeping secrets out of code with environment variables, and replacing a key after it was accidentally shown
- Running a Python app in Docker with a volume so the data lives outside the container
- Reading Python tracebacks to find the exact line and cause of an error
- Writing automated tests with pytest, which caught a floating point rounding bug at the safety margin boundary
- Share my in-stock colors with my 3D print order form

## Roadmap

- Scan the barcode on a filament box with my phone, and remember barcodes so repeat purchases fill in the form automatically
- A page that shows print history and filament used over time
- A login, before it's ever reachable outside my home network

