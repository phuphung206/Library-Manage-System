from datetime import date, timedelta
from typing import List, Optional, Tuple
from src.models.user import User, Member, Librarian, Admin
from src.repositories.user_repository import UserRepository
from src.utils.security import (
    hash_password,
    verify_password,
    generate_card_number,
    generate_temp_password,
)
from src.utils.validators import is_valid_email, is_valid_password, is_valid_phone


class AuthService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()
        self.current_user: Optional[User] = None  # Lưu session đăng nhập hiện tại

    # --- UC-05: Đăng ký thẻ độc giả ---
    def register_member(
        self,
        full_name: str,
        email: str,
        password: str,
        identity_number: str,
        phone: str = "",
        address: str = "",
    ) -> Member:
        if not all([full_name.strip(), email.strip(), identity_number.strip()]):
            raise ValueError("Vui lòng nhập đầy đủ Họ tên, Email và CCCD/MSSV.")
        if not is_valid_email(email):
            raise ValueError("Định dạng Email không hợp lệ.")
        if not is_valid_password(password):
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự.")
        if not is_valid_phone(phone):
            raise ValueError("Số điện thoại không hợp lệ.")

        if self.user_repo.exists_email_or_identity(email, identity_number):
            raise ValueError("Email hoặc số CCCD/MSSV đã được đăng ký trong hệ thống.")

        card_number = generate_card_number()
        hashed_pwd = hash_password(password)
        expiry_date = date.today() + timedelta(days=365)  # Thẻ có hạn 1 năm

        member = Member(
            user_id=None,
            card_number=card_number,
            full_name=full_name.strip(),
            email=email.strip(),
            password_hash=hashed_pwd,
            phone=phone.strip() or None,
            identity_number=identity_number.strip(),
            address=address.strip() or None,
            status="ACTIVE",
            membership_expiry_date=expiry_date,
        )
        member.user_id = self.user_repo.create_user(member)
        return member

    # --- UC-04: Đăng nhập / Đăng xuất ---
    def login(self, identifier: str, password: str) -> User:
        if not identifier.strip() or not password:
            raise ValueError("Vui lòng nhập Email/Mã thẻ và Mật khẩu.")

        user = self.user_repo.find_by_email_or_card(identifier)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Sai tên đăng nhập hoặc mật khẩu.")

        if user.status == "LOCKED":
            raise PermissionError("Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Quản trị viên.")
        if user.status == "EXPIRED":
            raise PermissionError("Thẻ thư viện đã hết hạn. Vui lòng gia hạn thẻ tại quầy.")

        self.current_user = user
        return user

    def logout(self) -> None:
        self.current_user = None

    # --- UC-06: Cập nhật hồ sơ cá nhân ---
    def update_profile(
        self,
        user_id: int,
        full_name: str,
        phone: str,
        address: str,
        new_password: Optional[str] = None,
    ) -> User:
        if not full_name.strip():
            raise ValueError("Họ tên không được để trống.")
        if not is_valid_phone(phone):
            raise ValueError("Số điện thoại không hợp lệ.")

        self.user_repo.update_profile(
            user_id=user_id,
            full_name=full_name.strip(),
            phone=phone.strip() or None,
            address=address.strip() or None,
        )

        if new_password:
            if not is_valid_password(new_password):
                raise ValueError("Mật khẩu mới phải có ít nhất 6 ký tự.")
            self.user_repo.update_password(user_id, hash_password(new_password))

        updated = self.user_repo.find_by_id(user_id)
        if self.current_user and self.current_user.user_id == user_id:
            self.current_user = updated
        return updated

    # --- UC-07: Quên mật khẩu ---
    def reset_password(self, email: str) -> str:
        if not is_valid_email(email):
            raise ValueError("Email không hợp lệ.")

        user = self.user_repo.find_by_email(email)
        if not user:
            raise ValueError("Không tìm thấy tài khoản nào gắn với Email này.")

        temp_pwd = generate_temp_password(10)
        self.user_repo.update_password(user.user_id, hash_password(temp_pwd))
        # Ghi chú: Tích hợp gửi SMTP email tại giai đoạn ghép nối Notification
        return temp_pwd


class UserService:
    """UC-12: Quản lý người dùng & Phân quyền (Chỉ dành cho Admin)."""

    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    def _require_admin(self, actor: User):
        if not actor or actor.role != "ADMIN":
            raise PermissionError("Chức năng này chỉ dành cho Quản trị viên (ADMIN).")

    def list_users(
        self,
        actor: User,
        role_filter: str = "ALL",
        status_filter: str = "ALL",
        keyword: str = "",
        page: int = 1,
        page_size: int = 30,
    ) -> Tuple[List[User], int]:
        self._require_admin(actor)
        return self.user_repo.get_all_users(role_filter, status_filter, keyword, page, page_size)

    def create_staff_or_member(
        self,
        actor: User,
        full_name: str,
        email: str,
        password: str,
        identity_number: str,
        role: str,
        phone: str = "",
        address: str = "",
    ) -> User:
        self._require_admin(actor)
        if role not in ("MEMBER", "LIBRARIAN", "ADMIN"):
            raise ValueError("Vai trò không hợp lệ.")
        if self.user_repo.exists_email_or_identity(email, identity_number):
            raise ValueError("Email hoặc CCCD đã tồn tại.")

        card_number = generate_card_number()
        hashed = hash_password(password)
        expiry = date.today() + timedelta(days=365) if role == "MEMBER" else None

        cls_map = {"MEMBER": Member, "LIBRARIAN": Librarian, "ADMIN": Admin}
        new_user = cls_map[role](
            user_id=None,
            card_number=card_number,
            full_name=full_name.strip(),
            email=email.strip(),
            password_hash=hashed,
            phone=phone.strip() or None,
            identity_number=identity_number.strip(),
            address=address.strip() or None,
            status="ACTIVE",
            membership_expiry_date=expiry,
        )
        new_user.user_id = self.user_repo.create_user(new_user)
        return new_user

    def update_user_access(
        self,
        actor: User,
        target_user_id: int,
        role: str,
        status: str,
        expiry_date: Optional[date] = None,
    ) -> bool:
        self._require_admin(actor)
        if role not in ("MEMBER", "LIBRARIAN", "ADMIN"):
            raise ValueError("Vai trò không hợp lệ.")
        if status not in ("ACTIVE", "LOCKED", "EXPIRED"):
            raise ValueError("Trạng thái tài khoản không hợp lệ.")
        return self.user_repo.admin_update_user(target_user_id, role, status, expiry_date)
