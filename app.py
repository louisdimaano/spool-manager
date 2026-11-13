from flask import Flask, render_template
from db import get_db, init_db

app = Flask(__name__)
init_db()


@app.route("/")
def spool_list():
    conn = get_db()
    spools = conn.execute("SELECT * FROM spools ORDER BY material, color").fetchall()
    conn.close()
    return render_template("spools.html", spools=spools)


if __name__ == "__main__":
    app.run(debug=True)