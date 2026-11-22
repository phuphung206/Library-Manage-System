from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

@dataclass
class BookCopy:
    copy_id: Optional[int]
    book_id: int
    barcode: str
    zone: Optional[str] = None
    shelf: Optional[str] = None
    floor: Optional[str] = None
    status: str = "AVAILABLE"

    @property
    def full_location(self) -> str:
        parts = [p for p in [self.floor, self.zone, self.shelf] if p]
        return " - ".join(parts) if parts else "Chưa xếp kệ"

@dataclass
class BookTitle:
    book_id: Optional[int]
    isbn: str
    title: str
    category_id: Optional[int] = None
    publisher_id: Optional[int] = None
    publication_year: Optional[int] = None
    summary: Optional[str] = None
    cover_price: Decimal = Decimal("0.00")
    is_deleted: bool = False
    category_name: Optional[str] = None
    publisher_name: Optional[str] = None
    author_names: Optional[str] = None
    available_copies: int = 0
    total_copies: int = 0
    copies: List[BookCopy] = field(default_factory=list)