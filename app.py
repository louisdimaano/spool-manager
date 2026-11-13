import math
import re
import os
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, abort, flash, jsonify

from db import get_db, init_db
from filament import meters_to_grams, check_print, stock_level

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-not-secret")
init_db()
app.jinja_env.globals["stock_level"] = stock_level


MATERIALS = ["PLA", "PETG", "ABS", "ASA", "TPU", "Other"]
FINISHES = ["Basic", "Matte", "Silk", "Glow", "Sparkle", "Marble", "Wood"]
LOW_STOCK_G = 150
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")
CHECKERBOARD = "repeating-conic-gradient(#d9d9d9 0% 25%, #ffffff 0% 50%) 0 0 / 16px 16px"


@app.template_filter("swatch")
def swatch(spool):
    """Build the CSS background that shows a spool's color(s)."""
    colors = [c for c in (spool["color_hex"], spool["color_hex_2"], spool["color_hex_3"]) if c]
    if not colors:
        return "var(--border)"
    if spool["is_translucent"]:
        colors = [c + "99" for c in colors]

    if len(colors) == 1:
        layer = f"linear-gradient({colors[0]}, {colors[0]})"
    elif spool["color_style"] == "gradient":
        layer = f"linear-gradient(135deg, {', '.join(colors)})"
    else:
        step = 100 / len(colors)
        stops = ", ".join(
            f"{c} {i * step:.0f}% {(i + 1) * step:.0f}%" for i, c in enumerate(colors)
        )
        layer = f"linear-gradient(135deg, {stops})"

    if spool["is_translucent"]:
        return f"{layer}, {CHECKERBOARD}"
    return layer


def get_spool_or_404(conn, spool_id):
    """Find one spool by id, or show a Not Found page."""
    spool = conn.execute("SELECT * FROM spools WHERE id = ?", (spool_id,)).fetchone()
    if spool is None:
        conn.close()
        abort(404)
    return spool


def read_spool_form(form):
    """Check the form and return (values, errors)."""
    errors = []

    brand = form.get("brand", "").strip()
    material = form.get("material", "").strip()
    color = form.get("color", "").strip()
    if not (brand and material and color):
        errors.append("Brand, material, and color are required.")
    finish = form.get("finish", "Basic")
    if finish not in FINISHES:
        errors.append("Pick a valid finish.")
        finish = "Basic"
    color_count = form.get("color_count", "1")
    if color_count not in ("1", "2", "3"):
        errors.append("Pick 1, 2, or 3 colors.")
        color_count = "1"

    color_style = form.get("color_style", "split")
    if color_style not in ("split", "gradient"):
        errors.append("Pick a valid multi-color style.")
        color_style = "split"

    hexes = []
    for name in ("color_hex", "color_hex_2", "color_hex_3")[: int(color_count)]:
        value = form.get(name, "").strip()
        if not HEX_COLOR.fullmatch(value):
            errors.append("Pick a valid color for each color slot.")
            value = None
        hexes.append(value)
    hexes += [None] * (3 - len(hexes))

    total_g = remaining_g = empty_spool_g = cost = None
    try:
        total_g = int(form.get("total_g") or 1000)
        remaining_g = int(form.get("remaining_g") or total_g)
        empty_spool_g = int(form["empty_spool_g"]) if form.get("empty_spool_g") else None
        cost = float(form["cost"]) if form.get("cost") else None
    except ValueError:
        errors.append("Weights must be whole numbers, and cost must be a number.")
    else:
        if cost is not None and not math.isfinite(cost):
            errors.append("Cost must be a real number.")
        elif total_g <= 0 or remaining_g < 0 or (empty_spool_g is not None and empty_spool_g < 0):
            errors.append("Weights can't be negative.")
        elif remaining_g > total_g:
            errors.append("Grams left can't be more than the spool's total.")

    values = {
        "brand": brand,
        "material": material,
        "color": color,
        "color_hex": hexes[0],
        "color_hex_2": hexes[1],
        "color_hex_3": hexes[2],
        "color_style": color_style,
        "is_translucent": 1 if form.get("is_translucent") else 0,
        "total_g": total_g,
        "remaining_g": remaining_g,
        "empty_spool_g": empty_spool_g,
        "cost": cost,
        "cfs_slot": form.get("cfs_slot", "").strip() or None,
        "in_dry_box": 1 if form.get("in_dry_box") else 0,
        "backup_brand": form.get("backup_brand", "").strip() or None,
        "notes": form.get("notes", "").strip() or None,
        "material": material,
        "finish": finish,
        "color": color,
    }
    return values, errors


