import math

# Grams per cubic centimeter for common materials
DENSITY = {
    "PLA": 1.24,
    "PETG": 1.27,
    "ABS": 1.04,
    "ASA": 1.07,
    "TPU": 1.21,
}
PLENTY_G = 500
LIMITED_G = 150
DEFAULT_DENSITY = 1.24


def meters_to_grams(meters, material, diameter_mm=1.75):
    """Convert a length of filament to its weight in grams."""
    radius_cm = diameter_mm / 10 / 2
    area_cm2 = math.pi * radius_cm ** 2
    volume_cm3 = area_cm2 * meters * 100
    return volume_cm3 * DENSITY.get(material, DEFAULT_DENSITY)


def check_print(needed_g, remaining_g, margin=0.10):
    """Return 'enough', 'tight', or 'not_enough'."""
    if remaining_g >= round(needed_g * (1 + margin), 2):
        return "enough"
    if remaining_g >= needed_g:
        return "tight"
    return "not_enough"

    PLENTY_G = 500
LIMITED_G = 150


def stock_level(grams):
    """Turn grams into a level customers understand."""
    if grams >= PLENTY_G:
        return "plenty"
    if grams >= LIMITED_G:
        return "limited"
    return "low"