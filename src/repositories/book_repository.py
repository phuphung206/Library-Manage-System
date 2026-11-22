from decimal import Decimal
from typing import List, Optional, Tuple
from src.config.db_connection import DatabaseConnection
from src.models.book import BookTitle, BookCopy


class BookRepository:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()

    def _get_conn(self):
        return self.db.get_connection()

    def _row_to_book_title(self, row) -> Optional[BookTitle]:
        if not row:
            return None
        return BookTitle(
            book_id=row.book_id,
            isbn=row.isbn,
            title=row.title,
            category_id=row.category_id,
            publisher_id=row.publisher_id,
            publication_year=row.publication_year,
            summary=row.summary,
            cover_price=Decimal(str(row.cover_price)),
            is_deleted=bool(row.is_deleted),
            category_name=getattr(row, "category_name", None),
            publisher_name=getattr(row, "publisher_name", None),
            author_names=getattr(row, "author_names", None),
            available_copies=int(getattr(row, "available_copies", 0) or 0),
            total_copies=int(getattr(row, "total_copies", 0) or 0),
        )

    def _row_to_book_copy(self, row) -> Optional[BookCopy]:
        if not row:
            return None
        return BookCopy(
            copy_id=row.copy_id,
            book_id=row.book_id,
            barcode=row.barcode,
            zone=row.zone,
            shelf=row.shelf,
            floor=row.floor,
            status=row.status,
        )

    # --- Danh mục phụ trợ (Categories, Publishers, Authors) ---
    def get_all_categories(self) -> List[Tuple[int, str]]:
        cursor = self._get_conn().cursor()
        cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
        return [(r.category_id, r.category_name) for r in cursor.fetchall()]

    def get_or_create_category(self, category_name: str) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT category_id FROM categories WHERE category_name = ?", (category_name.strip(),))
        row = cursor.fetchone()
        if row:
            return int(row.category_id)
        cursor.execute(
            "INSERT INTO categories (category_name) OUTPUT INSERTED.category_id VALUES (?)",
            (category_name.strip(),),
        )
        new_id = int(cursor.fetchone()[0])
        conn.commit()
        return new_id

    def get_or_create_publisher(self, publisher_name: str) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT publisher_id FROM publishers WHERE publisher_name = ?", (publisher_name.strip(),))
        row = cursor.fetchone()
        if row:
            return int(row.publisher_id)
        cursor.execute(
            "INSERT INTO publishers (publisher_name) OUTPUT INSERTED.publisher_id VALUES (?)",
            (publisher_name.strip(),),
        )
        new_id = int(cursor.fetchone()[0])
        conn.commit()
        return new_id

    def get_or_create_author(self, author_name: str) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT author_id FROM authors WHERE author_name = ?", (author_name.strip(),))
        row = cursor.fetchone()
        if row:
            return int(row.author_id)
        cursor.execute(
            "INSERT INTO authors (author_name) OUTPUT INSERTED.author_id VALUES (?)",
            (author_name.strip(),),
        )
        new_id = int(cursor.fetchone()[0])
        conn.commit()
        return new_id

    # --- UC-01 & UC-02: Tra cứu / Lọc OPAC ---
    def search_and_browse_books(
        self,
        keyword: Optional[str] = None,
        category_id: Optional[int] = None,
        publication_year: Optional[int] = None,
        sort_by: str = "title",
        sort_dir: str = "ASC",
        page: int = 1,
        page_size: int = 30,
    ) -> Tuple[List[BookTitle], int]:
        conditions = ["bt.is_deleted = 0"]
        params = []

        if category_id:
            conditions.append("bt.category_id = ?")
            params.append(category_id)
        if publication_year:
            conditions.append("bt.publication_year = ?")
            params.append(publication_year)
        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            conditions.append("""
                (bt.title LIKE ? OR bt.isbn LIKE ? OR c.category_name LIKE ?
                 OR EXISTS (
                     SELECT 1 FROM book_authors ba
                     JOIN authors a ON ba.author_id = a.author_id
                     WHERE ba.book_id = bt.book_id AND a.author_name LIKE ?
                 ))
            """)
            params.extend([kw, kw, kw, kw])

        where_clause = " AND ".join(conditions)
        direction = "DESC" if sort_dir.upper() == "DESC" else "ASC"
        order_map = {
            "title": f"bt.title {direction}",
            "year": f"bt.publication_year {direction}",
            "popularity": f"borrow_count {direction}",
        }
        order_clause = order_map.get(sort_by, "bt.title ASC")

        cursor = self._get_conn().cursor()
        count_sql = f"""
            SELECT COUNT(DISTINCT bt.book_id)
            FROM book_titles bt
            LEFT JOIN categories c ON bt.category_id = c.category_id
            WHERE {where_clause}
        """
        cursor.execute(count_sql, params)
        total = int(cursor.fetchone()[0])

        offset = (max(1, page) - 1) * page_size
        sql = f"""
            SELECT
                bt.book_id, bt.isbn, bt.title, bt.category_id, bt.publisher_id,
                bt.publication_year, bt.summary, bt.cover_price, bt.is_deleted,
                c.category_name, p.publisher_name,
                STRING_AGG(a.author_name, ', ') AS author_names,
                (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = bt.book_id AND bc.status = 'AVAILABLE') AS available_copies,
                (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = bt.book_id) AS total_copies,
                (SELECT COUNT(*) FROM loan_transactions lt
                 JOIN book_copies bc2 ON lt.copy_id = bc2.copy_id
                 WHERE bc2.book_id = bt.book_id) AS borrow_count
            FROM book_titles bt
            LEFT JOIN categories c ON bt.category_id = c.category_id
            LEFT JOIN publishers p ON bt.publisher_id = p.publisher_id
            LEFT JOIN book_authors ba ON bt.book_id = ba.book_id
            LEFT JOIN authors a ON ba.author_id = a.author_id
            WHERE {where_clause}
            GROUP BY bt.book_id, bt.isbn, bt.title, bt.category_id, bt.publisher_id,
                     bt.publication_year, bt.summary, bt.cover_price, bt.is_deleted,
                     c.category_name, p.publisher_name
            ORDER BY {order_clause}
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(sql, params + [offset, page_size])
        books = [self._row_to_book_title(r) for r in cursor.fetchall()]
        return books, total

    def get_book_detail(self, book_id: int) -> Optional[BookTitle]:
        sql = """
            SELECT
                bt.book_id, bt.isbn, bt.title, bt.category_id, bt.publisher_id,
                bt.publication_year, bt.summary, bt.cover_price, bt.is_deleted,
                c.category_name, p.publisher_name,
                STRING_AGG(a.author_name, ', ') AS author_names,
                (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = bt.book_id AND bc.status = 'AVAILABLE') AS available_copies,
                (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = bt.book_id) AS total_copies
            FROM book_titles bt
            LEFT JOIN categories c ON bt.category_id = c.category_id
            LEFT JOIN publishers p ON bt.publisher_id = p.publisher_id
            LEFT JOIN book_authors ba ON bt.book_id = ba.book_id
            LEFT JOIN authors a ON ba.author_id = a.author_id
            WHERE bt.book_id = ?
            GROUP BY bt.book_id, bt.isbn, bt.title, bt.category_id, bt.publisher_id,
                     bt.publication_year, bt.summary, bt.cover_price, bt.is_deleted,
                     c.category_name, p.publisher_name
        """
        cursor = self._get_conn().cursor()
        cursor.execute(sql, (book_id,))
        book = self._row_to_book_title(cursor.fetchone())
        if book:
            book.copies = self.get_copies_by_book(book_id)
        return book

    def get_copies_by_book(self, book_id: int) -> List[BookCopy]:
        sql = "SELECT copy_id, book_id, barcode, zone, shelf, floor, status FROM book_copies WHERE book_id = ? ORDER BY copy_id"
        cursor = self._get_conn().cursor()
        cursor.execute(sql, (book_id,))
        return [self._row_to_book_copy(r) for r in cursor.fetchall()]

    # --- UC-03: Quản lý Đầu sách & Bản sao vật lý ---
    def exists_isbn(self, isbn: str, exclude_book_id: Optional[int] = None) -> bool:
        cursor = self._get_conn().cursor()
        if exclude_book_id:
            cursor.execute("SELECT 1 FROM book_titles WHERE isbn = ? AND book_id <> ?", (isbn.strip(), exclude_book_id))
        else:
            cursor.execute("SELECT 1 FROM book_titles WHERE isbn = ?", (isbn.strip(),))
        return cursor.fetchone() is not None

    def exists_barcode(self, barcode: str, exclude_copy_id: Optional[int] = None) -> bool:
        cursor = self._get_conn().cursor()
        if exclude_copy_id:
            cursor.execute("SELECT 1 FROM book_copies WHERE barcode = ? AND copy_id <> ?", (barcode.strip(), exclude_copy_id))
        else:
            cursor.execute("SELECT 1 FROM book_copies WHERE barcode = ?", (barcode.strip(),))
        return cursor.fetchone() is not None

    def create_book_title(self, book: BookTitle, author_ids: List[int]) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO book_titles (isbn, title, category_id, publisher_id, publication_year, summary, cover_price, is_deleted)
                OUTPUT INSERTED.book_id
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """
            cursor.execute(sql, (
                book.isbn.strip(),
                book.title.strip(),
                book.category_id,
                book.publisher_id,
                book.publication_year,
                book.summary,
                book.cover_price,
            ))
            book_id = int(cursor.fetchone()[0])

            for aid in author_ids:
                cursor.execute("INSERT INTO book_authors (book_id, author_id) VALUES (?, ?)", (book_id, aid))

            conn.commit()
            return book_id
        except Exception:
            conn.rollback()
            raise

    def update_book_title(self, book: BookTitle, author_ids: List[int]) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            sql = """
                UPDATE book_titles
                SET isbn = ?, title = ?, category_id = ?, publisher_id = ?,
                    publication_year = ?, summary = ?, cover_price = ?
                WHERE book_id = ?
            """
            cursor.execute(sql, (
                book.isbn.strip(),
                book.title.strip(),
                book.category_id,
                book.publisher_id,
                book.publication_year,
                book.summary,
                book.cover_price,
                book.book_id,
            ))
            cursor.execute("DELETE FROM book_authors WHERE book_id = ?", (book.book_id,))
            for aid in author_ids:
                cursor.execute("INSERT INTO book_authors (book_id, author_id) VALUES (?, ?)", (book.book_id, aid))

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise

    def count_borrowed_copies(self, book_id: int) -> int:
        sql = "SELECT COUNT(*) FROM book_copies WHERE book_id = ? AND status = 'BORROWED'"
        cursor = self._get_conn().cursor()
        cursor.execute(sql, (book_id,))
        return int(cursor.fetchone()[0])

    def soft_delete_book_title(self, book_id: int) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE book_titles SET is_deleted = 1 WHERE book_id = ?", (book_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise

    def add_book_copy(self, copy: BookCopy) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO book_copies (book_id, barcode, zone, shelf, floor, status)
                OUTPUT INSERTED.copy_id
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (
                copy.book_id,
                copy.barcode.strip(),
                copy.zone,
                copy.shelf,
                copy.floor,
                copy.status or "AVAILABLE",
            ))
            copy_id = int(cursor.fetchone()[0])
            conn.commit()
            return copy_id
        except Exception:
            conn.rollback()
            raise

    def update_book_copy(self, copy_id: int, zone: str, shelf: str, floor: str, status: str) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            sql = """
                UPDATE book_copies
                SET zone = ?, shelf = ?, floor = ?, status = ?
                WHERE copy_id = ?
            """
            cursor.execute(sql, (zone, shelf, floor, status, copy_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise
