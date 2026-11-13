from flask import Flask, render_template, request, redirect, url_for
from db import get_db, init_db

app = Flask(__name__)
MATERIALS = ["PLA", "PETG", "ABS", "ASA", "TPU", "Other"]
init_db()


@app.route("/")
def spool_list():
    conn = get_db()
    spools = conn.execute("SELECT * FROM spools ORDER BY material, color").fetchall()
    conn.close()
    return render_template("spools.html", spools=spools)

@app.route("/spools/new", methods=["GET", "POST"])
def add_spool():
    if request.method == "GET":
        return render_template("spool_form.html", errors=[], form={}, materials=MATERIALS)

    form = request.form
    errors = []

    brand = form.get("brand", "").strip()
    material = form.get("material", "").strip()
    color = form.get("color", "").strip()
    if not (brand and material and color):
        errors.append("Brand, material, and color are required.")

    try:
        total_g = int(form.get("total_g") or 1000)
        remaining_g = int(form.get("remaining_g") or total_g)
        cost = float(form["cost"]) if form.get("cost") else None
    except ValueError:
        errors.append("Weights must be whole numbers, and cost must be a number.")
    else:
        if total_g <= 0 or remaining_g < 0:
            errors.append("Weights can't be negative.")
        elif remaining_g > total_g:
            errors.append("Grams left can't be more than the spool's total.")

    if errors:
        return render_template("spool_form.html", errors=errors, form=form, materials=MATERIALS)

    conn = get_db()
    conn.execute(
        "INSERT INTO spools (brand, material, color, total_g, remaining_g, cost, "
        "cfs_slot, in_dry_box, backup_brand, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            brand, material, color, total_g, remaining_g, cost,
            form.get("cfs_slot") or None,
            1 if form.get("in_dry_box") else 0,
            form.get("backup_brand") or None,
            form.get("notes") or None,
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("spool_list"))

if __name__ == "__main__":
    app.run(debug=True)