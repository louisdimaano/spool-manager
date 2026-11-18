"""Rules for the app's single password and its recovery code."""
import secrets

MIN_LENGTH = 8

# No 0/O, 1/I/L: easy to read back and type in
CODE_LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def read_new_password(form):
    """Check a new-password form. Returns (password, errors)."""
    password = form.get("password", "")
    confirm = form.get("confirm", "")
    errors = []
    if len(password) < MIN_LENGTH:
        errors.append(f"Use at least {MIN_LENGTH} characters.")
    elif password != confirm:
        errors.append("The two passwords don't match.")
    return password, errors


def new_recovery_code():
    """A random code like 7KQ4-M2XD-9PLR-F6TW."""
    groups = ["".join(secrets.choice(CODE_LETTERS) for _ in range(4)) for _ in range(4)]
    return "-".join(groups)


def normalize_code(text):
    """Ignore case, spaces, and dashes, so ' 7kq4 m2xd-9plr f6tw ' matches 7KQ4-M2XD-9PLR-F6TW."""
    return "".join(ch for ch in text.upper() if ch.isalnum())