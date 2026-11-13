import pytest

from filament import meters_to_grams, check_print


# meters_to_grams

def test_one_meter_of_pla_is_about_3_grams():
    assert meters_to_grams(1, "PLA") == pytest.approx(2.98, abs=0.01)


def test_petg_is_heavier_than_pla():
    assert meters_to_grams(1, "PETG") == pytest.approx(3.05, abs=0.01)


def test_ten_meters_weighs_ten_times_as_much():
    assert meters_to_grams(10, "PLA") == pytest.approx(10 * meters_to_grams(1, "PLA"))


def test_unknown_material_uses_pla_density():
    assert meters_to_grams(1, "Other") == meters_to_grams(1, "PLA")


def test_thicker_filament_weighs_more():
    assert meters_to_grams(1, "PLA", diameter_mm=2.85) == pytest.approx(7.91, abs=0.01)


# check_print

def test_plenty_left_is_enough():
    assert check_print(needed_g=100, remaining_g=200) == "enough"


def test_inside_the_margin_is_tight():
    assert check_print(needed_g=100, remaining_g=105) == "tight"


def test_exactly_the_needed_amount_is_tight():
    assert check_print(needed_g=100, remaining_g=100) == "tight"


def test_short_is_not_enough():
    assert check_print(needed_g=100, remaining_g=90) == "not_enough"


def test_exactly_needed_plus_margin_is_enough():
    assert check_print(needed_g=100, remaining_g=110, margin=0.10) == "enough"


def test_zero_margin_means_exact_amount_is_enough():
    assert check_print(needed_g=100, remaining_g=100, margin=0) == "enough"