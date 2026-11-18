import re

from auth import read_new_password, new_recovery_code, normalize_code


def test_matching_long_password_is_accepted():
    password, errors = read_new_password({"password": "zaku-ii-kai", "confirm": "zaku-ii-kai"})
    assert errors == []
    assert password == "zaku-ii-kai"


def test_short_password_is_rejected():
    _, errors = read_new_password({"password": "exia", "confirm": "exia"})
    assert errors == ["Use at least 8 characters."]


def test_mismatched_passwords_are_rejected():
    _, errors = read_new_password({"password": "zaku-ii-kai", "confirm": "zaku-ii-kia"})
    assert errors == ["The two passwords don't match."]


def test_spaces_count_and_are_kept():
    password, errors = read_new_password({"password": " my kit ", "confirm": " my kit "})
    assert errors == []
    assert password == " my kit "


def test_recovery_code_looks_right():
    code = new_recovery_code()
    assert re.fullmatch(r"[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}", code)
    assert not set("01OIL") & set(code)


def test_recovery_codes_are_different_each_time():
    assert new_recovery_code() != new_recovery_code()


def test_normalize_code_ignores_case_spaces_and_dashes():
    assert normalize_code(" 7kq4 m2xd-9plr f6tw ") == "7KQ4M2XD9PLRF6TW"
    assert normalize_code("7KQ4-M2XD-9PLR-F6TW") == "7KQ4M2XD9PLRF6TW"