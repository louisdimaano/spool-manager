from flask import Flask, render_template, request, redirect, url_for, abort
from db import get_db, init_db

app = Flask(__name__)
init_db()

MATERIALS = ["PLA", "PETG", "ABS", "ASA", "TPU", "Other"]


def read_spool_form(form):
    """Check the form and return (values, errors)."""
    errors = []

    brand = form.get("brand", "").strip()
    material = form.get("material", "").strip()
    color = form.get("color", "").strip()
    if not (brand and material and color):
        errors.append("Brand, material, and color are required.")

    total_g = remaining_g = cost = None
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

    values = {
        "brand": brand,
        "material": material,
        "color": color,
        "total_g": total_g,
        "remaining_g": remaining_g,
        "cost": cost,
        "cfs_slot": form.get("cfs_slot", "").strip() or None,
        "in_dry_box": 1 if form.get("in_dry_box") else 0,
        "backup_brand": form.get("backup_brand", "").strip() or None,
        "notes": form.get("notes", "").strip() or None,
    }
    return values, errors


@app.route("/")
def spool_list():
    conn = get_db()
    spools = conn.execute("SELECT * FROM spools ORDER BY material, color").fetchall()
    conn.close()
    return render_template("spools.html", spools=spools)


@app.route("/spools/new", methods=["GET", "POST"])
def add_spool():
    if request.method == "GET":
        return render_template("spool_form.html", heading="Add a Spool",
                               errors=[], form={}, materials=MATERIALS)

    values, errors = read_spool_form(request.form)
    if errors:
        return render_template("spool_form.html", heading="Add a Spool",
                               errors=errors, form=request.form, materials=MATERIALS)

    conn = get_db()
    conn.execute(
        "INSERT INTO spools (brand, material, color, total_g, remaining_g, cost, "
        "cfs_slot, in_dry_box, backup_brand, notes) VALUES (:brand, :material, :color, "
        ":total_g, :remaining_g, :cost, :cfs_slot, :in_dry_box, :backup_brand, :notes)",
        values,
    )
    conn.commit()
    conn.close()
    return redirect(url_for("spool_list"))


@app.route("/spools/<int:spool_id>/edit", methods=["GET", "POST"])
def edit_spool(spool_id):
    conn = get_db()
    spool = conn.execute("SELECT * FROM spools WHERE id = ?", (spool_id,)).fetchone()
    if spool is None:
        conn.close()
        abort(404)

    if request.method == "GET":
        conn.close()
        return render_template("spool_form.html", heading="Edit Spool", spool_id=spool_id,
                               errors=[], form=dict(spool), materials=MATERIALS)

    values, errors = read_spool_form(request.form)
    if errors:
        conn.close()
        return render_template("spool_form.html", heading="Edit Spool", spool_id=spool_id,
                               errors=errors, form=request.form, materials=MATERIALS)

    values["id"] = spool_id
    conn.execute(
        "UPDATE spools SET brand = :brand, material = :material, color = :color, "
        "total_g = :total_g, remaining_g = :remaining_g, cost = :cost, cfs_slot = :cfs_slot, "
        "in_dry_box = :in_dry_box, backup_brand = :backup_brand, notes = :notes "
        "WHERE id = :id",
        values,
    )
    conn.commit()
    conn.close()
    return redirect(url_for("spool_list"))


@app.route("/spools/<int:spool_id>/delete", methods=["POST"])
def delete_spool(spool_id):
    conn = get_db()
    conn.execute("DELETE FROM spools WHERE id = ?", (spool_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("spool_list"))


if __name__ == "__main__":
    app.run(debug=True)