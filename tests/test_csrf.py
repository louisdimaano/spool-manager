import re

from app import app

SPOOL = {"brand": "Sunlu", "material": "PLA", "finish": "Basic", "color": "Black",
         "color_count": "1", "color_hex": "#000000", "color_style": "split",
         "total_g": "1000", "remaining_g": "1000"}


def token_on(page):
    return re.search(r'name="csrf_token" value="([^"]+)"', page.data.decode()).group(1)


def turn_on_csrf(monkeypatch):
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)


def forms_on(html):
    """Every POST form on a page, from its opening tag to </form>."""
    return re.findall(r'<form method="post".*?</form>', html, re.DOTALL)


def test_form_without_its_token_is_rejected(client, monkeypatch):
    turn_on_csrf(monkeypatch)
    response = client.post("/spools/new", data=SPOOL)
    assert response.status_code == 400
    assert b"nothing was changed" in response.data
    assert b"Sunlu" not in client.get("/").data


def test_form_with_its_token_works(client, monkeypatch):
    turn_on_csrf(monkeypatch)
    token = token_on(client.get("/spools/new"))
    response = client.post("/spools/new", data={**SPOOL, "csrf_token": token})
    assert response.status_code == 302


def test_a_made_up_token_is_rejected(client, monkeypatch):
    turn_on_csrf(monkeypatch)
    response = client.post("/spools/new", data={**SPOOL, "csrf_token": "made-up"})
    assert response.status_code == 400


def test_tokens_last_as_long_as_the_login():
    assert app.config["WTF_CSRF_TIME_LIMIT"] is None


def test_every_token_is_inside_its_form(anon_client, monkeypatch):
    anon_client.post("/setup", data={"password": "benchy-print", "confirm": "benchy-print"})
    anon_client.post("/spools/new", data=SPOOL)
    anon_client.post("/logout")
    turn_on_csrf(monkeypatch)
    for path in ("/login", "/forgot"):
        forms = forms_on(anon_client.get(path).data.decode())
        assert forms, path
        for form in forms:
            assert 'name="csrf_token"' in form, path

    with anon_client.session_transaction() as session:
        session["logged_in"] = True
    check_result = anon_client.post("/check", data={"spool_id": "1", "amount": "50", "unit": "g", "margin": "10",
                                                    "csrf_token": token_on(anon_client.get("/check"))})
    pages = {path: anon_client.get(path).data.decode() for path in ("/", "/spools/new", "/spools/1/edit", "/check", "/account")}
    pages["/check (result)"] = check_result.data.decode()
    for path, html in pages.items():
        forms = forms_on(html)
        assert forms, path
        for form in forms:
            assert 'name="csrf_token"' in form, path