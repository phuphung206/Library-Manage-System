import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import MagicMock

from src.models.user import Member, Librarian, Admin
from src.models.book import BookTitle, BookCopy
from src.services.auth_service import AuthService, UserService
from src.services.catalog_service import CatalogService
from src.utils.security import hash_password

# PHẦN A: KIỂM THỬ TÀI KHOẢN, XÁC THỰC & PHÂN QUYỀN (UC-04, 05, 06, 07, 12)
class TestAuthAndUserManagement:

    def test_register_member_success(self):
        mock_repo = MagicMock()
        mock_repo.exists_email_or_identity.return_value = False
        mock_repo.create_user.return_value = 10

        service = AuthService(user_repo=mock_repo)
        member = service.register_member(
            full_name="Nguyễn Văn An",
            email="an.nguyen@lms.edu.vn",
            password="Password123",
            identity_number="079203001122",
            phone="0909123456",
            address="TP.HCM",
        )

        assert member.user_id == 10
        assert member.role == "MEMBER"
        assert member.status == "ACTIVE"
        assert member.card_number.startswith("LIB-")
        assert member.password_hash != "Password123"
        assert member.membership_expiry_date == date.today() + timedelta(days=365)

    @pytest.mark.parametrize("bad_email", ["khong_co_a_cong", "abc@", "@domain.com"])
    def test_register_invalid_email_raises(self, bad_email):
        service = AuthService(user_repo=MagicMock())
        with pytest.raises(ValueError, match="Email không hợp lệ"):
            service.register_member("Test", bad_email, "123456", "079203009999")

    def test_register_short_password_raises(self):
        service = AuthService(user_repo=MagicMock())
        with pytest.raises(ValueError, match="ít nhất 6 ký tự"):
            service.register_member("Test", "ok@lms.vn", "12345", "079203009999")

    def test_register_duplicate_email_or_cccd_raises(self):
        mock_repo = MagicMock()
        mock_repo.exists_email_or_identity.return_value = True
        service = AuthService(user_repo=mock_repo)

        with pytest.raises(ValueError, match="đã được đăng ký"):
            service.register_member("Test", "dup@lms.vn", "123456", "079203009999")

    def test_login_success_creates_session(self):
        mock_repo = MagicMock()
        user = Member(
            user_id=5,
            card_number="LIB-2026-888888",
            full_name="Trần Thị Bình",
            email="binh@lms.vn",
            password_hash=hash_password("secret99"),
            identity_number="001199887766",
            status="ACTIVE",
        )
        mock_repo.find_by_email_or_card.return_value = user

        service = AuthService(user_repo=mock_repo)
        logged_in = service.login("LIB-2026-888888", "secret99")

        assert logged_in.user_id == 5
        assert service.current_user == user

    def test_login_wrong_password_raises(self):
        mock_repo = MagicMock()
        user = Member(5, "LIB-01", "Bình", "binh@lms.vn", hash_password("secret99"), "123")
        mock_repo.find_by_email_or_card.return_value = user

        service = AuthService(user_repo=mock_repo)
        with pytest.raises(ValueError, match="Sai tên đăng nhập hoặc mật khẩu"):
            service.login("binh@lms.vn", "wrong_pass")

    def test_login_locked_account_raises(self):
        mock_repo = MagicMock()
        locked = Member(5, "LIB-01", "Bình", "binh@lms.vn", hash_password("secret99"), "123", status="LOCKED")
        mock_repo.find_by_email_or_card.return_value = locked

        service = AuthService(user_repo=mock_repo)
        with pytest.raises(PermissionError, match="bị khóa"):
            service.login("binh@lms.vn", "secret99")

    def test_update_profile_and_password(self):
        mock_repo = MagicMock()
        updated_user = Member(5, "LIB-01", "Tên Mới", "binh@lms.vn", "new_hash", "123", phone="0912345678")
        mock_repo.find_by_id.return_value = updated_user

        service = AuthService(user_repo=mock_repo)
        res = service.update_profile(5, "Tên Mới", "0912345678", "Hà Nội", new_password="newpassword")

        mock_repo.update_profile.assert_called_once_with(user_id=5, full_name="Tên Mới", phone="0912345678", address="Hà Nội")
        mock_repo.update_password.assert_called_once()
        assert res.full_name == "Tên Mới"

    def test_reset_password_generates_temp_password(self):
        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = Member(5, "LIB-01", "Bình", "binh@lms.vn", "old_hash", "123")

        service = AuthService(user_repo=mock_repo)
        temp_pwd = service.reset_password("binh@lms.vn")

        assert len(temp_pwd) == 10
        mock_repo.update_password.assert_called_once()

    def test_admin_manage_users_rbac_enforced(self):
        member_actor = Member(2, "LIB-02", "Độc giả", "m@lms.vn", "h", "111")
        admin_actor = Admin(1, "ADM-01", "Quản trị", "a@lms.vn", "h", "000")

        mock_repo = MagicMock()
        user_service = UserService(user_repo=mock_repo)

        # Member thường gọi bị chặn
        with pytest.raises(PermissionError, match="Quản trị viên"):
            user_service.update_user_access(member_actor, target_user_id=3, role="LIBRARIAN", status="ACTIVE")

        # Admin gọi thành công
        mock_repo.admin_update_user.return_value = True
        assert user_service.update_user_access(admin_actor, target_user_id=3, role="LIBRARIAN", status="ACTIVE") is True

