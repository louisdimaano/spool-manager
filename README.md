# SpoolManager

A web app I built to keep track of my 3D printer filament. It shows every spool I own, how much is left, and whether a print will fit on a spool before I start it. It runs in Docker on my home server, so I can check it from my phone at the printer.

## Features

- Add, edit, and delete spools (brand, material, finish, color, weight, cost, CFS slot, dry box, backup brand, notes)
- Cards that show the real filament color, including dual color, tri color, gradient, and translucent spools
- Fill bar and percent left on every spool, with a LOW badge under 150 g that shows the backup brand to reorder
- "Can I print this?" checker: enter what the slicer says in grams or meters, and it answers Enough, Tight, or Not enough based on a safety margin you set
- One click to subtract a finished print from the spool, or log a print by hand
- Update grams left by weighing the spool (scale reading minus the empty spool weight)
- Print history saved in the database
- Works on phones, with light and dark mode
- Exports in-stock colors as JSON for the public color page on my order form
- Password login that keeps each device logged in for 30 days
- A recovery code for a forgotten password, and a page to change the password
- Every form protected against cross-site request forgery (CSRF)

## Built With

- Python and Flask
- SQLite (using Python's built-in sqlite3, no ORM)
- Jinja templates, HTML, CSS, and a small amount of JavaScript
- Werkzeug password hashing and Flask-WTF for CSRF protection
- pytest for automated tests
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

## How login works

- There is one account with one password, no username. The first visit shows a page to set it.
- Only a hash of the password is saved, never the password itself.
- After setup, a recovery code is shown once. If the password is forgotten, "Forgot password?" takes the code and a new password, then gives a new code. The code is also saved only as a hash.
- Logging in gives the browser a signed session cookie that lasts 30 days. Every page checks for it, except the login pages, the styles, and the color export.
- Every form carries a hidden CSRF token, so another website can't make my browser change anything.
- If both the password and the recovery code are lost, the account can be cleared from the server, and the setup page comes back:

  ```
  docker compose exec spoolmanager python -c "import db; c = db.get_db(); c.execute('DELETE FROM users'); c.commit()"
  ```

## Sharing colors with my order form

Customers can see which colors I have before they order, without SpoolManager ever being on the internet.

1. `/export/colors.json` lists every color I have filament left in, grouped by material, finish, and color. Spools of the same color are combined.
2. It shows a stock level instead of exact grams: **Plenty** (500 g or more), **Limited** (150 to 499 g), or **Low** (under 150 g).
3. A script on my home server downloads the export every hour. If any colors changed, it commits the file to the order form repo and pushes it, and GitHub Pages updates the color page.

The export is the one page that doesn't need a login, so the script can still download it. It only holds what the public color page already shows. The script pushes with a deploy key that only has access to the order form repo, and SpoolManager itself stays on my private network.

## Project Structure

```
spool-manager/
├── app.py              # Routes, login, form checks, and page logic
├── auth.py             # Password rules and recovery codes
├── db.py               # Database connection and setup
├── filament.py         # Meters-to-grams math, the print check, and stock levels
├── schema.sql          # Database tables
├── templates/          # Jinja page templates
├── static/style.css    # Styles
├── tests/              # pytest tests
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

Then open http://127.0.0.1:5000 and set a password. The database (`spools.db`) is created automatically on the first run.

## Running the Tests

```
pip install -r requirements-dev.txt
pytest
```

## Running It with Docker

1. Create a `.env` file next to `docker-compose.yml` with a random secret key:

   ```
   SECRET_KEY=your-long-random-string
   ```

   One way to make one: `python3 -c "import secrets; print(secrets.token_hex(32))"`. Without it, the app makes a random key at startup, and everyone gets logged out whenever it restarts.

2. Build and start it:

   ```
   docker compose up -d --build
   ```

3. Open http://localhost:5000 (or your server's address on port 5000) **right away** and set the password. Until it's set, anyone who can reach the app could set it.

The database is stored in `./data`, outside the container, so it survives rebuilds. Back up that folder.

> **Note:** the login is meant to keep my own network safer, not to make the app safe on the open internet. It doesn't limit wrong password guesses or use HTTPS yet, so I still only run it on a private network.

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
- Returning JSON from Flask, and grouping rows with a dictionary so repeat colors become one entry
- Choosing what to share publicly: stock levels instead of exact grams, and no prices
- Automating a task with a shell script and cron, and only committing when the data actually changed
- Using a deploy key so a server can push to one repo without access to my whole GitHub account
- Keeping finish separate from material, so a new option didn't break the density math
- Storing passwords and recovery codes only as hashes, and checking them with `check_password_hash`
- Protecting every page with one `before_request` check, so a new page can't be left unprotected by accident
- How CSRF works, why Log out is a POST button instead of a link, and why each token has to sit inside its form
- Thinking through what a change breaks elsewhere: locking every page would have broken the hourly color script, so the export stays open on purpose
- Giving each app its own cookie name, because browsers share cookies between apps on the same host
- Reusing a pattern from another project (Gunpla Tracker) and adapting it, instead of starting over

## Roadmap

- Scan the barcode on a filament box with my phone, and remember barcodes so repeat purchases fill in the form automatically
- A page that shows print history and filament used over time
- Limit wrong password guesses, and add HTTPS, before it's ever reachable outside my home network