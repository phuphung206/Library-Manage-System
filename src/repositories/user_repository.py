from datetime import date
from typing import List, Optional, Tuple
from src.config.db_connection import DatabaseConnection
from src.models.user import User, Member, Librarian, Admin

class UserRepository:
    def __init__(self):
        self.db = DatabaseConnection()

    def _get_conn(self):
        return self.db.get_connection()

    def _row_to_user(self, row) -> Optional[User]:
        if not row:
            return None
        kwargs = dict(
            user_id=row.user_id,
            card_number=row.card_number,
            full_name=row.full_name,
            email=row.email,
            password_hash=row.password_hash,
            phone=row.phone,
            identity_number=row.identity_number,
            address=row.address,
            status=row.status,
            membership_expiry_date=row.membership_expiry_date,
            created_at=row.created_at,
        )
        if row.role == "ADMIN":
            return Admin(**kwargs)
        if row.role == "LIBRARIAN":
            return Librarian(**kwargs)
        return Member(**kwargs)

    def find_by_email_or_card(self, identifier: str) -> Optional[User]:
        """Tìm user theo Email hoặc Card Number phục vụ Đăng nhập (UC-04)."""
        sql = """
            SELECT user_id, card_number, full_name, email, password_hash,
                   phone, identity_number, address, role, status,
                   membership_expiry_date, created_at
            FROM users
            WHERE email = ? OR card_number = ?
        """
        cursor = self._get_conn().cursor()
        cursor.execute(sql, (identifier.strip(), identifier.strip()))
        return self._row_to_user(cursor.fetchone())

    def find_by_email(self, email: str) -> Optional[User]:
        sql = """
            SELECT user_id, card_number, full_name, email, password_hash,
                   phone, identity_number, address, role, status,
                   membership_expiry_date, created_at
            FROM users WHERE email = ?
        """
        cursor = self._get_conn().cursor()
        cursor.execute(sql, (email.strip(),))
        return self._row_to_user(cursor.fetchone())

    def find_by_id(self, user_id: int) -> Optional[User]:
        sql = """
            SELECT user_id, card_number, full_name, email, password_hash,
                   phone, identity_number, address, role, status,
                   membership_expiry_date, created_at
            FROM users WHERE user_id = ?
        """
        cursor = self._get_conn().cursor()
        cursor.execute(sql, (user_id,))
        return self._row_to_user(cursor.fetchone())

    def exists_email_or_identity(self, email: str, identity_number: str) -> bool:
        """Kiểm tra trùng Email hoặc CCCD/MSSV khi đăng ký (UC-05)."""
        sql = "SELECT 1 FROM users WHERE email = ? OR identity_number = ?"
        cursor = self._get_conn().cursor()
        cursor.execute(sql, (email.strip(), identity_number.strip()))
        return cursor.fetchone() is not None

    def create_user(self, user: User) -> int:
        """Thêm mới tài khoản vào bảng users, trả về user_id vừa tạo."""
        sql = """
            INSERT INTO users (
                card_number, full_name, email, password_hash, phone,
                identity_number, address, role, status, membership_expiry_date
            )
            OUTPUT INSERTED.user_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (
                user.card_number,
                user.full_name,
                user.email,
                user.password_hash,
                user.phone,
                user.identity_number,
                user.address,
                user.role,
                user.status,
                user.membership_expiry_date,
            ))
            new_id = cursor.fetchone()[0]
            conn.commit()
            return int(new_id)
        except Exception:
            conn.rollback()
            raise

    def update_profile(self, user_id: int, full_name: str, phone: str, address: str) -> bool:
        """Độc giả cập nhật hồ sơ cá nhân (UC-06)."""
        sql = """
            UPDATE users
            SET full_name = ?, phone = ?, address = ?
            WHERE user_id = ?
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (full_name, phone, address, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Đổi mật khẩu hoặc cập nhật mật khẩu tạm (UC-06, UC-07)."""
        sql = "UPDATE users SET password_hash = ? WHERE user_id = ?"
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (new_password_hash, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise

    def get_all_users(
        self,
        role_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 30
    ) -> Tuple[List[User], int]:
        """Lấy danh sách user phân trang và lọc theo Role/Status cho Admin (UC-12)."""
        conditions = ["1=1"]
        params = []

        if role_filter and role_filter != "ALL":
            conditions.append("role = ?")
            params.append(role_filter)
        if status_filter and status_filter != "ALL":
            conditions.append("status = ?")
            params.append(status_filter)
        if keyword:
            conditions.append("(full_name LIKE ? OR email LIKE ? OR card_number LIKE ?)")
            kw = f"%{keyword.strip()}%"
            params.extend([kw, kw, kw])

        where_clause = " AND ".join(conditions)
        cursor = self._get_conn().cursor()

        # Đếm tổng bản ghi
        cursor.execute(f"SELECT COUNT(*) FROM users WHERE {where_clause}", params)
        total = cursor.fetchone()[0]

        # Truy vấn phân trang SQL Server (OFFSET ... FETCH NEXT)
        offset = (max(1, page) - 1) * page_size
        sql = f"""
            SELECT user_id, card_number, full_name, email, password_hash,
                   phone, identity_number, address, role, status,
                   membership_expiry_date, created_at
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(sql, params + [offset, page_size])
        users = [self._row_to_user(r) for r in cursor.fetchall()]
        return users, total

    def admin_update_user(
        self,
        user_id: int,
        role: str,
        status: str,
        expiry_date: Optional[date]
    ) -> bool:
        """Admin cập nhật quyền, khóa/mở khóa tài khoản và gia hạn thẻ (UC-12)."""
        sql = """
            UPDATE users
            SET role = ?, status = ?, membership_expiry_date = ?
            WHERE user_id = ?
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (role, status, expiry_date, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise
