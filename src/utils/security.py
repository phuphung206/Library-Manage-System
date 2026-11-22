import bcrypt
import secrets
import string
from datetime import datetime


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False


def generate_card_number() -> str:
    year = datetime.now().year
    random_digits = "".join(secrets.choice(string.digits) for _ in range(6))
    return f"LIB-{year}-{random_digits}"


def generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))