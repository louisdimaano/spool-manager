import db

SPOOL = {"brand": "Sunlu", "material": "PLA", "finish": "Basic", "color": "Black",
         "color_count": "1", "color_hex": "#000000", "color_style": "split",
         "total_g": "1000", "remaining_g": "1000", "empty_spool_g": "", "cost": ""}


def add(client, **changes):
    return client.post("/spools/new", data={**SPOOL, **changes})


def spool(spool_id=1):
    conn = db.get_db()
    row = conn.execute("SELECT * FROM spools WHERE id = ?", (spool_id,)).fetchone()
    conn.close()
    return row


def count(table):
    conn = db.get_db()
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return n


# Adding

def test_empty_list_invites_you_to_add_one(client):
    assert b"No spools yet" in client.get("/").data


def test_adding_a_spool_saves_it_and_shows_it(client):
    response = add(client)
    assert response.headers["Location"].endswith("/")
    assert spool()["brand"] == "Sunlu"
    assert b"Sunlu" in client.get("/").data


def test_blank_grams_left_means_a_full_new_spool(client):
    add(client, remaining_g="", total_g="750")
    assert spool()["remaining_g"] == 750


def test_missing_brand_shows_an_error_and_saves_nothing(client):
    page = add(client, brand="  ")
    assert b"Brand, material, and color are required." in page.data
    assert count("spools") == 0


def test_more_left_than_the_total_is_rejected(client):
    page = add(client, remaining_g="1200")
    assert b"Grams left can&#39;t be more than the spool&#39;s total." in page.data
    assert count("spools") == 0


def test_nan_and_inf_costs_are_rejected(client):
    for bad in ("nan", "inf"):
        page = add(client, cost=bad)
        assert b"Cost must be a real number." in page.data
    assert count("spools") == 0


def test_a_made_up_color_is_rejected(client):
    page = add(client, color_hex="red")
    assert b"Pick a valid color for each color slot." in page.data
    assert count("spools") == 0


def test_a_made_up_finish_is_rejected(client):
    page = add(client, finish="Chrome")
    assert b"Pick a valid finish." in page.data
    assert count("spools") == 0


def test_a_made_up_material_is_rejected(client):
    page = add(client, material="Unobtainium")
    assert b"Pick a material from the list." in page.data
    assert count("spools") == 0


# Editing and deleting

def test_editing_changes_the_spool(client):
    add(client)
    client.post("/spools/1/edit", data={**SPOOL, "color": "Galaxy Black", "remaining_g": "640"})
    assert spool()["color"] == "Galaxy Black"
    assert spool()["remaining_g"] == 640


def test_editing_with_grams_left_blank_is_rejected(client):
    add(client, remaining_g="300")
    page = client.post("/spools/1/edit", data={**SPOOL, "remaining_g": ""})
    assert b"Enter how many grams are left." in page.data
    assert spool()["remaining_g"] == 300


def test_a_spool_that_does_not_exist_is_not_found(client):
    assert client.get("/spools/99/edit").status_code == 404
    assert client.post("/spools/99/use", data={"grams_used": "10"}).status_code == 404


def test_deleting_a_spool_also_deletes_its_print_history(client):
    add(client)
    client.post("/spools/1/use", data={"grams_used": "25"})
    client.post("/spools/1/delete")
    assert count("spools") == 0
    assert count("prints") == 0


# Weighing

def test_weighing_needs_the_empty_spool_weight_first(client):
    add(client)
    client.post("/spools/1/weigh", data={"scale_g": "800"})
    assert spool()["remaining_g"] == 1000
    assert b"Add this spool&#39;s empty weight first" in client.get("/spools/1/edit").data


def test_weighing_subtracts_the_empty_spool(client):
    add(client, empty_spool_g="180")
    client.post("/spools/1/weigh", data={"scale_g": "800"})
    assert spool()["remaining_g"] == 620


def test_weighing_never_goes_below_zero_or_above_the_total(client):
    add(client, empty_spool_g="180")
    client.post("/spools/1/weigh", data={"scale_g": "100"})
    assert spool()["remaining_g"] == 0
    client.post("/spools/1/weigh", data={"scale_g": "5000"})
    assert spool()["remaining_g"] == 1000


# Logging a print

def test_logging_a_print_subtracts_and_saves_history(client):
    add(client)
    client.post("/spools/1/use", data={"grams_used": "42.6"})
    assert spool()["remaining_g"] == 957
    assert count("prints") == 1


def test_logging_more_than_is_left_stops_at_zero(client):
    add(client, remaining_g="30")
    client.post("/spools/1/use", data={"grams_used": "50"})
    assert spool()["remaining_g"] == 0


def test_logging_zero_or_nonsense_changes_nothing(client):
    add(client)
    for bad in ("0", "-5", "abc", "nan", "inf"):
        client.post("/spools/1/use", data={"grams_used": bad})
    assert spool()["remaining_g"] == 1000
    assert count("prints") == 0


# Can I print this?

def check(client, amount, unit="g", margin="10"):
    return client.post("/check", data={"spool_id": "1", "amount": amount, "unit": unit, "margin": margin})


def test_check_says_enough_tight_or_not_enough(client):
    add(client, remaining_g="200")
    assert b"<h2>Enough</h2>" in check(client, "150").data
    assert b"<h2>Tight</h2>" in check(client, "190").data
    assert b"<h2>Not enough</h2>" in check(client, "250").data


def test_check_converts_meters_to_grams(client):
    add(client, remaining_g="200")
    assert b"needs about 30 g" in check(client, "10", unit="m").data


def test_check_rejects_bad_numbers(client):
    add(client)
    assert b"Enter real numbers" in check(client, "nan").data
    assert b"The amount must be more than 0" in check(client, "0").data
    assert b"That spool doesn&#39;t exist." in client.post("/check", data={"spool_id": "9", "amount": "5"}).data


def test_checking_changes_nothing(client):
    add(client)
    check(client, "150")
    assert spool()["remaining_g"] == 1000
    assert count("prints") == 0


# Color export

def test_export_combines_matching_spools_and_hides_grams(client):
    add(client, remaining_g="300")
    add(client, remaining_g="250")
    add(client, color="White", color_hex="#ffffff", remaining_g="100")
    add(client, color="Gray", color_hex="#888888", remaining_g="0")
    colors = client.get("/export/colors.json").get_json()["colors"]
    by_name = {c["color"]: c for c in colors}
    assert set(by_name) == {"Black", "White"}
    assert by_name["Black"]["level"] == "plenty"
    assert by_name["White"]["level"] == "low"
    assert all("grams" not in c for c in colors)


def test_export_keeps_finishes_apart(client):
    add(client)
    add(client, finish="Matte")
    colors = client.get("/export/colors.json").get_json()["colors"]
    assert sorted(c["finish"] for c in colors) == ["Basic", "Matte"]