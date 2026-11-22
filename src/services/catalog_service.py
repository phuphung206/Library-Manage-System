from decimal import Decimal
from typing import List, Optional, Tuple
from src.models.book import BookTitle, BookCopy
from src.models.user import User
from src.repositories.book_repository import BookRepository


class CatalogService:
    def __init__(self, book_repo: Optional[BookRepository] = None):
        self.book_repo = book_repo or BookRepository()

    def _require_staff(self, actor: User):
        if not actor or actor.role not in ("LIBRARIAN", "ADMIN"):
            raise PermissionError("Chỉ Thủ thư hoặc Quản trị viên mới được phép chỉnh sửa danh mục sách.")

    # --- UC-01 & UC-02: Tra cứu / Lọc OPAC (Tất cả người dùng kể cả Guest) ---
    def browse_or_search(
        self,
        keyword: Optional[str] = None,
        category_id: Optional[int] = None,
        publication_year: Optional[int] = None,
        sort_by: str = "title",
        sort_dir: str = "ASC",
        page: int = 1,
        page_size: int = 30,
    ) -> Tuple[List[BookTitle], int]:
        return self.book_repo.search_and_browse_books(
            keyword=keyword,
            category_id=category_id,
            publication_year=publication_year,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )

    def get_book_details(self, book_id: int) -> Optional[BookTitle]:
        return self.book_repo.get_book_detail(book_id)

    def get_categories(self) -> List[Tuple[int, str]]:
        return self.book_repo.get_all_categories()

    # --- UC-03: Thêm / Sửa / Xóa mềm Đầu sách ---
    def add_book_title(
        self,
        actor: User,
        isbn: str,
        title: str,
        author_names_csv: str,
        category_name: str,
        publisher_name: str,
        publication_year: Optional[int],
        cover_price: Decimal,
        summary: str = "",
    ) -> BookTitle:
        self._require_staff(actor)
        if not isbn.strip() or not title.strip():
            raise ValueError("ISBN và Tên sách là bắt buộc.")
        if self.book_repo.exists_isbn(isbn):
            raise ValueError(f"Mã ISBN '{isbn}' đã tồn tại trong hệ thống.")

        cat_id = self.book_repo.get_or_create_category(category_name) if category_name.strip() else None
        pub_id = self.book_repo.get_or_create_publisher(publisher_name) if publisher_name.strip() else None

        author_ids = []
        for name in [n.strip() for n in author_names_csv.split(",") if n.strip()]:
            author_ids.append(self.book_repo.get_or_create_author(name))

        book = BookTitle(
            book_id=None,
            isbn=isbn.strip(),
            title=title.strip(),
            category_id=cat_id,
            publisher_id=pub_id,
            publication_year=publication_year,
            summary=summary.strip() or None,
            cover_price=Decimal(str(cover_price or 0)),
        )
        book.book_id = self.book_repo.create_book_title(book, author_ids)
        return book

    def update_book_title(
        self,
        actor: User,
        book_id: int,
        isbn: str,
        title: str,
        author_names_csv: str,
        category_name: str,
        publisher_name: str,
        publication_year: Optional[int],
        cover_price: Decimal,
        summary: str = "",
    ) -> bool:
        self._require_staff(actor)
        if not isbn.strip() or not title.strip():
            raise ValueError("ISBN và Tên sách là bắt buộc.")
        if self.book_repo.exists_isbn(isbn, exclude_book_id=book_id):
            raise ValueError(f"Mã ISBN '{isbn}' đã thuộc về một đầu sách khác.")

        cat_id = self.book_repo.get_or_create_category(category_name) if category_name.strip() else None
        pub_id = self.book_repo.get_or_create_publisher(publisher_name) if publisher_name.strip() else None

        author_ids = []
        for name in [n.strip() for n in author_names_csv.split(",") if n.strip()]:
            author_ids.append(self.book_repo.get_or_create_author(name))

        book = BookTitle(
            book_id=book_id,
            isbn=isbn.strip(),
            title=title.strip(),
            category_id=cat_id,
            publisher_id=pub_id,
            publication_year=publication_year,
            summary=summary.strip() or None,
            cover_price=Decimal(str(cover_price or 0)),
        )
        return self.book_repo.update_book_title(book, author_ids)

    def soft_delete_book_title(self, actor: User, book_id: int) -> bool:
        """Xóa mềm đầu sách (is_deleted = 1), chặn nếu đang có bản sao BORROWED (UC-03)."""
        self._require_staff(actor)
        borrowed_count = self.book_repo.count_borrowed_copies(book_id)
        if borrowed_count > 0:
            raise ValueError(f"Không thể xóa đầu sách vì đang có {borrowed_count} bản sao được độc giả mượn.")
        return self.book_repo.soft_delete_book_title(book_id)

    # --- UC-03: Quản lý Kho Bản sao vật lý ---
    def add_physical_copy(
        self,
        actor: User,
        book_id: int,
        barcode: str,
        zone: str = "",
        shelf: str = "",
        floor: str = "",
    ) -> BookCopy:
        self._require_staff(actor)
        if not barcode.strip():
            raise ValueError("Mã vạch (Barcode) không được để trống.")
        if self.book_repo.exists_barcode(barcode):
            raise ValueError(f"Mã vạch '{barcode}' đã tồn tại trong kho.")

        copy = BookCopy(
            copy_id=None,
            book_id=book_id,
            barcode=barcode.strip(),
            zone=zone.strip() or None,
            shelf=shelf.strip() or None,
            floor=floor.strip() or None,
            status="AVAILABLE",
        )
        copy.copy_id = self.book_repo.add_book_copy(copy)
        return copy

    def update_physical_copy(
        self,
        actor: User,
        copy_id: int,
        zone: str,
        shelf: str,
        floor: str,
        status: str,
    ) -> bool:
        self._require_staff(actor)
        if status not in ("AVAILABLE", "BORROWED", "RESERVED", "DAMAGED", "LOST"):
            raise ValueError("Trạng thái bản sao không hợp lệ.")
        return self.book_repo.update_book_copy(copy_id, zone.strip(), shelf.strip(), floor.strip(), status)
