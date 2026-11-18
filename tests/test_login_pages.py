from werkzeug.security import check_password_hash

import db

PASSWORD = "benchy-print"
SPOOL = {"brand": "Sunlu", "material": "PLA", "finish": "Basic", "color": "Black",
         "color_count": "1", "color_hex": "#000000", "color_style": "split",
         "total_g": "1000", "remaining_g": "1000"}


def set_password(anon_client, password=PASSWORD):
    return anon_client.post("/setup", data={"password": password, "confirm": password})


def saved_user():
    conn = db.get_db()
    row = conn.execute("SELECT * FROM users").fetchone()
    conn.close()
    return row


def count_spools():
    conn = db.get_db()
    count = conn.execute("SELECT COUNT(*) FROM spools").fetchone()[0]
    conn.close()
    return count


def test_first_visit_goes_to_setup(anon_client):
    response = anon_client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/setup")


def test_setup_saves_only_a_hash(anon_client):
    set_password(anon_client)
    saved = saved_user()["password_hash"]
    assert PASSWORD not in saved
    assert check_password_hash(saved, PASSWORD)


def test_setup_logs_you_in(anon_client):
    set_password(anon_client)
    assert anon_client.get("/").status_code == 200


def test_setup_shows_errors_and_saves_nothing(anon_client):
    page = anon_client.post("/setup", data={"password": "pla", "confirm": "pla"})
    assert b"Use at least 8 characters." in page.data
    assert saved_user() is None


def test_setup_closes_once_a_password_exists(anon_client):
    set_password(anon_client)
    anon_client.post("/logout")
    response = anon_client.post("/setup", data={"password": "new-password", "confirm": "new-password"})
    assert response.headers["Location"].endswith("/login")
    assert check_password_hash(saved_user()["password_hash"], PASSWORD)


def test_logged_out_visitor_is_sent_to_login(anon_client):
    set_password(anon_client)
    anon_client.post("/logout")
    for path in ("/", "/spools/new", "/spools/1/edit", "/check", "/account"):
        response = anon_client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


def test_logged_out_visitor_cannot_change_anything(anon_client):
    set_password(anon_client)
    anon_client.post("/logout")
    anon_client.post("/spools/new", data=SPOOL)
    assert count_spools() == 0


def test_wrong_password_is_rejected(anon_client):
    set_password(anon_client)
    anon_client.post("/logout")
    page = anon_client.post("/login", data={"password": "wrong-password"})
    assert b"Wrong password." in page.data
    assert anon_client.get("/").status_code == 302


def test_right_password_logs_in_for_30_days(anon_client):
    set_password(anon_client)
    anon_client.post("/logout")
    response = anon_client.post("/login", data={"password": PASSWORD})
    assert response.headers["Location"].endswith("/")
    assert "Expires=" in response.headers["Set-Cookie"]
    assert anon_client.get("/").status_code == 200


def test_styles_load_when_logged_out(anon_client):
    assert anon_client.get("/static/style.css").status_code == 200


def test_menu_shows_log_out_only_when_logged_in(anon_client):
    set_password(anon_client)
    assert b"Log out" in anon_client.get("/").data
    anon_client.post("/logout")
    assert b"Log out" not in anon_client.get("/login").data

def test_login_cookie_has_its_own_name(anon_client):
    response = set_password(anon_client)
    assert response.headers["Set-Cookie"].startswith("spool_session=")

def test_color_export_stays_open_for_the_server_script(anon_client):
    set_password(anon_client)
    anon_client.post("/logout")
    response = anon_client.get("/export/colors.json")
    assert response.status_code == 200
    assert "colors" in response.get_json()