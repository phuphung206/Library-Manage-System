import re


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email.strip()))


def is_valid_password(password: str) -> bool:
    return bool(password and len(password) >= 6)


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return True
    return bool(re.match(r"^(0|\+84)[0-9]{8,10}$", phone.strip()))