# PHẦN B: KIỂM THỬ DANH MỤC OPAC & KHO BẢN SAO (UC-01, UC-02, UC-03)
class TestCatalogAndInventory:

    def test_guest_can_search_opac(self):
        mock_repo = MagicMock()
        sample_books = [BookTitle(book_id=1, isbn="978-0132350884", title="Clean Code", available_copies=3, total_copies=5)]
        mock_repo.search_and_browse_books.return_value = (sample_books, 1)

        catalog_service = CatalogService(book_repo=mock_repo)
        books, total = catalog_service.browse_or_search(keyword="Clean Code")

        assert total == 1
        assert books[0].title == "Clean Code"
        assert books[0].available_copies == 3

    def test_add_book_title_success_by_librarian(self):
        librarian = Librarian(2, "EMP-01", "Thủ thư", "lib@lms.vn", "h", "222")
        mock_repo = MagicMock()
        mock_repo.exists_isbn.return_value = False
        mock_repo.get_or_create_category.return_value = 1
        mock_repo.get_or_create_publisher.return_value = 2
        mock_repo.get_or_create_author.side_effect = [10, 11]
        mock_repo.create_book_title.return_value = 99

        catalog_service = CatalogService(book_repo=mock_repo)
        book = catalog_service.add_book_title(
            actor=librarian,
            isbn="978-604-999",
            title="Thiết kế Phần mềm",
            author_names_csv="Tác giả A, Tác giả B",
            category_name="Công nghệ thông tin",
            publisher_name="NXB Khoa học",
            publication_year=2025,
            cover_price=Decimal("180000"),
        )

        assert book.book_id == 99
        mock_repo.create_book_title.assert_called_once()

    def test_add_book_duplicate_isbn_raises(self):
        admin = Admin(1, "ADM-01", "Admin", "a@lms.vn", "h", "000")
        mock_repo = MagicMock()
        mock_repo.exists_isbn.return_value = True

        catalog_service = CatalogService(book_repo=mock_repo)
        with pytest.raises(ValueError, match="đã tồn tại"):
            catalog_service.add_book_title(
                actor=admin,
                isbn="978-604-999",
                title="Sách Trùng ISBN",
                author_names_csv="Tác giả A",
                category_name="IT",
                publisher_name="NXB",
                publication_year=2024,
                cover_price=Decimal("100000"),
            )

    def test_soft_delete_blocked_when_copies_borrowed(self):
        librarian = Librarian(2, "EMP-01", "Thủ thư", "lib@lms.vn", "h", "222")
        mock_repo = MagicMock()
        mock_repo.count_borrowed_copies.return_value = 1

        catalog_service = CatalogService(book_repo=mock_repo)
        with pytest.raises(ValueError, match="đang có 1 bản sao được độc giả mượn"):
            catalog_service.soft_delete_book_title(actor=librarian, book_id=15)

        mock_repo.soft_delete_book_title.assert_not_called()

    def test_soft_delete_success_when_no_borrowed_copies(self):
        librarian = Librarian(2, "EMP-01", "Thủ thư", "lib@lms.vn", "h", "222")
        mock_repo = MagicMock()
        mock_repo.count_borrowed_copies.return_value = 0
        mock_repo.soft_delete_book_title.return_value = True

        catalog_service = CatalogService(book_repo=mock_repo)
        assert catalog_service.soft_delete_book_title(actor=librarian, book_id=15) is True

    def test_add_physical_copy_duplicate_barcode_raises(self):
        librarian = Librarian(2, "EMP-01", "Thủ thư", "lib@lms.vn", "h", "222")
        mock_repo = MagicMock()
        mock_repo.exists_barcode.return_value = True

        catalog_service = CatalogService(book_repo=mock_repo)
        with pytest.raises(ValueError, match="Mã vạch"):
            catalog_service.add_physical_copy(actor=librarian, book_id=15, barcode="BC-2026-001")