@app.route("/")
def spool_list():
    conn = get_db()
    spools = conn.execute("SELECT * FROM spools ORDER BY material, color").fetchall()
    conn.close()
    return render_template("spools.html", spools=spools, low_stock_g=LOW_STOCK_G)


@app.route("/spools/new", methods=["GET", "POST"])
def add_spool():
    if request.method == "GET":
        return render_template("spool_form.html", heading="Add a Spool",
                               errors=[], form={}, materials=MATERIALS, finishes=FINISHES)

    values, errors = read_spool_form(request.form)
    if errors:
        return render_template("spool_form.html", heading="Add a Spool",
                               errors=errors, form=request.form, materials=MATERIALS, finishes=FINISHES)

    conn = get_db()
    conn.execute(
        "INSERT INTO spools (brand, material, finish, color, color_hex, color_hex_2, color_hex_3, "
        "color_style, is_translucent, total_g, remaining_g, empty_spool_g, cost, cfs_slot, "
        "in_dry_box, backup_brand, notes) VALUES (:brand, :material, :finish, :color, :color_hex, "
        ":color_hex_2, :color_hex_3, :color_style, :is_translucent, :total_g, :remaining_g, "
        ":empty_spool_g, :cost, :cfs_slot, :in_dry_box, :backup_brand, :notes)",
        values,
    )
    conn.commit()
    conn.close()
    return redirect(url_for("spool_list"))


