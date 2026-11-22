from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

# ==========================================
# PHÂN HỆ 1: QUẢN LÝ NGƯỜI DÙNG & HỆ THỐNG (Người 1)
# ==========================================
@dataclass
class User:
    """Thực thể đại diện cho bảng users (Người dùng, Độc giả, Thủ thư, Admin)"""
    user_id: int
    username: str
    password_hash: str
    full_name: str
    identity_number: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    role: str = 'MEMBER'  # ADMIN, LIBRARIAN, MEMBER
    status: str = 'ACTIVE' # ACTIVE, LOCKED, EXPIRED
    membership_expiry_date: Optional[date] = None
    created_at: Optional[datetime] = None

@dataclass
class Notification:
    """Thực thể đại diện cho bảng notifications (Thông báo hệ thống)"""
    notification_id: int
    user_id: int
    message: str
    is_read: bool = False
    created_at: Optional[datetime] = None


# ==========================================
# PHÂN HỆ 2: QUẢN LÝ DANH MỤC SÁCH (Người 1 / Người 2)
# ==========================================
@dataclass
class Category:
    """Thực thể đại diện cho bảng categories (Thể loại sách)"""
    category_id: int
    name: str
    description: Optional[str] = None

@dataclass
class Author:
    """Thực thể đại diện cho bảng authors (Tác giả)"""
    author_id: int
    author_name: str
    bio: Optional[str] = None

@dataclass
class BookTitle:
    """Thực thể đại diện cho bảng book_titles (Đầu sách)"""
    title_id: int
    title: str
    category_id: int
    publisher: Optional[str] = None
    publish_year: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class BookAuthor:
    """Thực thể đại diện cho bảng book_authors (Bảng trung gian Sách - Tác giả)"""
    title_id: int
    author_id: int

@dataclass
class BookCopy:
    """Thực thể đại diện cho bảng book_copies (Cuốn sách vật lý cụ thể)"""
    copy_id: int
    title_id: int
    barcode: str
    status: str = 'AVAILABLE' # AVAILABLE, BORROWED, LOST, DAMAGED
    condition: Optional[str] = None
    created_at: Optional[datetime] = None


# ==========================================
# PHÂN HỆ 3: MƯỢN TRẢ & LƯU THÔNG (Người 2)
# ==========================================
@dataclass
class LoanTransaction:
    """Thực thể đại diện cho bảng loan_transactions (Giao dịch Mượn/Trả)"""
    loan_id: int
    user_id: int
    copy_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date] = None
    status: str = 'BORROWED' # BORROWED, RETURNED, OVERDUE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==========================================
# PHÂN HỆ 4: TIỀN PHẠT, BÁO CÁO & CẤU HÌNH (Người 3 - Bạn)
# ==========================================
@dataclass
class Fine:
    """Thực thể đại diện cho bảng fines (Khoản tiền phạt)"""
    fine_id: int
    loan_id: int
    user_id: int
    amount: float
    fine_reason: str # LATE_RETURN, LOST_BOOK, DAMAGED_BOOK
    status: str = 'UNPAID' # UNPAID, PAID, WAIVED
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class FinePayment:
    """Thực thể đại diện cho bảng fine_payments (Biên lai thanh toán)"""
    payment_id: int
    fine_id: int
    amount_paid: float
    payment_method: str # CASH, ONLINE
    payment_date: Optional[datetime] = None
    receipt_number: Optional[str] = None

@dataclass
class SystemConfig:
    """Thực thể đại diện cho bảng system_configs (Cấu hình hệ thống)"""
    config_key: str
    config_value: str
    description: Optional[str] = None
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None