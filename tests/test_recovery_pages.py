import re

from werkzeug.security import check_password_hash

import db

PASSWORD = "benchy-print"
NEW_PASSWORD = "dry-box-spool"


def code_on(page):
    return re.search(r"[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}", page.data.decode()).group(0)


def set_password(anon_client):
    """Set the first password and return the recovery code shown."""
    page = anon_client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return code_on(page)


def saved_user():
    conn = db.get_db()
    row = conn.execute("SELECT * FROM users").fetchone()
    conn.close()
    return row


def can_log_in(anon_client, password):
    anon_client.post("/logout")
    response = anon_client.post("/login", data={"password": password})
    return response.status_code == 302


def reset(anon_client, code, password=NEW_PASSWORD):
    anon_client.post("/logout")
    return anon_client.post("/forgot", data={"code": code, "password": password, "confirm": password})


def test_setup_shows_a_recovery_code_and_saves_only_its_hash(anon_client):
    code = set_password(anon_client)
    saved = saved_user()["recovery_hash"]
    assert code.replace("-", "") not in saved
    assert check_password_hash(saved, code.replace("-", ""))


def test_login_page_links_to_forgot_password(anon_client):
    set_password(anon_client)
    anon_client.post("/logout")
    assert b'href="/forgot"' in anon_client.get("/login").data
    assert anon_client.get("/forgot").status_code == 200


def test_right_code_sets_a_new_password_and_a_new_code(anon_client):
    code = set_password(anon_client)
    page = reset(anon_client, code)
    new_code = code_on(page)
    assert new_code != code
    assert can_log_in(anon_client, NEW_PASSWORD)
    assert not can_log_in(anon_client, PASSWORD)


def test_a_used_code_stops_working(anon_client):
    code = set_password(anon_client)
    reset(anon_client, code)
    page = reset(anon_client, code, password="another-password")
    assert b"Wrong recovery code." in page.data
    assert can_log_in(anon_client, NEW_PASSWORD)


def test_code_can_be_typed_lowercase_without_dashes(anon_client):
    code = set_password(anon_client)
    reset(anon_client, code.lower().replace("-", " "))
    assert can_log_in(anon_client, NEW_PASSWORD)


def test_wrong_code_changes_nothing(anon_client):
    set_password(anon_client)
    page = reset(anon_client, "AAAA-BBBB-CCCC-DDDD")
    assert b"Wrong recovery code." in page.data
    assert can_log_in(anon_client, PASSWORD)


def test_reset_with_short_password_changes_nothing(anon_client):
    code = set_password(anon_client)
    page = reset(anon_client, code, password="exia")
    assert b"Use at least 8 characters." in page.data
    assert can_log_in(anon_client, PASSWORD)


def test_change_password_needs_the_current_one(anon_client):
    set_password(anon_client)
    page = anon_client.post("/account", data={"current": "wrong-password",
                                              "password": NEW_PASSWORD, "confirm": NEW_PASSWORD})
    assert b"Your current password is wrong." in page.data
    assert can_log_in(anon_client, PASSWORD)


def test_change_password_works_and_keeps_the_recovery_code(anon_client):
    code = set_password(anon_client)
    page = anon_client.post("/account", data={"current": PASSWORD,
                                              "password": NEW_PASSWORD, "confirm": NEW_PASSWORD})
    assert b"Password changed." in page.data
    assert can_log_in(anon_client, NEW_PASSWORD)
    reset(anon_client, code, password="third-password")
    assert can_log_in(anon_client, "third-password")


def test_change_password_page_needs_login(anon_client):
    set_password(anon_client)
    anon_client.post("/logout")
    response = anon_client.get("/account")
    assert response.headers["Location"].endswith("/login")

def test_menu_links_to_change_password(anon_client):
    set_password(anon_client)
    page = anon_client.get("/").data
    assert b'href="/account"' in page
    assert b">Password</a>" in page