@app.route("/spools/<int:spool_id>/edit", methods=["GET", "POST"])
def edit_spool(spool_id):
    conn = get_db()
    spool = get_spool_or_404(conn, spool_id)

    if request.method == "GET":
        conn.close()
        form = dict(spool)
        form["color_count"] = str(1 + bool(spool["color_hex_2"]) + bool(spool["color_hex_3"]))
        return render_template("spool_form.html", heading="Edit Spool", spool_id=spool_id,
                               errors=[], form=form, materials=MATERIALS, finishes=FINISHES)

    values, errors = read_spool_form(request.form)
    if errors:
        conn.close()
        return render_template("spool_form.html", heading="Edit Spool", spool_id=spool_id,
                               errors=errors, form=request.form, materials=MATERIALS, finishes=FINISHES)

    values["id"] = spool_id
    conn.execute(
        "UPDATE spools SET brand = :brand, material = :material, finish = :finish, color = :color, "
        "color_hex = :color_hex, color_hex_2 = :color_hex_2, color_hex_3 = :color_hex_3, "
        "color_style = :color_style, is_translucent = :is_translucent, total_g = :total_g, "
        "remaining_g = :remaining_g, empty_spool_g = :empty_spool_g, cost = :cost, "
        "cfs_slot = :cfs_slot, in_dry_box = :in_dry_box, backup_brand = :backup_brand, "
        "notes = :notes WHERE id = :id",
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


@app.route("/spools/<int:spool_id>/weigh", methods=["POST"])
def weigh_spool(spool_id):
    conn = get_db()
    spool = get_spool_or_404(conn, spool_id)

    try:
        scale_g = int(request.form.get("scale_g", ""))
    except ValueError:
        conn.close()
        flash("Enter the scale reading as a whole number of grams.")
        return redirect(url_for("edit_spool", spool_id=spool_id))

    if spool["empty_spool_g"] is None:
        conn.close()
        flash("Add this spool's empty weight first, then weigh it.")
        return redirect(url_for("edit_spool", spool_id=spool_id))

    remaining_g = max(0, min(scale_g - spool["empty_spool_g"], spool["total_g"]))
    conn.execute("UPDATE spools SET remaining_g = ? WHERE id = ?", (remaining_g, spool_id))
    conn.commit()
    conn.close()
    flash(f"Updated {spool['brand']} {spool['color']}: {remaining_g} g left.")
    return redirect(url_for("spool_list"))


@app.route("/spools/<int:spool_id>/use", methods=["POST"])
def use_filament(spool_id):
    conn = get_db()
    spool = get_spool_or_404(conn, spool_id)

    try:
        value = float(request.form.get("grams_used", ""))
    except ValueError:
        value = 0
    grams_used = round(value) if math.isfinite(value) else 0
    if grams_used <= 0:
        conn.close()
        flash("Enter the grams used as a number more than 0.")
        return redirect(url_for("edit_spool", spool_id=spool_id))

    new_remaining = max(0, spool["remaining_g"] - grams_used)
    conn.execute("UPDATE spools SET remaining_g = ? WHERE id = ?", (new_remaining, spool_id))
    conn.execute("INSERT INTO prints (spool_id, grams_used) VALUES (?, ?)", (spool_id, grams_used))
    conn.commit()
    conn.close()
    flash(f"Logged {grams_used} g for {spool['brand']} {spool['color']}. {new_remaining} g left.")
    return redirect(url_for("spool_list"))


@app.route("/check", methods=["GET", "POST"])
def check():
    conn = get_db()
    spools = conn.execute("SELECT * FROM spools ORDER BY material, color").fetchall()
    conn.close()

    form = request.form if request.method == "POST" else {}
    errors = []
    result = None

    if request.method == "POST":
        try:
            spool_id = int(form.get("spool_id", ""))
            amount = float(form.get("amount", ""))
            margin_pct = float(form.get("margin") or 10)
        except ValueError:
            errors.append("Pick a spool and enter a number for the amount.")
        else:
            spool = None
            for s in spools:
                if s["id"] == spool_id:
                    spool = s

            
            if spool is None:
                errors.append("That spool doesn't exist.")
            elif not (math.isfinite(amount) and math.isfinite(margin_pct)):
                errors.append("Enter real numbers for the amount and margin.")
            elif amount <= 0 or margin_pct < 0:
                errors.append("The amount must be more than 0, and the margin can't be negative.")
            else:
                if form.get("unit") == "m":
                    needed_g = meters_to_grams(amount, spool["material"])
                else:
                    needed_g = amount

                result = {
                    "spool": spool,
                    "needed_g": round(needed_g),
                    "left_after_g": round(spool["remaining_g"] - needed_g),
                    "shortfall_g": round(needed_g - spool["remaining_g"]),
                    "margin_pct": margin_pct,
                    "status": check_print(needed_g, spool["remaining_g"], margin_pct / 100),
                }

    return render_template("check.html", spools=spools, form=form, errors=errors, result=result)

@app.route("/export/colors.json")
def export_colors():
    conn = get_db()
    spools = conn.execute(
        "SELECT * FROM spools WHERE remaining_g > 0 ORDER BY material, finish, color"
    ).fetchall()
    conn.close()

    groups = {}
    for s in spools:
        colors = [c for c in (s["color_hex"], s["color_hex_2"], s["color_hex_3"]) if c]
        key = (s["material"], s["finish"], s["color"].strip().lower(), tuple(colors),
               s["color_style"], s["is_translucent"])
        if key not in groups:
            groups[key] = {
                "material": s["material"],
                "finish": s["finish"],
                "color": s["color"],
                "hex": colors,
                "style": s["color_style"] if len(colors) > 1 else "solid",
                "translucent": bool(s["is_translucent"]),
                "grams": 0,
            }
        groups[key]["grams"] += s["remaining_g"]

    colors_out = []
    for group in groups.values():
        group["level"] = stock_level(group.pop("grams"))
        colors_out.append(group)

    response = jsonify({"updated": date.today().isoformat(), "colors": colors_out})
    response.headers["Content-Disposition"] = "attachment; filename=colors.json"
    return response

if __name__ == "__main__":
    app.run(debug=True)