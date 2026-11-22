from abc import ABC
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

@dataclass
class User(ABC):
    user_id: Optional[int]
    card_number: str
    full_name: str
    email: str
    password_hash: str
    identity_number: str
    role: str = "MEMBER"
    status: str = "ACTIVE"
    phone: Optional[str] = None
    address: Optional[str] = None
    membership_expiry_date: Optional[date] = None
    created_at: Optional[datetime] = None

@dataclass
class Member(User):
    role: str = field(default="MEMBER", init=False)

@dataclass
class Librarian(User):
    role: str = field(default="LIBRARIAN", init=False)

@dataclass
class Admin(User):
    role: str = field(default="ADMIN", init=False)